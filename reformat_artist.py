import os
from mutagen.aiff import AIFF

album_dir = 'G:\iTunes\iTunes Media\Music\Compilations\異次元フェス アイドルマスター★ ラブライブ! 歌合戦 LIVE CD'

songs = [song for song in os.listdir(album_dir) if os.path.isfile(os.path.join(album_dir, song))]

print(songs)
