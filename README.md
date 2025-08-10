# format_audio_meta_data

## Usage
### 初期設定
- `config/config.yaml.example`をもとに`config/config.yaml`を作成してください
  - 楽曲を管理するパス（例：`G:/iTunes/iTunes Media/Music`）を実行環境に合わせて設定する必要があります
### アルバムアートワーク取得
- アルバムを指定し、そのアルバムに含まれる楽曲のアートワークを追加する
- すでにアートワークが存在する楽曲に対しては、アートワークを更新しない
- アートワークは`tmp/artwork/{アルバム名}.jpg`に保存される
```commandline
python3 add_album_artworks.py {アルバム名}
```

## TODO
### bug fix
- "{アルバム} {アーティスト}"で検索、保存する
- 複数のアルバムが検索でヒットした場合の挙動
  - complicationアルバムを考慮する（アーティストを含めると検索に出ない場合がある）
### Feature development
- 歌詞の取得
- 作曲家/編曲家（/作詞家）の取得
- アーティスト名/アルバム名のフォーマット
  - 大文字、小文字や記号(、|, )の統一
  - CV表記
