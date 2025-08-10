from src.itunes_album_finder import iTunesAlbumFinder
from src.audio_metadata_extractor import AudioMetadataExtractor

if __name__ == "__main__":
    finder = iTunesAlbumFinder()
    extractor = AudioMetadataExtractor()
    
    # アルバム名を入力
    album_name = input("検索するアルバム名を入力してください: ")
    
    if album_name:
        results = finder.find_albums_by_name(album_name)
        
        if results:
            print(f"\n{len(results)}件のアルバムが見つかりました")
            print("=" * 80)
            
            for i, album_info in enumerate(results, 1):
                print(f"\n【{i}】アーティスト: {album_info['artist_name']}")
                print(f"    アルバム: {album_info['album_name']}")
                print(f"    パス: {album_info['album_path']}")
                print(f"    楽曲数: {album_info['audio_file_count']}曲")
                print("-" * 60)
                
                # 各楽曲の詳細情報を取得・表示
                for j, audio_file in enumerate(album_info['audio_files'], 1):
                    print(f"\n  [{j:2d}] {audio_file}")
                    metadata = extractor.extract_metadata(audio_file)
                    
                    if metadata:
                        print(f"       タイトル: {metadata['title']}")
                        print(f"       アーティスト: {metadata['artist']}")
                        print(f"       アルバム: {metadata['album']}")
                        print(f"       作曲者: {metadata['composer']}")
                        print(f"       年: {metadata['year']}")
                        print(f"       アートワーク: {'あり' if metadata['has_artwork'] else 'なし'}")
                    else:
                        print("       メタデータを取得できませんでした")
                
                print("-" * 60)
        else:
            print("\n該当するアルバムはありませんでした")
