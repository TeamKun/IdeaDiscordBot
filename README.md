# IdeaDiscordBot
アイデア整理用Discord Bot

Pythonバージョン\
Python 3.9.1

必要ライブラリ\
discord.py
# 機能
・特定チャンネルでいいねリアクションをされた場合、いいねされた投稿をいいねチャンネルにコピーして投稿する\
・いいねチャンネルでいいねされた場合、賛同者の名前を記載していいねチャンネルの一番下に持ってくる\
・いいねチャンネルで特定リアクションをされた場合、リアクションした人のIDが賛同者の中に記載されていれば賛同者から名前を削除する\
・いいねチャンネルで特定リアクションをされた場合、リアクションした人に補足情報を追加するためのDMを送る\
 補足情報があった場合、リアクションがあった投稿に補足情報を追記する\
・いいねチャンネル内で2週間経過した投稿をチェックして削除する