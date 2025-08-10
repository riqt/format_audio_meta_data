import os
from pathlib import Path
from typing import Optional
import mimetypes


class AudioMetadataWriter:
    """音楽ファイルにメタデータを書き込むクラス"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.aiff', '.aif', '.m4a', '.aac', '.flac', '.ogg', '.wav']
    
    def embed_artwork(self, audio_file_path: str, artwork_file_path: str) -> bool:
        """
        音楽ファイルにアートワークを埋め込む
        
        Args:
            audio_file_path: 音楽ファイルのパス
            artwork_file_path: アートワーク画像ファイルのパス
        
        Returns:
            成功したかどうか
        """
        try:
            from mutagen import File
            
            # ファイルの存在確認
            if not os.path.exists(audio_file_path):
                print(f"音楽ファイルが見つかりません: {audio_file_path}")
                return False
            
            if not os.path.exists(artwork_file_path):
                print(f"アートワークファイルが見つかりません: {artwork_file_path}")
                return False
            
            # ファイル形式の確認
            file_extension = Path(audio_file_path).suffix.lower()
            if file_extension not in self.supported_formats:
                print(f"サポートされていないファイル形式です: {file_extension}")
                return False
            
            # アートワークデータを読み込み
            with open(artwork_file_path, 'rb') as f:
                artwork_data = f.read()
            
            # MIMEタイプを取得
            mime_type = mimetypes.guess_type(artwork_file_path)[0]
            if not mime_type:
                mime_type = 'image/jpeg'  # デフォルト
            
            # ファイル形式に応じて処理
            if file_extension == '.mp3':
                return self._embed_to_mp3(audio_file_path, artwork_data, mime_type)
            elif file_extension in ['.m4a', '.aac', '.mp4']:
                return self._embed_to_mp4(audio_file_path, artwork_data, mime_type)
            elif file_extension == '.flac':
                return self._embed_to_flac(audio_file_path, artwork_data, mime_type)
            else:
                print(f"アートワーク埋め込み未対応の形式です: {file_extension}")
                return False
                
        except ImportError as e:
            print(f"必要なライブラリがインストールされていません: {e}")
            return False
        except Exception as e:
            print(f"アートワーク埋め込みエラー: {e}")
            return False
    
    def _embed_to_mp3(self, audio_file_path: str, artwork_data: bytes, mime_type: str) -> bool:
        """MP3ファイルにアートワークを埋め込み"""
        try:
            from mutagen.id3 import ID3, APIC, ID3NoHeaderError
            
            try:
                audio_file = ID3(audio_file_path)
            except ID3NoHeaderError:
                audio_file = ID3()
            
            # 既存のアートワークを削除
            audio_file.delall('APIC')
            
            # 新しいアートワークを追加
            audio_file.add(APIC(
                encoding=3,  # UTF-8
                mime=mime_type,
                type=3,  # Cover (front)
                desc='Cover',
                data=artwork_data
            ))
            
            audio_file.save(audio_file_path)
            return True
            
        except Exception as e:
            print(f"MP3埋め込みエラー: {e}")
            return False
    
    def _embed_to_mp4(self, audio_file_path: str, artwork_data: bytes, mime_type: str) -> bool:
        """M4A/MP4ファイルにアートワークを埋め込み"""
        try:
            from mutagen.mp4 import MP4, MP4Cover
            
            audio_file = MP4(audio_file_path)
            
            # カバーフォーマットを決定
            if mime_type == 'image/png':
                cover_format = MP4Cover.FORMAT_PNG
            else:
                cover_format = MP4Cover.FORMAT_JPEG
            
            # アートワークを設定
            audio_file['covr'] = [MP4Cover(artwork_data, cover_format)]
            
            audio_file.save()
            return True
            
        except Exception as e:
            print(f"M4A/MP4埋め込みエラー: {e}")
            return False
    
    def _embed_to_flac(self, audio_file_path: str, artwork_data: bytes, mime_type: str) -> bool:
        """FLACファイルにアートワークを埋め込み"""
        try:
            from mutagen.flac import FLAC, Picture
            
            audio_file = FLAC(audio_file_path)
            
            # 既存のピクチャーを削除
            audio_file.clear_pictures()
            
            # 新しいピクチャーを作成
            picture = Picture()
            picture.type = 3  # Cover (front)
            picture.mime = mime_type
            picture.desc = 'Cover'
            picture.data = artwork_data
            
            audio_file.add_picture(picture)
            audio_file.save()
            return True
            
        except Exception as e:
            print(f"FLAC埋め込みエラー: {e}")
            return False
    
    def update_metadata(self, audio_file_path: str, metadata: dict) -> bool:
        """
        音楽ファイルのメタデータを更新
        
        Args:
            audio_file_path: 音楽ファイルのパス
            metadata: 更新するメタデータの辞書
                     {'title': '曲名', 'artist': 'アーティスト', 'album': 'アルバム名', ...}
        
        Returns:
            成功したかどうか
        """
        try:
            from mutagen import File
            
            if not os.path.exists(audio_file_path):
                print(f"音楽ファイルが見つかりません: {audio_file_path}")
                return False
            
            audio_file = File(audio_file_path)
            if audio_file is None:
                print(f"音楽ファイルを読み込めませんでした: {audio_file_path}")
                return False
            
            file_extension = Path(audio_file_path).suffix.lower()
            
            # ファイル形式に応じてメタデータを更新
            if file_extension == '.mp3':
                return self._update_mp3_metadata(audio_file_path, metadata)
            elif file_extension in ['.m4a', '.aac', '.mp4']:
                return self._update_mp4_metadata(audio_file_path, metadata)
            elif file_extension == '.flac':
                return self._update_flac_metadata(audio_file_path, metadata)
            else:
                print(f"メタデータ更新未対応の形式です: {file_extension}")
                return False
                
        except Exception as e:
            print(f"メタデータ更新エラー: {e}")
            return False
    
    def _update_mp3_metadata(self, audio_file_path: str, metadata: dict) -> bool:
        """MP3ファイルのメタデータを更新"""
        try:
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCOM, TDRC, ID3NoHeaderError
            
            try:
                audio_file = ID3(audio_file_path)
            except ID3NoHeaderError:
                audio_file = ID3()
            
            # メタデータマッピング
            tag_mapping = {
                'title': TIT2,
                'artist': TPE1,
                'album': TALB,
                'composer': TCOM,
                'year': TDRC
            }
            
            for key, value in metadata.items():
                if key in tag_mapping and value:
                    audio_file.add(tag_mapping[key](encoding=3, text=str(value)))
            
            audio_file.save(audio_file_path)
            return True
            
        except Exception as e:
            print(f"MP3メタデータ更新エラー: {e}")
            return False
    
    def _update_mp4_metadata(self, audio_file_path: str, metadata: dict) -> bool:
        """M4A/MP4ファイルのメタデータを更新"""
        try:
            from mutagen.mp4 import MP4
            
            audio_file = MP4(audio_file_path)
            
            # メタデータマッピング
            tag_mapping = {
                'title': '\xa9nam',
                'artist': '\xa9ART',
                'album': '\xa9alb',
                'composer': '\xa9wrt',
                'year': '\xa9day'
            }
            
            for key, value in metadata.items():
                if key in tag_mapping and value:
                    audio_file[tag_mapping[key]] = [str(value)]
            
            audio_file.save()
            return True
            
        except Exception as e:
            print(f"M4A/MP4メタデータ更新エラー: {e}")
            return False
    
    def _update_flac_metadata(self, audio_file_path: str, metadata: dict) -> bool:
        """FLACファイルのメタデータを更新"""
        try:
            from mutagen.flac import FLAC
            
            audio_file = FLAC(audio_file_path)
            
            # メタデータマッピング
            tag_mapping = {
                'title': 'TITLE',
                'artist': 'ARTIST',
                'album': 'ALBUM',
                'composer': 'COMPOSER',
                'year': 'DATE'
            }
            
            for key, value in metadata.items():
                if key in tag_mapping and value:
                    audio_file[tag_mapping[key]] = [str(value)]
            
            audio_file.save()
            return True
            
        except Exception as e:
            print(f"FLACメタデータ更新エラー: {e}")
            return False


# 使用例
if __name__ == "__main__":
    writer = AudioMetadataWriter()
    
    # テスト用
    audio_file = input("音楽ファイルのパスを入力してください: ").strip()
    artwork_file = input("アートワークファイルのパスを入力してください: ").strip()
    
    if audio_file and artwork_file:
        success = writer.embed_artwork(audio_file, artwork_file)
        if success:
            print("アートワークの埋め込みが完了しました！")
        else:
            print("アートワークの埋め込みに失敗しました")
    else:
        print("ファイルパスを入力してください")