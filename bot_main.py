import discord
import configparser

config = configparser.ConfigParser()
config.read('config.ini', 'UTF-8')
token = config.get('discord', 'bot_token')
idea_channel_id = config.getint('discord', 'from_channel_id')
reaction_channel_id = config.getint('discord', 'to_channel_id')
good = config.get('discord', 'good')
bad = config.get('discord', 'bad')
info = config.get('discord', 'info')


class BotClient(discord.Client):
    idea_channel = ''
    good_channel = ''

    async def on_ready(self):
        BotClient.idea_channel = BotClient.get_channel(self, idea_channel_id)
        BotClient.good_channel = BotClient.get_channel(self, reaction_channel_id)
        print("アイデアBotが起動しました")

    async def on_raw_reaction_add(self, reaction):
        channel_id = reaction.channel_id
        if channel_id == idea_channel_id:
            await BotClient.on_idea_channel(self, reaction)
        elif channel_id == reaction_channel_id:
            await BotClient.on_reaction_channel(self, reaction)

    async def on_reaction_channel(self, reaction):
        emoji = reaction.emoji.name
        if emoji == good:
            await BotClient.on_good_reaction(self, reaction)
        elif emoji == bad:
            await BotClient.on_bad_reaction(self, reaction)
        elif emoji == info:
            await BotClient.on_info_reaction(self, reaction)

    async def on_good_reaction(self, reaction):
        message_id = reaction.message_id
        message = await BotClient.good_channel.fetch_message(message_id)
        embed = message.embeds[0]
        supporter = embed.fields[0].value
        name = reaction.member.display_name + '(' + str(reaction.member) + ')'
        if str(reaction.member) not in supporter:
            embed.remove_field(0)
            supporter += ', ' + name
            embed.insert_field_at(0, name='賛同者', value=supporter, inline=False)
        await BotClient.good_channel.send(embed=embed)
        await message.delete()

    async def on_bad_reaction(self, reaction):
        message_id = reaction.message_id
        message = await BotClient.good_channel.fetch_message(message_id)
        embed = message.embeds[0]
        await BotClient.good_channel.send(embed=embed)
        await message.delete()

    async def on_info_reaction(self, reaction):
        message_id = reaction.message_id
        message = await BotClient.good_channel.fetch_message(message_id)

    async def on_idea_channel(self, reaction):
        emoji = reaction.emoji.name
        if emoji != good:
            return
        message_id = reaction.message_id
        message = await BotClient.idea_channel.fetch_message(message_id)
        message_url = message.jump_url
        print(message.content)
        print(message.attachments)
        embed = discord.Embed(title=message.author.display_name + 'の企画案',
                              description=message.content,
                              color=discord.Colour.green())
        embed.add_field(name='賛同者',
                        value=reaction.member.display_name + '(' + str(reaction.member) + ')',
                        inline=False)
        embed.add_field(name='リンク', value=message_url, inline=True)
        await BotClient.good_channel.send(embed=embed)


client = BotClient()
client.run(token)
