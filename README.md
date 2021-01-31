# IdeaDiscordBot
アイデア整理用Discord Bot
# 機能
・特定チャンネルでいいねリアクションをされた場合、いいねされた投稿をいいねチャンネルにコピーして投稿する\
・いいねチャンネルでいいねされた場合、賛同者の名前を記載していいねチャンネルの一番下に持ってくる\
・いいねチャンネルで特定リアクションをされた場合、リアクションした人のIDが賛同者の中に記載されていれば賛同者から名前を削除する\
・いいねチャンネルで特定リアクションをされた場合、リアクションした人に補足情報を追加するためのDMを送る\
補足情報があった場合、リアクションがあった投稿に補足情報を追記する\
・いいねチャンネル内で2週間経過した投稿をチェックして削除する\
・特権ユーザーがいいねした投稿を第3のチャンネルに移動させる機能(デフォルトFalse)
・特権ユーザーがbadした投稿を没にする
# 実行に必要なファイル
bot_main.py\
config.ini
# Pythonのバージョンと必要ライブラリ
Pythonバージョン\
Python 3.9.1

必要ライブラリ\
discord.py
# 設定
config.iniの各パラメータを設定する

bot_token = ボットToken\
from_channel_id = いいねをする元のチャンネル\
to_channel_id = いいねした後に投稿を移動するチャンネル\
third_channel_id = 第3のチャンネルID\
third_channel = 第3のチャンネルに移動させる機能を使う(True/False Falseデフォルト)
super_user = スーパーユーザーのID(,区切りでIDを記載すると複数可)\
good = いいねリアクション(ユニコードに存在するリアクション。デフォは👍)\
bad = 取り消しリアクション(ユニコードに存在するリアクション。デフォは👎)\
info = 補足リアクション(ユニコードに存在するリアクション。デフォは🖊️)

# 必要権限(Discord Bot)
Text Permissions
 - Send messages
 - Manage Messages
 - Embed Links
 - Attach Links
 - Read Message History
 - Add Reaction

