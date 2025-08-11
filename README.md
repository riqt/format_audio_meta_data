# format_audio_meta_data

## Usage
### 初期設定
- `config/config.yaml.example`をもとに`config/config.yaml`を作成してください
  - 楽曲を管理するパス（例：`G:/iTunes/iTunes Media/Music`）を実行環境に合わせて設定する必要があります
### アルバムアートワーク取得
- アルバムを指定し、そのアルバムに含まれる楽曲のアートワークを追加する
- すでにアートワークが存在する楽曲に対しては、アートワークを更新しない
- アートワークは[iTunes Search API](https://performance-partners.apple.com/search-api)で取得する
```commandline
python3 update_album_artworks.py {アルバム名}
```
### 作家情報取得
- アルバムを指定し、そのアルバムに含まれる楽曲の作家情報を更新する
- すでに作家情報が登録されている楽曲も更新される
- 作家情報は[tower.jp](https://tower.jp/)に登録されている値を取得する
```commandline
python3 update_composer.py {アルバム名}
```

## TODO
### Feature development
- 歌詞の取得
- アーティスト名/アルバム名のフォーマット
  - 大文字、小文字や記号(、|, )の統一
  - キャラソンのCV表記
- 呼び出し方修正、UI追加
  - As is: あらかじめ登録した楽曲管理パスから、入力したアルバム名に一致するディレクトリを走査する
  - To be: アルバムのディレクトリをドラッグ&ドロップする
