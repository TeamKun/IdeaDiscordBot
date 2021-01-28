import discord
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
token = config.get('discord', 'bot_token')


class BotClient(discord.Client):
    from_channel_id = config.getint('discord', 'from_channel_id')
    to_channel_id = config.getint('discord', 'to_channel_id')

    async def on_ready(self):
        print("Bot起動")

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))

    async def on_raw_reaction_add(self, reaction):
        channel_id = reaction.channel_id
        if channel_id != BotClient.from_channel_id:
            return
        emoji = reaction.emoji.name
        if emoji != '👍':
            return
        from_channel = BotClient.get_channel(self, BotClient.from_channel_id)
        to_channel = BotClient.get_channel(self, BotClient.to_channel_id)
        message_id = reaction.message_id
        message = await from_channel.fetch_message(message_id)
        message_url = message.jump_url

        print(message_url)
        print(message.author)
        print(message.content)
        print(message.attachments)
        embed = discord.Embed(title=message.author.display_name + 'の企画案',
                              description=message.content, url=message_url)
        embed.add_field(name='賛同者', value=reaction.member, inline=False)
        embed.set_footer(text='元のメッセージ：'+message_url)
        await to_channel.send(embed=embed)


client = BotClient()
client.run(token)