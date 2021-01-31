import asyncio
import re
import configparser
from datetime import datetime, timedelta

import discord
from discord.ext import tasks


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
        print("Botが起動しました")
        BotClient.check_expired_post.start(BotClient)

    @tasks.loop(hours=24)
    async def check_expired_post(self):
        today = datetime.now()
        two_weeks = today - timedelta(weeks=2)
        messages = []
        async for message in BotClient.good_channel.history(before=two_weeks):
            messages.append(message)
        await BotClient.good_channel.delete_messages(messages)

    async def on_raw_reaction_add(self, reaction):
        channel_id = reaction.channel_id
        if reaction.member.bot:
            return
        if channel_id == idea_channel_id:
            await BotClient.on_idea_channel(self, reaction)
        elif channel_id == reaction_channel_id:
            await BotClient.on_reaction_channel(self, reaction)

    async def on_idea_channel(self, reaction):
        emoji = reaction.emoji.name
        if emoji != good:
            return
        message_id = reaction.message_id
        message = await BotClient.idea_channel.fetch_message(message_id)
        message_url = message.jump_url
        attachment_files = []
        for attachment in message.attachments:
            attachment_files.append(await attachment.to_file())
        embed = discord.Embed(title=message.author.display_name + 'の企画案',
                              description=message.content,
                              color=discord.Colour.green())
        embed.add_field(name='賛同者',
                        value=reaction.member.display_name + '(' + str(reaction.member) + ')',
                        inline=False)
        embed.add_field(name='リンク', value=message_url, inline=True)
        sent_message = await BotClient.good_channel.send(embed=embed, files=attachment_files)
        await sent_message.add_reaction('👍')
        await sent_message.add_reaction('👎')
        await sent_message.add_reaction('🧐')

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
        supporter_field_pos = len(embed.fields) - 2
        supporter = embed.fields[supporter_field_pos].value
        if str(reaction.member) not in supporter:
            embed.remove_field(supporter_field_pos)
            name = reaction.member.display_name + '(' + str(reaction.member) + ')'
            supporter += ', ' + name
            embed.insert_field_at(supporter_field_pos, name='賛同者', value=supporter, inline=False)
        attachment_files = []
        for attachment in message.attachments:
            attachment_files.append(await attachment.to_file())
        sent_message = await BotClient.good_channel.send(embed=embed, files=attachment_files)
        await sent_message.add_reaction('👍')
        await sent_message.add_reaction('👎')
        await sent_message.add_reaction('🧐')
        await message.delete()

    async def on_bad_reaction(self, reaction):
        emoji = reaction.emoji.name
        message_id = reaction.message_id
        message = await BotClient.good_channel.fetch_message(message_id)
        embed = message.embeds[0]
        supporter_field_pos = len(embed.fields) - 2
        supporter = embed.fields[supporter_field_pos].value
        regex = ',.+\(' + str(reaction.member) + '\)|'\
                '.+\(' +str(reaction.member) + '\),|' \
                '^(?!.*,).+\(' + str(reaction.member) + '\)'
        if str(reaction.member) in supporter:
            embed.remove_field(supporter_field_pos)
            supporter = re.sub(regex, '', supporter)
            if len(supporter) == 0:
                await message.delete()
            else:
                emoji = reaction.emoji.name
                embed.insert_field_at(supporter_field_pos, name='賛同者', value=supporter, inline=False)
                await message.edit(embed=embed)
                await message.remove_reaction(emoji, reaction.member)
        else:
            await message.remove_reaction(emoji, reaction.member)

    async def on_info_reaction(self, reaction):
        wait_time = 1.0 * 60.0 * 60.0
        emoji = reaction.emoji.name
        content = '以下の企画案に補足説明をしますか？\n補足説明を追加する場合は1時間以内に補足の内容を返信してください'
        exp = ''
        old_attachment_files = []
        new_attachment_files = []
        attachments = []
        message_id = reaction.message_id
        message = await BotClient.good_channel.fetch_message(message_id)
        name = reaction.member.display_name + '(' + str(reaction.member) + ')'
        await message.remove_reaction(emoji, reaction.member)
        for attachment in message.attachments:
            attachments.append(attachment)
            old_attachment_files.append(await attachment.to_file())
        embed = message.embeds[0]
        await reaction.member.send(content=content, embed=embed, files=old_attachment_files)

        def add_explanation(msg):
            if not msg.author.bot and msg.author.id == reaction.member.id:
                nonlocal name, exp, attachments
                exp = msg.content + ' / ' + name
                for attach in msg.attachments:
                    attachments.append(attach)
                return True

        try:
            await self.wait_for('message', timeout=wait_time, check=add_explanation)
        except asyncio.TimeoutError:
            content = '時間切れです😢'
        else:
            embed.insert_field_at(0, name='企画案の補足', value=exp, inline=False)
            for attachment in attachments:
                new_attachment_files.append(await attachment.to_file())
            content = '企画案の補足を追記しました👍'
            sent_message = await BotClient.good_channel.send(embed=embed, files=new_attachment_files)
            await sent_message.add_reaction('👍')
            await sent_message.add_reaction('👎')
            await sent_message.add_reaction('🧐')
            await message.delete()
        await reaction.member.send(content=content)


client = BotClient()
client.run(token)
