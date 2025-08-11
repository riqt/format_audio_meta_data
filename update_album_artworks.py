import os
from pathlib import Path
from typing import Optional, Dict, List
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
            
            # アルバム内のアートワークなしの楽曲を収集
            songs_without_artwork = []
            album_metadata_collection = {}
            
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
                    artist_name = metadata['artist']
                    print(f"       アートワークなし - 検出されたアルバム名: {album_name}")
                    
                    # アートワークなしの楽曲として記録
                    songs_without_artwork.append(audio_file)
                    
                    # 即座にアートワーク収集を実行
                    print(f"\n--- アートワーク収集 (楽曲: {file_name}) ---")
                    song_metadata_list = [metadata]
                    artwork_info = self._download_artwork_for_scoring(album_name, artist_name, song_metadata_list)
                    if artwork_info:
                        print(f"    ✓ アートワーク取得成功 (スコア: {artwork_info['score']})")
                    else:
                        print(f"    ✗ アートワーク取得失敗")
                    
                    # アルバムのメタデータを記録（スコアリング用）
                    if album_name not in album_metadata_collection:
                        album_metadata_collection[album_name] = []
                    album_metadata_collection[album_name].append({
                        'album': album_name,
                        'artist': artist_name,
                        'file': audio_file
                    })
                else:
                    print("       メタデータを取得できませんでした")
            
            # アートワーク埋め込みフェーズ
            if songs_without_artwork and album_metadata_collection:
                print(f"\n--- アートワーク埋め込みフェーズ ---")
                best_artwork = self._collect_and_select_best_artwork(album_metadata_collection)
                
                if best_artwork:
                    print(f"最適なアートワーク: {best_artwork['path']}")
                    
                    # 全ての対象楽曲にアートワークを埋め込み
                    for audio_file in songs_without_artwork:
                        file_name = Path(audio_file).name
                        print(f"  埋め込み中: {file_name}")
                        
                        embed_success = self.metadata_writer.embed_artwork(audio_file, best_artwork['path'])
                        if embed_success:
                            total_success += 1
                            print(f"       ✓ アートワーク埋め込み成功")
                        else:
                            print(f"       ✗ アートワーク埋め込み失敗")
                else:
                    print(f"適切なアートワークが見つかりませんでした")
        
        print(f"\n" + "=" * 80)
        print(f"処理完了: {total_success}/{total_songs} 件のアートワークを取得")
        return total_success > 0
    
    def _download_artwork_for_album(self, album_name: str, artist_name: str = None) -> Optional[str]:
        """
        アルバム名でアートワークをダウンロード
        
        Args:
            album_name: アルバム名
            artist_name: アーティスト名（オプション）
        
        Returns:
            ダウンロードしたファイルのパス（失敗時はNone）
        """
        # アルバム名が空または不明な場合はスキップ
        if not album_name or album_name == "Unknown Album":
            return None
        
        # 既に処理済みの場合は既存ファイルをチェック
        if album_name in self.processed_albums:
            # 2パターンのファイル名をチェック
            if artist_name and artist_name != "Unknown Artist":
                artist_album_file = f"{self.output_dir}/{self._make_safe_filename(artist_name)}_{self._make_safe_filename(album_name)}.jpg"
                if os.path.exists(artist_album_file):
                    return artist_album_file
            
            album_file = f"{self.output_dir}/{self._make_safe_filename(album_name)}.jpg"
            if os.path.exists(album_file):
                return album_file
            
            # ファイルが存在しない場合は処理済みフラグをリセット
            self.processed_albums.remove(album_name)
        
        
        # 1. まず "{アーティスト} {アルバム}" で検索
        if artist_name and artist_name != "Unknown Artist":
            print(f"         iTunes APIで検索中: {artist_name} {album_name}")
            artwork_path = self._try_download_artwork(f"{artist_name} {album_name}", f"{self._make_safe_filename(artist_name)}_{self._make_safe_filename(album_name)}.jpg")
            if artwork_path:
                self.processed_albums.add(album_name)
                return artwork_path
        
        # 2. 見つからない場合は "{アルバム}" のみで検索
        print(f"         iTunes APIで検索中: {album_name}")
        artwork_path = self._try_download_artwork(album_name, f"{self._make_safe_filename(album_name)}.jpg")
        if artwork_path:
            self.processed_albums.add(album_name)
            return artwork_path
        
        print(f"         iTunes APIで見つかりませんでした")
        return None
    
    def _try_download_artwork(self, search_query: str, filename: str) -> Optional[str]:
        """
        指定されたクエリでアートワークをダウンロードを試行
        
        Args:
            search_query: 検索クエリ
            filename: 保存ファイル名
        
        Returns:
            ダウンロードしたファイルのパス（失敗時はNone）
        """
        target_path = f"{self.output_dir}/{filename}"
        
        # 既にファイルが存在する場合はそれを返す
        if os.path.exists(target_path):
            print(f"         既に存在: {filename}")
            return target_path
        
        try:
            # iTunes検索APIを使用してアートワークを取得
            # search_queryから元のアーティスト名・アルバム名を推定
            parts = search_query.split(' ', 1)
            if len(parts) >= 2:
                # "{アーティスト} {アルバム}" の場合
                target_artist = parts[0]
                target_album = parts[1] if len(parts) > 1 else None
            else:
                # "{アルバム}" のみの場合
                target_artist = None
                target_album = search_query
            
            downloaded_items = list(self.artwork_fetcher.search_and_download(
                query=search_query,
                output_dir=str(self.output_dir),
                quality=config.get_artwork_quality(),
                country=config.get_itunes_api_country(),
                target_artist=target_artist,
                target_album=target_album
            ))
            
            if downloaded_items:
                # ダウンロードされたファイル名を変更
                downloaded_item = downloaded_items[0]
                old_filename = downloaded_item['filename']
                
                # 実際に取得されたアルバム名を使用してファイル名を決定
                actual_album = downloaded_item.get('album', target_album or search_query)
                album_filename = f"{self.output_dir}/{self._make_safe_filename(actual_album)}.jpg"
                
                # ファイル名を変更
                if os.path.exists(old_filename):
                    os.rename(old_filename, album_filename)
                    print(f"         保存完了: {self._make_safe_filename(actual_album)}.jpg")
                    return album_filename
                else:
                    print(f"         ダウンロードファイルが見つかりません")
                    return None
            else:
                return None
                
        except Exception as e:
            print(f"         エラー: {e}")
            return None
    
    def _collect_and_select_best_artwork(self, album_metadata_collection: Dict[str, List[Dict]]) -> Optional[Dict[str, str]]:
        """
        アルバムのメタデータコレクションから全てのアートワークを収集し、最適なものを選択
        
        Args:
            album_metadata_collection: アルバム名をキーとしたメタデータのリスト
        
        Returns:
            最適なアートワークの情報（パス、スコアなど）
        """
        all_artworks = []
        
        # 各アルバムのアートワークを収集（既に個別楽曲ごとに収集済みのため、ここは結果をまとめる）
        # tmp/artwork/*.jpgから既存のアートワークファイルを収集
        import glob
        artwork_pattern = f"{self.output_dir}/*.jpg"
        existing_artworks = glob.glob(artwork_pattern)
        
        for artwork_path in existing_artworks:
            # ファイル名からアルバム情報を推定
            filename = os.path.basename(artwork_path).replace('.jpg', '')
            
            # アルバム名に一致するメタデータを検索
            matching_metadata = None
            for album_name, metadata_list in album_metadata_collection.items():
                if album_name.lower() in filename.lower() or filename.lower() in album_name.lower():
                    matching_metadata = metadata_list[0] if metadata_list else {}
                    break
            
            if matching_metadata:
                score = self._calculate_artwork_score(artwork_path, 
                                                    matching_metadata.get('album', ''), 
                                                    matching_metadata.get('artist', ''), 
                                                    [matching_metadata])
                
                all_artworks.append({
                    'path': artwork_path,
                    'album': matching_metadata.get('album', ''),
                    'artist': matching_metadata.get('artist', ''),
                    'score': score,
                    'metadata_count': 1
                })
        
        if not all_artworks:
            return None
        
        # スコアに基づいて最適なアートワークを選択
        best_artwork = max(all_artworks, key=lambda x: x['score'])
        print(f"  最適なアートワーク選択: {best_artwork['album']} (スコア: {best_artwork['score']})")
        
        return best_artwork
    
    def _download_artwork_for_scoring(self, album_name: str, artist_name: str, metadata_list: List[Dict]) -> Optional[Dict[str, any]]:
        """
        スコアリング用のアートワークダウンロード
        
        Args:
            album_name: アルバム名
            artist_name: アーティスト名
            metadata_list: そのアルバムのメタデータリスト
        
        Returns:
            アートワーク情報とスコア
        """
        artwork_path = self._download_artwork_for_album(album_name, artist_name)
        if not artwork_path:
            return None
        
        # アートワークのスコアを計算
        score = self._calculate_artwork_score(artwork_path, album_name, artist_name, metadata_list)
        
        return {
            'path': artwork_path,
            'album': album_name,
            'artist': artist_name,
            'score': score,
            'metadata_count': len(metadata_list)
        }
    
    def _calculate_artwork_score(self, artwork_path: str, album_name: str, artist_name: str, metadata_list: List[Dict]) -> int:
        """
        アートワークのスコアを計算
        
        Args:
            artwork_path: アートワークファイルのパス
            album_name: アルバム名
            artist_name: アーティスト名
            metadata_list: そのアルバムのメタデータリスト
        
        Returns:
            計算されたスコア
        """
        import os
        
        score = 0
        
        # アーティスト名とアルバム名の組み合わせによるスコア
        filename = os.path.basename(artwork_path)
        if artist_name and artist_name.lower() in filename.lower():
            score += 100  # アーティスト名がファイル名に含まれている
        if album_name and album_name.lower() in filename.lower():
            score += 100  # アルバム名がファイル名に含まれている
        
        # メタデータの一貫性によるスコア
        # 同じアルバム名の楽曲数が多いほど信頼性が高い
        score += len(metadata_list) * 10
        
        # アーティスト名の一貫性チェック
        if artist_name:
            artist_matches = sum(1 for meta in metadata_list 
                               if meta.get('artist', '').lower() == artist_name.lower())
            if artist_matches == len(metadata_list):
                score += 50  # 全楽曲で同じアーティスト
            elif artist_matches >= len(metadata_list) * 0.8:
                score += 30  # 80%以上で同じアーティスト
        
        return score
    
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
    
    def cleanup_artwork_files(self) -> None:
        """一時的なアートワークファイルを削除"""
        try:
            import glob
            
            # tmp/artwork/*.jpg のパターンでファイルを検索
            artwork_pattern = f"{self.output_dir}/*.jpg"
            artwork_files = glob.glob(artwork_pattern)
            
            if artwork_files:
                print(f"\n一時アートワークファイルを削除中...")
                deleted_count = 0
                
                for file_path in artwork_files:
                    try:
                        os.remove(file_path)
                        file_name = Path(file_path).name
                        print(f"  削除: {file_name}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"  削除失敗: {Path(file_path).name} - {e}")
                
                print(f"削除完了: {deleted_count}件のファイルを削除しました")
            else:
                print("\n削除対象のアートワークファイルはありませんでした")
                
        except Exception as e:
            print(f"アートワークファイル削除エラー: {e}")


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
        
        # 処理完了後にアートワークファイルを削除
        downloader.cleanup_artwork_files()
    else:
        print("アルバム名を指定してください")
