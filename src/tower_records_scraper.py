import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from urllib.parse import quote


class TowerRecordsScraper:
    """Tower RecordsのWebサイトから作曲者情報を取得するクラス"""
    
    def __init__(self):
        self.base_url = "https://tower.jp"
        self.search_url = "https://tower.jp/search/item"
        
        # ヘッダー設定（ブラウザのふりをする）
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # セッション管理
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_album(self, album_name: str, artist_name: str) -> List[Dict[str, str]]:
        """
        Tower Recordsでアルバムとアーティストを検索
        
        Args:
            album_name: アルバム名
            artist_name: アーティスト名
        
        Returns:
            検索結果のリスト
        """
        search_query = f"{album_name} {artist_name}"
        print(f"Tower Records検索: {search_query}")
        
        try:
            # 検索クエリの前処理（半角記号を全角に変換）
            processed_query = search_query.replace('&', '＆')  # 半角&を全角＆に変換
            
            # 検索クエリをURL エンコード（パス形式）
            encoded_query = quote(processed_query, safe='')
            # CDのみを検索するためのフォーマットパラメータを追加
            search_url = f"{self.search_url}/{encoded_query}?format=121%7C131"
            
            print(f"元の検索クエリ: {search_query}")
            print(f"処理後の検索クエリ: {processed_query}")
            print(f"検索URL: {search_url}")
            
            # リクエスト実行（レート制限対応）
            time.sleep(1)  # 1秒待機
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # HTMLを解析
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 検索結果を解析
            results = self._parse_search_results(soup)
            
            print(f"検索結果: {len(results)}件")
            return results
            
        except requests.RequestException as e:
            print(f"Tower Records検索エラー: {e}")
            return []
        except Exception as e:
            print(f"検索結果解析エラー: {e}")
            return []
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        検索結果HTMLを解析して情報を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
        
        Returns:
            検索結果のリスト
        """
        results = []
        
        try:
            # Tower Records特有のクラス名を使用
            product_items = []
            
            # 複数のセレクタを試行
            selectors = [
                '.TOL-item-search-result-PC-result-tile-display-item',  # 正しい商品アイテム
                '.tr-item-block',
                '.item-block',
                '.search-result-item',
                '[class*="item"]',
                '[class*="product"]',
                '.item',
                '.product'
            ]
            
            for selector in selectors:
                product_items = soup.select(selector)
                if product_items:
                    print(f"商品要素を発見: {selector} ({len(product_items)}件)")
                    break
            
            # 各商品アイテムを処理
            for item in product_items[:10]:  # 最大10件まで
                try:
                    result = self._extract_product_info(item)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"商品情報抽出エラー: {e}")
                    continue
            
            # 結果が空の場合、デバッグ情報を表示
            if not results:
                self._debug_html_structure(soup)
        
        except Exception as e:
            print(f"検索結果解析エラー: {e}")
        
        return results
    
    def _debug_html_structure(self, soup: BeautifulSoup):
        """デバッグ用：HTMLの構造を分析"""
        print("\n=== デバッグ情報 ===")
        
        # タイトルタグを確認
        title = soup.find('title')
        if title:
            print(f"ページタイトル: {title.get_text(strip=True)}")
        
        # 検索結果数を確認
        result_count_selectors = ['.result-count', '.search-count', '[class*="count"]']
        for selector in result_count_selectors:
            count_elem = soup.select_one(selector)
            if count_elem:
                print(f"結果数表示: {count_elem.get_text(strip=True)}")
        
        # よく使われるクラス名を確認
        common_classes = ['item', 'product', 'result', 'card', 'block', 'box']
        for class_name in common_classes:
            elements = soup.find_all(class_=lambda x: x and class_name in x.lower())
            if elements:
                print(f"'{class_name}' 関連クラス: {len(elements)}個")
                # 最初の要素のクラス名を表示
                if elements[0].get('class'):
                    print(f"  例: {' '.join(elements[0]['class'])}")
        
        # HTMLの一部を表示
        body = soup.find('body')
        if body:
            # bodyの最初の1000文字を表示
            body_text = str(body)[:1000]
            print(f"\nHTML構造（最初の1000文字）:\n{body_text}...")
        
        print("==================")
    
    def _extract_product_info(self, item) -> Optional[Dict[str, str]]:
        """
        商品アイテムから情報を抽出
        
        Args:
            item: BeautifulSoupの商品要素
        
        Returns:
            商品情報の辞書
        """
        try:
            # Tower Records特有のクラス名を含む複数のセレクタを試行
            
            # タイトル取得
            title_selectors = [
                '.tr-item-block-info-item-name a',  # 正しいタイトルセレクタ
                '.tr-item-block-info-title',
                '.item-title', 
                '.product-title',
                '.title',
                'h3', 'h4', 'h5',
                '[class*="title"]',
                'a'
            ]
            
            title = ""
            for selector in title_selectors:
                title_elem = item.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title:
                        break
            
            # アーティスト取得
            artist_selectors = [
                '.tr-item-block-info-artist-name p a',  # 正しいアーティストセレクタ
                '.tr-item-block-info-artist-name',
                '.artist-name',
                '.artist',
                '.performer',
                '[class*="artist"]'
            ]
            
            artist = ""
            for selector in artist_selectors:
                artist_elem = item.select_one(selector)
                if artist_elem:
                    artist = artist_elem.get_text(strip=True)
                    if artist:
                        break
            
            # リンク取得（tr-item-blockクラスを持つaタグを優先）
            link_elem = item.select_one('a.tr-item-block[href]')
            if not link_elem:
                link_elem = item.find('a', href=True)
            
            link = ""
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    link = f"{self.base_url}{href}"
                elif href.startswith('http'):
                    link = href
            
            # 価格取得
            price_selectors = [
                '.tr-item-block-info-price span',  # 正しい価格セレクタ
                '.tr-item-block-info-price',
                '.price',
                '.cost',
                '[class*="price"]'
            ]
            
            price = ""
            for selector in price_selectors:
                price_elem = item.select_one(selector)
                if price_elem:
                    price = price_elem.get_text(strip=True)
                    if price:
                        break
            
            # レーベル取得
            label_selectors = [
                '.tr-item-block-info-label',
                '.label',
                '.publisher',
                '[class*="label"]'
            ]
            
            label = ""
            for selector in label_selectors:
                label_elem = item.select_one(selector)
                if label_elem:
                    label = label_elem.get_text(strip=True)
                    if label:
                        break
            
            # 商品IDを取得
            product_id = ""
            import re
            
            # まずリンクのhrefからIDを抽出（最も確実）
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                # /item/4497459 のような形式からIDを抽出
                match = re.search(r'/item/(\d+)', href)
                if match:
                    product_id = match.group(1)
            
            # data属性からも試行
            if not product_id:
                # カートボタンのonclickからIDを抽出
                cart_button = item.select_one('button[onclick*="cartinsearchresult"]')
                if cart_button and cart_button.get('onclick'):
                    onclick = cart_button['onclick']
                    match = re.search(r'cartinsearchresult\((\d+)\)', onclick)
                    if match:
                        product_id = match.group(1)
            
            # 商品IDがあればリンクを構築
            if product_id:
                link = f"{self.base_url}/item/{product_id}"
            
            # デバッグ情報を詳細化
            print(f"抽出結果:")
            print(f"  タイトル: {title[:50]}...")
            print(f"  アーティスト: {artist[:30]}...")
            print(f"  商品ID: {product_id}")
            print(f"  リンク: {link}")
            print(f"  要素のクラス: {item.get('class', 'なし')}")
            
            # HTMLの一部を表示（デバッグ用）
            item_html = str(item)[:300]
            print(f"  要素HTML: {item_html}...")
            print()
            
            # IDまたは何らかの情報があれば返す
            if product_id or title or artist:
                return {
                    'title': title or "タイトル不明",
                    'artist': artist or "アーティスト不明", 
                    'price': price,
                    'label': label,
                    'link': link,
                    'product_id': product_id
                }
            
        except Exception as e:
            print(f"商品情報抽出エラー: {e}")
        
        return None
    
    def get_product_detail_html(self, product_url: str) -> Optional[str]:
        """
        商品詳細ページのHTMLを取得
        
        Args:
            product_url: 商品ページのURL
        
        Returns:
            詳細ページのHTML文字列
        """
        try:
            print(f"詳細ページHTML取得: {product_url}")
            
            time.sleep(1)  # レート制限対応
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            
            return response.text
            
        except Exception as e:
            print(f"詳細ページHTML取得エラー: {e}")
            return None
    
    def parse_track_credits(self, product_url: str) -> List[Dict[str, any]]:
        """
        商品詳細ページから収録内容の作曲者情報を解析
        
        Args:
            product_url: 商品ページのURL
        
        Returns:
            楽曲情報のリスト
        """
        try:
            print(f"収録内容解析: {product_url}")
            
            time.sleep(1)  # レート制限対応
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            tracks = []
            
            # 収録内容のリストを取得
            track_items = soup.select('.TOL-item-info-PC-tab-recorded-contents-list-track-item')
            
            for track_item in track_items:
                track_info = {}
                
                # 曲番号とタイトルを取得
                track_number_elem = track_item.select_one('.TOL-item-info-PC-tab-recorded-contents-list-track-number span')
                track_title_elem = track_item.select_one('.TOL-item-info-PC-tab-recorded-contents-list-track-title')
                track_length_elem = track_item.select_one('.TOL-item-info-PC-tab-recorded-contents-list-track-length')
                
                if track_number_elem:
                    track_info['track_number'] = track_number_elem.get_text(strip=True)
                if track_title_elem:
                    track_info['title'] = track_title_elem.get_text(strip=True)
                if track_length_elem:
                    track_info['length'] = track_length_elem.get_text(strip=True)
                
                # 詳細情報（作曲者など）を取得
                hidden_area = track_item.select_one('.TOL-item-info-PC-tab-recorded-contents-list-track-hidden-area')
                if hidden_area:
                    credits = self._parse_track_credits_from_hidden_area(hidden_area)
                    track_info.update(credits)
                
                tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            print(f"収録内容解析エラー: {e}")
            return []
    
    def _parse_track_credits_from_hidden_area(self, hidden_area) -> Dict[str, str]:
        """
        楽曲の詳細エリアからクレジット情報を抽出
        
        Args:
            hidden_area: BeautifulSoupの詳細エリア要素
        
        Returns:
            クレジット情報の辞書
        """
        credits = {}
        
        try:
            # 各段落を処理
            paragraphs = hidden_area.select('.TOL-item-info-PC-tab-recorded-contents-list-track-hidden-paragraph')
            
            for paragraph in paragraphs:
                # div要素を取得
                divs = paragraph.find_all('div')
                
                for div in divs:
                    # boldなspanでラベルを取得
                    label_span = div.find('span', class_='is-bold')
                    if label_span:
                        label = label_span.get_text(strip=True).replace('：', '').replace(':', '')
                        
                        # ラベルの後にあるリンクやテキストを取得
                        # ラベルのspanを除去して残りのテキストを取得
                        label_span.decompose()  # 一時的に削除
                        
                        # リンクがある場合はリンクテキストを取得
                        links = div.find_all('a')
                        if links:
                            values = []
                            for link in links:
                                values.append(link.get_text(strip=True))
                            credits[label] = ', '.join(values)
                        else:
                            # リンクがない場合はテキストを取得
                            text = div.get_text(strip=True)
                            if text:
                                credits[label] = text
        
        except Exception as e:
            print(f"クレジット情報抽出エラー: {e}")
        
        return credits
    
    def close(self):
        """セッションを閉じる"""
        if self.session:
            self.session.close()


# 使用例
if __name__ == "__main__":
    scraper = TowerRecordsScraper()
    
    try:
        # テスト検索
        album = input("アルバム名を入力してください: ").strip()
        artist = input("アーティスト名を入力してください: ").strip()
        
        if album and artist:
            results = scraper.search_album(album, artist)
            
            print(f"\n検索結果 ({len(results)}件):")
            print("-" * 60)
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   アーティスト: {result['artist']}")
                if result['price']:
                    print(f"   価格: {result['price']}")
                if result['label']:
                    print(f"   レーベル: {result['label']}")
                if result['link']:
                    print(f"   URL: {result['link']}")
                print()
                
                # 最初の結果の収録内容を解析
                if i == 1 and result['link']:
                    print("最初の商品の収録内容を解析中...")
                    tracks = scraper.parse_track_credits(result['link'])
                    if tracks:
                        print(f"\n収録内容 ({len(tracks)}曲):")
                        print("=" * 80)
                        for track in tracks:
                            print(f"{track.get('track_number', '')} {track.get('title', 'タイトル不明')} ({track.get('length', '')})")
                            
                            # クレジット情報を表示
                            print(track)
                            credits_to_show = ['歌', '作詞', '作曲', '編曲', '録音']
                            for credit_type in credits_to_show:
                                if credit_type in track:
                                    print(f"  {credit_type}: {track[credit_type]}")
                            print()
                    else:
                        print("収録内容の取得に失敗しました")
    
    finally:
        scraper.close()