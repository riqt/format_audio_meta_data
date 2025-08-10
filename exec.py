import src.fetch_itunes_artwork.iTunesArtworkFetcher

if __name__ == "__main__":
    fetcher = iTunesArtworkFetcher()
    
    # 検索とダウンロード
    query = input("検索する曲名・アーティスト名・アルバム名を入力してください: ")
    
    print(f"\n'{query}' を検索中...")
    
    downloaded_items = list(fetcher.search_and_download(
        query=query,
        output_dir="artwork",
        quality="large",  # small, medium, large, original から選択
        country="jp"
    ))
    
    if downloaded_items:
        print(f"\n{len(downloaded_items)}件のアートワークをダウンロードしました")
    else:
        print("\nダウンロードできるアートワークが見つかりませんでした")
