from pathlib import Path
from typing import List, Dict, Optional
from .config import config


class iTunesAlbumFinder:
    """iTunes Mediaディレクトリからアルバムを検索するクラス"""
    
    def __init__(self, itunes_media_path: str = None):
        # 設定ファイルからパスを取得、引数で上書き可能
        if itunes_media_path is None:
            itunes_media_path = config.get_itunes_media_path()
        
        self.itunes_media_path = Path(itunes_media_path)
        self.supported_formats = ['.mp3', '.aiff', '.aif', '.m4a', '.aac', '.flac', '.ogg', '.wav']
        
        # 設定ファイルのパス検証
        if not config.validate_itunes_path():
            print(f"設定されたiTunes Media Path: {self.itunes_media_path}")
            print("config.yamlファイルでパスを変更できます")
    
    def find_albums_by_name(self, album_name: str, case_sensitive: bool = False) -> List[Dict[str, any]]:
        """
        アルバム名でディレクトリを検索し、該当するアルバムの情報を返す
        
        Args:
            album_name: 検索するアルバム名
            case_sensitive: 大文字小文字を区別するか
        
        Returns:
            マッチしたアルバムの情報リスト
        """
        if not self.itunes_media_path.exists():
            print(f"iTunes Mediaディレクトリが見つかりません: {self.itunes_media_path}")
            return []
        
        results = []
        search_pattern = album_name if case_sensitive else album_name.lower()
        
        try:
            # アーティストディレクトリを走査
            for artist_dir in self.itunes_media_path.iterdir():
                if not artist_dir.is_dir():
                    continue
                
                # アルバムディレクトリを走査
                for album_dir in artist_dir.iterdir():
                    if not album_dir.is_dir():
                        continue
                    
                    album_dir_name = album_dir.name if case_sensitive else album_dir.name.lower()
                    
                    # アルバム名の部分一致をチェック
                    if search_pattern in album_dir_name:
                        audio_files = self._get_audio_files(album_dir)
                        if audio_files:  # オーディオファイルが含まれている場合のみ追加
                            album_info = {
                                'artist_name': artist_dir.name,
                                'album_name': album_dir.name,
                                'album_path': str(album_dir),
                                'audio_files': audio_files,
                                'audio_file_count': len(audio_files)
                            }
                            results.append(album_info)
                            
        except PermissionError as e:
            print(f"ディレクトリアクセス権限エラー: {e}")
        except Exception as e:
            print(f"検索エラー: {e}")
        
        return results
    
    def find_exact_album(self, album_name: str, artist_name: Optional[str] = None) -> Optional[Dict[str, any]]:
        """
        完全一致でアルバムを検索
        
        Args:
            album_name: アルバム名
            artist_name: アーティスト名（指定すると検索を絞り込む）
        
        Returns:
            マッチしたアルバムの情報、見つからない場合はNone
        """
        results = self.find_albums_by_name(album_name, case_sensitive=True)
        
        for result in results:
            if result['album_name'] == album_name:
                if artist_name is None or result['artist_name'] == artist_name:
                    return result
        
        return None
    
    def _get_audio_files(self, directory: Path) -> List[str]:
        """
        ディレクトリ内のオーディオファイルを取得
        
        Args:
            directory: 検索対象のディレクトリ
        
        Returns:
            オーディオファイルのパスリスト
        """
        audio_files = []
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    audio_files.append(str(file_path))
            
            # ファイル名でソート
            audio_files.sort()
            
        except Exception as e:
            print(f"ファイル検索エラー in {directory}: {e}")
        
        return audio_files
    
    def search_and_display(self, album_name: str) -> List[Dict[str, any]]:
        """
        アルバムを検索して結果を表示
        
        Args:
            album_name: 検索するアルバム名
        
        Returns:
            検索結果のリスト
        """
        print(f"アルバム名 '{album_name}' を検索中...")
        print("-" * 60)
        
        results = self.find_albums_by_name(album_name)
        
        if not results:
            print("該当するアルバムが見つかりませんでした。")
            return []
        
        print(f"{len(results)}件のアルバムが見つかりました:\n")
        
        for i, album_info in enumerate(results, 1):
            print(f"{i}. アーティスト: {album_info['artist_name']}")
            print(f"   アルバム: {album_info['album_name']}")
            print(f"   パス: {album_info['album_path']}")
            print(f"   楽曲数: {album_info['audio_file_count']}曲")
            print(f"   楽曲ファイル:")
            
            for j, audio_file in enumerate(album_info['audio_files'], 1):
                file_name = Path(audio_file).name
                print(f"     {j:2d}. {file_name}")
            
            print()
        
        return results
    
    def get_all_albums_by_artist(self, artist_name: str) -> List[Dict[str, any]]:
        """
        指定されたアーティストの全アルバムを取得
        
        Args:
            artist_name: アーティスト名
        
        Returns:
            アーティストのアルバム一覧
        """
        if not self.itunes_media_path.exists():
            print(f"iTunes Mediaディレクトリが見つかりません: {self.itunes_media_path}")
            return []
        
        results = []
        artist_path = self.itunes_media_path / artist_name
        
        if not artist_path.exists() or not artist_path.is_dir():
            print(f"アーティストディレクトリが見つかりません: {artist_path}")
            return []
        
        try:
            for album_dir in artist_path.iterdir():
                if album_dir.is_dir():
                    audio_files = self._get_audio_files(album_dir)
                    if audio_files:
                        album_info = {
                            'artist_name': artist_name,
                            'album_name': album_dir.name,
                            'album_path': str(album_dir),
                            'audio_files': audio_files,
                            'audio_file_count': len(audio_files)
                        }
                        results.append(album_info)
        
        except Exception as e:
            print(f"アーティスト検索エラー: {e}")
        
        return results


# 使用例
if __name__ == "__main__":
    finder = iTunesAlbumFinder()
    
    # アルバム名を入力
    album_name = input("検索するアルバム名を入力してください: ")
    
    if album_name:
        results = finder.search_and_display(album_name)
        
        if results:
            print(f"\n検索完了: {len(results)}件のアルバムが見つかりました")
        else:
            print("\n該当するアルバムはありませんでした")
