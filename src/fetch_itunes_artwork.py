import requests
from pathlib import Path
from typing import Dict, List

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
                          quality: str = "large", country: str = "jp"):
        """
        検索してアートワークをダウンロード
        
        Args:
            query: 検索クエリ
            output_dir: 出力ディレクトリ
            quality: 画質（small, medium, large, original）
            country: 国コード
        """
        results = self.search_music(query, country)
        
        if not results:
            print("検索結果が見つかりませんでした")
            return
        
        # 出力ディレクトリを作成
        Path(output_dir).mkdir(exist_ok=True)
        
        for i, result in enumerate(results[:1]):  # 最初の1件のみ
            artist = result.get('artistName', 'Unknown')
            album = result.get('collectionName', 'Unknown')
            
            print(f"\n{i+1}. {artist} - {album}")
            
            # アートワークURLを取得
            artwork_urls = self.get_artwork_urls(result)
            
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
                        'itunes_id': result.get('collectionId'),
                        'release_date': result.get('releaseDate')
                    }
