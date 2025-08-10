import os
from pathlib import Path
from typing import Optional, Dict
try:
    from mutagen import File
except ImportError:
    print("mutagenライブラリが必要です。pip install mutagenでインストールしてください。")
    raise


class AudioMetadataExtractor:
    """音楽ファイルからメタデータを抽出するクラス"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.aiff', '.aif', '.m4a', '.aac', '.flac', '.ogg', '.wav']
    
    def extract_metadata(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        音楽ファイルからアルバム名とアーティスト名を取得
        
        Args:
            file_path: 音楽ファイルのパス
        
        Returns:
            アルバム名とアーティスト名の辞書、失敗時はNone
        """
        try:
            # ファイルの存在確認
            if not os.path.exists(file_path):
                print(f"ファイルが見つかりません: {file_path}")
                return None
            
            # ファイル形式の確認
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in self.supported_formats:
                print(f"サポートされていないファイル形式です: {file_extension}")
                return None
            
            # メタデータを読み込み
            audio_file = File(file_path)
            if audio_file is None:
                print(f"メタデータを読み込めませんでした: {file_path}")
                return None
            
            # アーティスト名を取得（複数のタグから試行）
            artist = self._get_artist(audio_file)
            
            # アルバム名を取得
            album = self._get_album(audio_file)
            
            # 曲名を取得
            title = self._get_title(audio_file)
            
            # 作曲者を取得
            composer = self._get_composer(audio_file)
            
            # 年を取得
            year = self._get_year(audio_file)
            
            # アートワークの有無を確認
            has_artwork = self._has_artwork(audio_file)
            
            result = {
                'artist': artist or 'Unknown Artist',
                'album': album or 'Unknown Album',
                'title': title or 'Unknown Title',
                'file_path': file_path,
                'composer': composer or 'Unknown Composer',
                'year': year or 'Unknown Year',
                'has_artwork': has_artwork
            }
            
            return result
            
        except Exception as e:
            print(f"メタデータ取得エラー: {e}")
            return None
    
    def _get_artist(self, audio_file) -> Optional[str]:
        """アーティスト名を取得（複数のタグから試行）"""
        artist_tags = ['TPE1', 'ARTIST', '\xa9ART', 'Artist', 'ALBUMARTIST', 'TPE2', '©ART']
        
        for tag in artist_tags:
            if tag in audio_file:
                value = audio_file[tag]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    def _get_album(self, audio_file) -> Optional[str]:
        """アルバム名を取得"""
        album_tags = ['TALB', 'ALBUM', '\xa9alb', 'Album', '©alb']
        
        for tag in album_tags:
            if tag in audio_file:
                value = audio_file[tag]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    def _get_title(self, audio_file) -> Optional[str]:
        """曲名を取得"""
        title_tags = ['TIT2', 'TITLE', '\xa9nam', 'Title', '©nam']
        
        for tag in title_tags:
            if tag in audio_file:
                value = audio_file[tag]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    def _get_composer(self, audio_file) -> Optional[str]:
        """作曲者を取得"""
        composer_tags = ['TCOM', 'COMPOSER', '\xa9wrt', 'Composer', '©wrt']
        
        for tag in composer_tags:
            if tag in audio_file:
                value = audio_file[tag]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    def _get_year(self, audio_file) -> Optional[str]:
        """年を取得"""
        year_tags = ['TDRC', 'DATE', '\xa9day', 'Year', 'TYER', '©day']
        
        for tag in year_tags:
            if tag in audio_file:
                value = audio_file[tag]
                if isinstance(value, list) and value:
                    year_str = str(value[0])
                    # 日付形式（YYYY-MM-DD）から年のみを抽出
                    if '-' in year_str:
                        return year_str.split('-')[0]
                    return year_str
                elif value:
                    year_str = str(value)
                    if '-' in year_str:
                        return year_str.split('-')[0]
                    return year_str
        return None
    
    def _has_artwork(self, audio_file) -> bool:
        """アートワークが存在するかどうかを確認"""
        # ID3タグ（MP3）のアートワーク
        for tag in audio_file.keys():
            if tag.startswith('APIC'):  # ID3v2のアートワークタグ
                return True
        
        # FLAC
        if hasattr(audio_file, 'pictures') and audio_file.pictures:
            return True
        
        # MP4/M4A
        if 'covr' in audio_file:
            return True
        
        return False
    
    def extract_from_file_path(self, file_path: str) -> Dict[str, str]:
        """
        ファイルパスからメタデータを抽出し、見やすい形式で表示
        
        Args:
            file_path: 音楽ファイルのパス
        
        Returns:
            抽出されたメタデータ
        """
        print(f"ファイル: {file_path}")
        print("-" * 50)
        
        metadata = self.extract_metadata(file_path)
        
        if metadata:
            print(f"アーティスト: {metadata['artist']}")
            print(f"アルバム: {metadata['album']}")
            print(f"曲名: {metadata['title']}")
            print(f"作曲者: {metadata['composer']}")
            print(f"年: {metadata['year']}")
            print(f"アートワーク: {'あり' if metadata['has_artwork'] else 'なし'}")
            return metadata
        else:
            print("メタデータを取得できませんでした")
            return {
                'artist': 'Unknown Artist', 
                'album': 'Unknown Album', 
                'title': 'Unknown Title', 
                'file_path': file_path,
                'composer': 'Unknown Composer',
                'year': 'Unknown Year',
                'has_artwork': False
            }


# 使用例
if __name__ == "__main__":
    extractor = AudioMetadataExtractor()
    
    # テスト用のファイルパス
    test_file = input("音楽ファイルのパスを入力してください: ")
    
    if test_file:
        result = extractor.extract_from_file_path(test_file)
        print("\n取得結果:")
        print(result)
