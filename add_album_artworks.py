import os
from pathlib import Path
from typing import Optional
from src.itunes_album_finder import iTunesAlbumFinder
from src.audio_metadata_extractor import AudioMetadataExtractor
from src.fetch_itunes_artwork import iTunesArtworkFetcher
from src.audio_metadata_writer import AudioMetadataWriter
from src.config import config


class AlbumArtworkBatchDownloader:
    """アルバム内全楽曲のアートワークを一括取得するクラス"""
    
    def __init__(self, output_dir: str = None):
        # 設定ファイルから出力ディレクトリを取得
        if output_dir is None:
            output_dir = config.get_artwork_output_dir()
        
        self.finder = iTunesAlbumFinder()
        self.extractor = AudioMetadataExtractor()
        self.artwork_fetcher = iTunesArtworkFetcher()
        self.metadata_writer = AudioMetadataWriter()
        self.output_dir = Path(output_dir)
        
        # 出力ディレクトリを作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 既に処理済みのアルバムを記録するセット
        self.processed_albums = set()
    
    def download_album_artworks(self, album_name_input: str) -> bool:
        """
        指定されたアルバム名で検索し、該当する全楽曲のアートワークをダウンロード
        
        Args:
            album_name_input: 検索するアルバム名
        
        Returns:
            成功したかどうか
        """
        print(f"アルバム検索中: '{album_name_input}'")
        print("=" * 80)
        
        # アルバムを検索
        results = self.finder.find_albums_by_name(album_name_input)
        
        if not results:
            print("該当するアルバムが見つかりませんでした")
            return False
        
        total_success = 0
        total_songs = 0
        
        # 見つかったアルバムを処理
        for i, album_info in enumerate(results, 1):
            print(f"\n【{i}】アーティスト: {album_info['artist_name']}")
            print(f"    アルバム: {album_info['album_name']}")
            print(f"    楽曲数: {album_info['audio_file_count']}曲")
            print("-" * 60)
            
            # アルバム内の各楽曲を処理
            for j, audio_file in enumerate(album_info['audio_files'], 1):
                file_name = Path(audio_file).name
                print(f"\n  [{j:2d}] {file_name}")
                
                # 楽曲のメタデータを取得
                metadata = self.extractor.extract_metadata(audio_file)
                
                if metadata:
                    # アートワークが既に存在する楽曲はスキップ
                    if metadata['has_artwork']:
                        print(f"       アートワーク既存 - スキップ")
                        continue
                    
                    total_songs += 1
                    album_name = metadata['album']
                    print(f"       アートワークなし - 検出されたアルバム名: {album_name}")
                    
                    # アートワークをダウンロード
                    artwork_path = self._download_artwork_for_album(album_name)
                    if artwork_path:
                        print(f"       ✓ アートワーク取得成功")
                        
                        # 楽曲ファイルにアートワークを埋め込み
                        embed_success = self.metadata_writer.embed_artwork(audio_file, artwork_path)
                        if embed_success:
                            total_success += 1
                            print(f"       ✓ アートワーク埋め込み成功")
                        else:
                            print(f"       ✗ アートワーク埋め込み失敗")
                    else:
                        print(f"       ✗ アートワーク取得失敗")
                else:
                    print("       メタデータを取得できませんでした")
        
        print(f"\n" + "=" * 80)
        print(f"処理完了: {total_success}/{total_songs} 件のアートワークを取得")
        return total_success > 0
    
    def _download_artwork_for_album(self, album_name: str) -> Optional[str]:
        """
        アルバム名でアートワークをダウンロード
        
        Args:
            album_name: アルバム名
        
        Returns:
            ダウンロードしたファイルのパス（失敗時はNone）
        """
        # アルバム名が空または不明な場合はスキップ
        if not album_name or album_name == "Unknown Album":
            return None
        
        # 安全なファイル名に変換
        safe_album_name = self._make_safe_filename(album_name)
        target_filename = f"{self.output_dir}/{safe_album_name}.jpg"
        
        # 既に処理済みまたはファイルが存在する場合はパスを返す
        if album_name in self.processed_albums:
            return target_filename if os.path.exists(target_filename) else None
        
        if os.path.exists(target_filename):
            print(f"         既に存在: {safe_album_name}.jpg")
            self.processed_albums.add(album_name)
            return target_filename
        
        print(f"         iTunes APIで検索中: {album_name}")
        
        try:
            # iTunes検索APIを使用してアートワークを取得
            downloaded_items = list(self.artwork_fetcher.search_and_download(
                query=album_name,
                output_dir=str(self.output_dir),
                quality=config.get_artwork_quality(),
                country=config.get_itunes_api_country()
            ))
            
            if downloaded_items:
                # ダウンロードされたファイル名を変更
                downloaded_item = downloaded_items[0]
                old_filename = downloaded_item['filename']
                
                # ファイル名を変更
                if os.path.exists(old_filename):
                    os.rename(old_filename, target_filename)
                    print(f"         保存完了: {safe_album_name}.jpg")
                    self.processed_albums.add(album_name)
                    return target_filename
                else:
                    print(f"         ダウンロードファイルが見つかりません")
                    return None
            else:
                print(f"         iTunes APIで見つかりませんでした")
                return None
                
        except Exception as e:
            print(f"         エラー: {e}")
            return None
    
    def _make_safe_filename(self, filename: str) -> str:
        """
        ファイル名として安全な文字列に変換
        
        Args:
            filename: 元のファイル名
        
        Returns:
            安全なファイル名
        """
        # 危険な文字を置換
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        safe_filename = filename
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        return safe_filename.strip()
    
    def show_summary(self) -> None:
        """処理結果のサマリーを表示"""
        print(f"\n処理済みアルバム数: {len(self.processed_albums)}")
        if self.processed_albums:
            print("取得したアートワーク:")
            for i, album in enumerate(sorted(self.processed_albums), 1):
                safe_name = self._make_safe_filename(album)
                print(f"  {i:2d}. {safe_name}.jpg ({album})")


if __name__ == "__main__":
    import sys
    
    downloader = AlbumArtworkBatchDownloader()
    
    # コマンドライン引数をチェック
    if len(sys.argv) < 2:
        print("使用方法: python3 add_album_artworks.py {アルバム名}")
        print("例: python3 add_album_artworks.py Furusato")
        print("例: python3 add_album_artworks.py \"My Album Name\"")
        sys.exit(1)
    
    # コマンドライン引数からアルバム名を取得（複数の引数を結合）
    album_name = " ".join(sys.argv[1:]).strip()
    
    if album_name:
        print(f"アルバム '{album_name}' 内の全楽曲のアートワークを取得・埋め込みを実行します")
        print("=" * 80)
        
        # アルバム内全楽曲のアートワークを取得・埋め込み
        success = downloader.download_album_artworks(album_name)
        
        if success:
            print("\nアートワークの取得・埋め込みが完了しました！")
            downloader.show_summary()
        else:
            print("\nアートワークの取得・埋め込みに失敗しました")
    else:
        print("アルバム名を指定してください")
