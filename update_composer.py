import sys
from pathlib import Path
from typing import Optional, Dict, List
from src.itunes_album_finder import iTunesAlbumFinder
from src.audio_metadata_extractor import AudioMetadataExtractor
from src.tower_records_scraper import TowerRecordsScraper
from src.audio_metadata_writer import AudioMetadataWriter


class AlbumComposerUpdater:
    """アルバム内全楽曲のcomposer情報を更新するクラス"""
    
    def __init__(self):
        self.finder = iTunesAlbumFinder()
        self.extractor = AudioMetadataExtractor()
        self.scraper = TowerRecordsScraper()
        self.metadata_writer = AudioMetadataWriter()
    
    def update_album_composers(self, album_name_input: str) -> bool:
        """
        指定されたアルバム名で検索し、該当する全楽曲のcomposer情報を更新
        
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
            
            # Tower Recordsから作詞・作曲・編曲情報を取得
            album_name = album_info['album_name']
            artist_name = album_info['artist_name']
            
            print(f"\n--- Tower Records検索フェーズ ---")
            track_credits = self._get_track_credits_from_tower(album_name, artist_name)
            
            if track_credits:
                print(f"Tower Recordsから {len(track_credits)} 曲の情報を取得")
            else:
                print("Tower Recordsから情報を取得できませんでした")
            
            print(f"\n--- Composer情報埋め込みフェーズ ---")
            
            # アルバム内の各楽曲を処理
            for j, audio_file in enumerate(album_info['audio_files'], 1):
                file_name = Path(audio_file).name
                print(f"\n  [{j:2d}] {file_name}")
                
                # 楽曲のメタデータを取得
                metadata = self.extractor.extract_metadata(audio_file)
                
                if metadata:
                    total_songs += 1
                    track_title = metadata['title']
                    current_composer = metadata.get('composer', '')
                    
                    print(f"       曲名: {track_title}")
                    print(f"       現在のComposer: {current_composer or '(空)'}")
                    
                    # Tower Recordsの情報から該当する楽曲を検索
                    matching_credit = self._find_matching_track_credit(track_title, track_credits)
                    
                    if matching_credit:
                        # 作詞・作曲・編曲情報を組み合わせてcomposerフィールドに埋め込み
                        composer_info = self._format_composer_info(matching_credit)
                        
                        if composer_info and composer_info != current_composer:
                            success = self.metadata_writer.update_composer(audio_file, composer_info)
                            if success:
                                total_success += 1
                                print(f"       ✓ Composer更新成功: {composer_info}")
                            else:
                                print(f"       ✗ Composer更新失敗")
                        else:
                            print(f"       - 更新する情報がないか、既に同じ情報が設定済み")
                    else:
                        print(f"       - Tower Recordsに該当する楽曲情報が見つかりませんでした")
                else:
                    print("       メタデータを取得できませんでした")
        
        print(f"\n" + "=" * 80)
        print(f"処理完了: {total_success}/{total_songs} 件のComposer情報を更新")
        return total_success > 0
    
    def _get_track_credits_from_tower(self, album_name: str, artist_name: str) -> List[Dict]:
        """
        Tower Recordsから楽曲のクレジット情報を取得
        
        Args:
            album_name: アルバム名
            artist_name: アーティスト名
        
        Returns:
            楽曲クレジット情報のリスト
        """
        try:
            # Tower Recordsでアルバムを検索
            search_results = self.scraper.search_album(album_name, artist_name)
            
            if not search_results:
                print("  Tower Recordsで検索結果が見つかりませんでした")
                return []
            
            # 最初の検索結果の詳細を取得
            first_result = search_results[0]
            if not first_result.get('link'):
                print("  商品詳細ページのリンクが見つかりませんでした")
                return []
            
            print(f"  商品詳細ページを解析中: {first_result['title']}")
            
            # 収録内容を解析
            track_credits = self.scraper.parse_track_credits(first_result['link'])
            
            return track_credits
            
        except Exception as e:
            print(f"  Tower Records情報取得エラー: {e}")
            return []
    
    def _find_matching_track_credit(self, track_title: str, track_credits: List[Dict]) -> Optional[Dict]:
        """
        楽曲タイトルに対応するクレジット情報を検索
        
        Args:
            track_title: 楽曲タイトル
            track_credits: Tower Recordsから取得したクレジット情報リスト
        
        Returns:
            該当するクレジット情報
        """
        if not track_title or not track_credits:
            return None
        
        import unicodedata
        import re
        
        def normalize_text(text):
            """全角・半角を統一し、比較用に正規化"""
            if not text:
                return ""
            # 全角英数字を半角に変換
            text = unicodedata.normalize('NFKC', text)
            # 小文字に変換
            text = text.lower()
            # 空白文字を統一
            text = re.sub(r'\s+', ' ', text)
            # 前後の空白を削除
            text = text.strip()
            # 記号を削除（比較用）
            text = re.sub(r'[^\w\s]', '', text)
            return text
        
        # 正規化されたトラックタイトル
        normalized_track_title = normalize_text(track_title)
        
        # 完全一致を優先
        for credit in track_credits:
            tower_title = credit.get('title', '')
            normalized_tower_title = normalize_text(tower_title)
            if normalized_tower_title == normalized_track_title:
                return credit
        
        # 部分一致を検索
        for credit in track_credits:
            tower_title = credit.get('title', '')
            normalized_tower_title = normalize_text(tower_title)
            
            if normalized_tower_title:
                # 1. 8割以上の文字列一致をチェック
                similarity_ratio = self._calculate_similarity_ratio(normalized_track_title, normalized_tower_title)
                if similarity_ratio >= 0.8:
                    return credit
                
                # 2. 部分文字列マッチング
                if (normalized_track_title in normalized_tower_title or 
                    normalized_tower_title in normalized_track_title):
                    return credit
        
        # 楽曲番号による一致を試行
        track_number_match = re.search(r'^(\d+)', track_title)
        if track_number_match:
            track_number = track_number_match.group(1)
            for credit in track_credits:
                credit_number = credit.get('track_number', '')
                if credit_number == track_number:
                    return credit
        
        return None
    
    def _calculate_similarity_ratio(self, text1: str, text2: str) -> float:
        """
        2つのテキスト間の類似度を計算（文字レベル）
        
        Args:
            text1: 比較テキスト1
            text2: 比較テキスト2
        
        Returns:
            類似度（0.0-1.0）
        """
        if not text1 or not text2:
            return 0.0
        
        # 共通文字数を計算
        set1 = set(text1)
        set2 = set(text2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if not union:
            return 0.0
        
        # Jaccard係数を計算
        jaccard = len(intersection) / len(union)
        
        # 長さの類似度も考慮
        length_similarity = min(len(text1), len(text2)) / max(len(text1), len(text2))
        
        # 最終類似度（Jaccard係数と長さ類似度の平均）
        similarity = (jaccard + length_similarity) / 2
        
        return similarity
    
    def _format_composer_info(self, credit: Dict) -> str:
        """
        クレジット情報をcomposerフィールド用にフォーマット
        
        Args:
            credit: Tower Recordsから取得したクレジット情報
        
        Returns:
            フォーマットされたcomposer情報
        """
        parts = []
        
        # 作詞者
        if '作詞' in credit:
            parts.append(f"作詞: {credit['作詞']}")
        
        # 作曲者
        if '作曲' in credit:
            parts.append(f"作曲: {credit['作曲']}")
        
        # 編曲者
        if '編曲' in credit:
            parts.append(f"編曲: {credit['編曲']}")
        
        return '/'.join(parts) if parts else ''
    
    def close(self):
        """リソースを解放"""
        if hasattr(self.scraper, 'close'):
            self.scraper.close()


if __name__ == "__main__":
    updater = AlbumComposerUpdater()
    
    # コマンドライン引数をチェック
    if len(sys.argv) < 2:
        print("使用方法: python3 update_composer.py {アルバム名}")
        print("例: python3 update_composer.py PRiSM")
        print("例: python3 update_composer.py \"My Album Name\"")
        sys.exit(1)
    
    # コマンドライン引数からアルバム名を取得（複数の引数を結合）
    album_name = " ".join(sys.argv[1:]).strip()
    
    if album_name:
        print(f"アルバム '{album_name}' 内の全楽曲のComposer情報を更新します")
        print("=" * 80)
        
        try:
            # アルバム内全楽曲のComposer情報を更新
            success = updater.update_album_composers(album_name)
            
            if success:
                print("\nComposer情報の更新が完了しました！")
            else:
                print("\nComposer情報の更新に失敗しました")
        
        finally:
            updater.close()
    else:
        print("アルバム名を指定してください")
