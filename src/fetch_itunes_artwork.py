import requests
from pathlib import Path
from typing import Dict, List, Optional

class iTunesArtworkFetcher:
    """iTunes Search APIを使用してアートワークを取得するクラス"""
    
    def __init__(self):
        self.base_url = "https://itunes.apple.com/search"
        self.lookup_url = "https://itunes.apple.com/lookup"
    
    def search_music(self, query: str, country: str = "jp", limit: int = 10) -> List[Dict]:
        """
        音楽を検索してアートワーク情報を取得
        
        Args:
            query: 検索クエリ（アーティスト名、アルバム名など）
            country: 国コード（jp, us, など）
            limit: 検索結果の上限数
        
        Returns:
            検索結果のリスト
        """
        params = {
            'term': query,
            'country': country,
            'entity': 'album',
            'media': 'music',
            'limit': limit
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.RequestException as e:
            print(f"検索エラー: {e}")
            return []
    
    def get_artwork_urls(self, result: Dict) -> Dict[str, str]:
        """
        検索結果からアートワークURLを抽出
        
        Args:
            result: iTunes検索結果の1つの項目
        
        Returns:
            各解像度のアートワークURL辞書
        """
        artwork_base = result.get('artworkUrl100', '')
        if not artwork_base:
            return {}
        
        # 各解像度のURLを生成
        urls = {
            'small': artwork_base,  # 100x100
            'medium': artwork_base.replace('100x100bb', '600x600bb'),  # 600x600
            'large': artwork_base.replace('100x100bb', '1200x1200bb'),  # 1200x1200
            'original': artwork_base.replace('100x100bb', '3000x3000bb'),  # 最高解像度
            'no_border': artwork_base.replace('100x100bb-c', '600x600')  # ボーダーなし
        }
        
        return urls
    
    def download_artwork(self, url: str, filename: str) -> bool:
        """
        アートワークをダウンロード
        
        Args:
            url: ダウンロードするURL
            filename: 保存ファイル名
        
        Returns:
            成功したかどうか
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"ダウンロード完了: {filename}")
            return True
        except requests.RequestException as e:
            print(f"ダウンロードエラー: {e}")
            return False
    
    def search_and_download(self, query: str, output_dir: str = "artwork", 
                          quality: str = "large", country: str = "jp", target_artist: str = None, target_album: str = None):
        """
        検索してアートワークをダウンロード
        
        Args:
            query: 検索クエリ
            output_dir: 出力ディレクトリ
            quality: 画質（small, medium, large, original）
            country: 国コード
            target_artist: 対象アーティスト名（優先選択用）
            target_album: 対象アルバム名（優先選択用）
        """
        results = self.search_music(query, country)
        
        if not results:
            print("検索結果が見つかりませんでした")
            return
        
        # 出力ディレクトリを作成
        Path(output_dir).mkdir(exist_ok=True)
        
        # 最適な結果を選択
        best_result = self._select_best_match(results, target_artist, target_album)
        
        if best_result:
            artist = best_result.get('artistName', 'Unknown')
            album = best_result.get('collectionName', 'Unknown')
            
            print(f"\n選択された結果: {artist} - {album}")
            
            # アートワークURLを取得
            artwork_urls = self.get_artwork_urls(best_result)
            
            if quality in artwork_urls:
                url = artwork_urls[quality]
                # ファイル名を安全な形式に変換
                safe_filename = f"{artist} - {album}".replace('/', '_').replace('\\', '_')
                filename = f"{output_dir}/{safe_filename}.jpg"
                
                if self.download_artwork(url, filename):
                    print(f"保存先: {filename}")
                    # アートワーク情報を返却
                    yield {
                        'artist': artist,
                        'album': album,
                        'artwork_url': url,
                        'filename': filename,
                        'itunes_id': best_result.get('collectionId'),
                        'release_date': best_result.get('releaseDate')
                    }
    
    def _select_best_match(self, results: List[Dict], target_artist: str = None, target_album: str = None) -> Optional[Dict]:
        """
        検索結果から最適なマッチを選択
        
        Args:
            results: 検索結果のリスト
            target_artist: 対象アーティスト名
            target_album: 対象アルバム名
        
        Returns:
            最適な検索結果
        """
        if not results:
            return None
        
        # ターゲットが指定されていない場合は最初の結果を返す
        if not target_artist and not target_album:
            return results[0]
        
        # スコアリング用の関数
        def calculate_score(result):
            score = 0
            result_artist = result.get('artistName', '').lower()
            result_album = result.get('collectionName', '').lower()
            
            # アーティスト名の一致度をチェック
            if target_artist:
                target_artist_lower = target_artist.lower()
                if target_artist_lower == result_artist:
                    score += 100  # 完全一致
                elif target_artist_lower in result_artist or result_artist in target_artist_lower:
                    score += 50   # 部分一致
                
                # 単語レベルでの一致をチェック
                target_words = set(target_artist_lower.split())
                result_words = set(result_artist.split())
                common_words = target_words.intersection(result_words)
                score += len(common_words) * 10
            
            # アルバム名の一致度をチェック
            if target_album:
                target_album_lower = target_album.lower()
                if target_album_lower == result_album:
                    score += 100  # 完全一致
                elif target_album_lower in result_album or result_album in target_album_lower:
                    score += 50   # 部分一致
                
                # 単語レベルでの一致をチェック
                target_words = set(target_album_lower.split())
                result_words = set(result_album.split())
                common_words = target_words.intersection(result_words)
                score += len(common_words) * 10
            
            return score
        
        # 各結果にスコアを付けてソート
        scored_results = [(result, calculate_score(result)) for result in results]
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # デバッグ情報を表示
        if len(scored_results) > 1:
            print(f"検索結果の優先順位:")
            for i, (result, score) in enumerate(scored_results[:3], 1):
                artist = result.get('artistName', 'Unknown')
                album = result.get('collectionName', 'Unknown')
                print(f"  {i}. {artist} - {album} (スコア: {score})")
        
        # 最高スコアの結果を返す
        return scored_results[0][0]
