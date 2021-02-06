import asyncio
import os
import configparser
from datetime import datetime, timedelta

import discord
from discord.ext import tasks


config = configparser.ConfigParser()
config.read('config.ini', 'UTF-8')
token = os.environ.get('DISCORD_TOKEN') or config.get('discord', 'bot_token')
idea_channel_id = config.getint('discord', 'from_channel_id')
reaction_channel_id = config.getint('discord', 'to_channel_id')
super_to_channel_id = config.getint('discord', 'super_to_channel_id')
super_from_channels_id = config.get('discord', 'super_from_channels_id').replace(' ', '').split(',')
super_users_id = config.get('discord', 'super_users_id').replace(' ', '').split(',')
good = config.get('discord', 'good')
bad = config.get('discord', 'bad')
info = config.get('discord', 'info')


class BotClient(discord.Client):
    good_channel = ''
    super_from_channels = []
    super_to_channel = ''
    use_super = True

    async def on_ready(self):
        BotClient.good_channel = BotClient.get_channel(self, reaction_channel_id)
        if not super_from_channels_id[0] == 0:
            for super_from in super_from_channels_id:
                BotClient.super_from_channels.append(BotClient.get_channel(self, int(super_from)))
        else:
            BotClient.use_super = False
        if super_users_id[0] == 0:
            BotClient.use_super = False
        if not super_to_channel_id == 0:
            BotClient.super_to_channel = BotClient.get_channel(self, super_to_channel_id)
        else:
            BotClient.use_super = False
        print("Botが起動しました")
        BotClient.check_expired_post.start(BotClient)

    # 2週間経過したメッセージを消去する（1日ごとに実行）
    @tasks.loop(hours=24)
    async def check_expired_post(self):
        today = datetime.now()
        two_weeks = today - timedelta(weeks=2)
        async for message in BotClient.good_channel.history(before=two_weeks):
            await message.delete()

    # リアクションされたとき
    async def on_raw_reaction_add(self, reaction):
        channel_id = reaction.channel_id
        if reaction.member is None or reaction.member.bot:
            return
        if channel_id == idea_channel_id or\
                (channel_id != reaction_channel_id and
                 channel_id != super_to_channel_id and
                 str(channel_id) in super_from_channels_id):

            await BotClient.on_from_channel(self, reaction)
        elif channel_id == reaction_channel_id:
            await BotClient.on_reaction_channel(self, reaction)

    # アイデアチャンネルでいいねが押された時の処理
    async def on_from_channel(self, reaction):
        emoji = reaction.emoji.name
        channel = BotClient.get_channel(self, reaction.channel_id)
        if emoji != good:
            return
        message_id = reaction.message_id
        message = await channel.fetch_message(message_id)
        member = await message.guild.fetch_member(message.author.id)
        author_id = member.id
        message_url = message.jump_url

        async for msg in BotClient.good_channel.history():
            embed = msg.embeds[0]
            supporter_field_pos = len(embed.fields) - 1
            if message_url in embed.fields[supporter_field_pos].value:
                await BotClient.send_good(self, msg.id, reaction.member)
                return
        date = message.created_at.strftime('%Y/%m/%d')
        attachment_files = []
        for attachment in message.attachments:
            attachment_files.append(await attachment.to_file())

        embed = discord.Embed(title=member.display_name + ' の企画案',
                              description=message.content,
                              color=discord.Colour.green())
        embed.add_field(name='👍 いいね',
                        value='<@' + str(reaction.member.id) + '>',
                        inline=False)
        embed.add_field(name='💡 元ネタ',
                        value='<@' + str(author_id) + '> [' + date + ' の企画](' + message_url + ')より',
                        inline=False)
        if BotClient.use_super and str(reaction.member.id) in super_users_id:
            if str(reaction.channel_id) in super_from_channels_id:
                await BotClient.super_to_channel.send(embed=embed, files=attachment_files)
                return
        sent_message = await BotClient.good_channel.send(embed=embed, files=attachment_files)
        await sent_message.add_reaction(good)
        await sent_message.add_reaction(bad)
        await sent_message.add_reaction(info)

    # リアクションチャンネルでリアクションが押された時の処理
    async def on_reaction_channel(self, reaction):
        emoji = reaction.emoji.name
        if emoji == good:
            await BotClient.on_good_reaction(self, reaction)
        elif emoji == bad:
            await BotClient.on_bad_reaction(self, reaction)
        elif emoji == info:
            await BotClient.on_info_reaction(self, reaction)

    # いいね時の処理
    async def send_good(self, message_id, member):
        message = await BotClient.good_channel.fetch_message(message_id)
        member_id = str(member.id)
        is_newest = False
        has_name = False
        embed = message.embeds[0]
        link_pos = len(embed.fields) - 1
        pos_fix = 1
        damedane_pos = link_pos - 1
        damedane = ''
        damedaname = ''
        if 'だめだね' in embed.fields[damedane_pos].name:
            damedane = embed.fields[damedane_pos].value
            damedaname = embed.fields[damedane_pos].name
            pos_fix = 2
        supporter_pos = link_pos - pos_fix
        supporter = embed.fields[supporter_pos].value
        if member_id not in supporter:
            if member_id in damedane:
                damedane = damedane.replace('<@' + member_id + '>', '')
                embed.remove_field(damedane_pos)
                if len(damedane) != 0:
                    embed.insert_field_at(damedane_pos,
                                          name=damedaname,
                                          value=damedane,
                                          inline=False)
            else:
                embed.remove_field(supporter_pos)
                supporter += '<@' + member_id + '>'
                embed.insert_field_at(supporter_pos,
                                      name='👍 いいね',
                                      value=supporter,
                                      inline=False)
        else:
            has_name = True
        attachment_files = []
        for attachment in message.attachments:
            attachment_files.append(await attachment.to_file())
        if BotClient.use_super:
            if member_id in super_users_id:
                await BotClient.super_to_channel.send(embed=embed, files=attachment_files)
                await message.delete()
                return

        # 最新の投稿チェック
        async for msg in BotClient.good_channel.history(limit=1, oldest_first=False):
            if msg.id == message_id:
                is_newest = True
        if is_newest:
            if not has_name:
                await message.edit(embed=embed)
            await message.remove_reaction(good, member)
        else:
            sent_message = await BotClient.good_channel.send(embed=embed, files=attachment_files)
            await sent_message.add_reaction(good)
            await sent_message.add_reaction(bad)
            await sent_message.add_reaction(info)
            await message.delete()

    # いいねのリアクションがいいねチャンネルでされたとき
    async def on_good_reaction(self, reaction):
        message_id = reaction.message_id
        await BotClient.send_good(self, message_id, reaction.member)

    # バッドリアクションがいいねチャンネルでされたとき
    async def on_bad_reaction(self, reaction):
        emoji = reaction.emoji.name
        member_id = str(reaction.member.id)
        message_id = reaction.message_id
        message = await BotClient.good_channel.fetch_message(message_id)
        embed = message.embeds[0]
        link_pos = len(embed.fields) - 1
        pos_fix = 1
        damedane_pos = link_pos - pos_fix
        damedane = ''
        if 'だめだね' in embed.fields[damedane_pos].name:
            pos_fix = 2
            damedane = embed.fields[damedane_pos].value
        supporter_pos = link_pos - pos_fix

        # スーパーユーザーの処理
        if BotClient.use_super and member_id in super_users_id:
            content = '<@' + str(reaction.member.id) + '>によって没になりました'
            await message.remove_reaction(emoji, reaction.member)
            title = '~~' + embed.title + '~~'
            bad_embed = discord.Embed(title=title,
                                      description=embed.description,
                                      color=discord.Colour.red())
            bad_embed.add_field(name=embed.fields[supporter_pos].name,
                                value=embed.fields[supporter_pos].value,
                                inline=False)
            if 'だめだね' in embed.fields[link_pos].name:
                bad_embed.add_field(name=embed.fields[link_pos].name,
                                    value=embed.fields[link_pos].value,
                                    inline=False)
            bad_embed.add_field(name=embed.fields[link_pos].name,
                                value=embed.fields[link_pos].value,
                                inline=False)
            await message.delete()
            await BotClient.good_channel.send(content=content, embed=bad_embed)
            return

        supporter = embed.fields[supporter_pos].value
        if member_id in supporter:
            field_name = embed.fields[supporter_pos].name
            embed.remove_field(supporter_pos)
            supporter = supporter.replace('<@' + member_id + '>', '')
            if len(supporter) == 0:
                await message.delete()
            else:
                emoji = reaction.emoji.name
                embed.insert_field_at(supporter_pos,
                                      name=field_name,
                                      value=supporter,
                                      inline=False)
                await message.edit(embed=embed)
                await message.remove_reaction(emoji, reaction.member)
        else:
            if len(damedane) != 0:
                embed.remove_field(damedane_pos)
                damedane_pos = damedane_pos - 1
            if member_id not in damedane:
                damedane += '<@' + member_id + '>'
                embed.insert_field_at(damedane_pos + 1,
                                      name='👎 だめだね～',
                                      value=damedane,
                                      inline=False)
                await message.edit(embed=embed)
            await message.remove_reaction(emoji, reaction.member)

    # 補足追加処理
    async def on_info_reaction(self, reaction):
        reaction_wait_time = 1.0 * 60.0 * 3
        explanation_wait_time = 1.0 * 60.0 * 10
        emoji = reaction.emoji.name
        content1 = '以下の企画案に補足説明をしますか？\n' \
                   '補足説明を追加する場合は3分以内に' + good + 'のリアクションをしてください。\n' \
                   '補足を中止したい場合は' + bad + 'のリアクションをすると中止されます。'
        content2 = '企画案の補足説明を10分以内に記載して送信してください(画像も添付できます)\n' \
                   '補足を中止したい場合は「' + bad + '」の絵文字を送信すると中止されます。'
        exp = ''
        old_attachment_files = []
        new_attachment_files = []
        attachments = []
        message_id = reaction.message_id
        message = await BotClient.good_channel.fetch_message(message_id)
        await message.remove_reaction(emoji, reaction.member)
        for attachment in message.attachments:
            attachments.append(attachment)
            old_attachment_files.append(await attachment.to_file())
        embed = message.embeds[0]
        dm = await reaction.member.send(content=content2, embed=embed, files=old_attachment_files)
        await dm.add_reaction(good)
        await dm.add_reaction(bad)

        # 補足追加時のメッセージ待ち処理
        def add_explanation(msg):
            if not msg.author.bot \
                    and msg.channel.type == discord.ChannelType.private \
                    and msg.author.id == reaction.member.id:
                if msg.content == bad:
                    return asyncio.TimeoutError
                nonlocal exp, attachments
                exp = msg.content + ' by <@' + str(reaction.member.id) + '>'
                for attach in msg.attachments:
                    attachments.append(attach)
                return True

        try:
            await self.wait_for('raw_reaction_add', timeout=reaction_wait_time, check=check_explanation)
            await dm.delete()
            await self.wait_for('message', timeout=explanation_wait_time, check=add_explanation)
        except asyncio.TimeoutError:
            content = 'メッセージの補足をキャンセルしました'
        else:
            embed.insert_field_at(0, name='✏ 補足', value=exp, inline=False)
            for attachment in attachments:
                new_attachment_files.append(await attachment.to_file())
            content = '企画案の補足を追記しました👍'
            sent_message = await BotClient.good_channel.send(embed=embed, files=new_attachment_files)
            await sent_message.add_reaction(good)
            await sent_message.add_reaction(bad)
            await sent_message.add_reaction(info)
            await message.delete()
        await dm.delete()
        await reaction.member.send(content=content)


client = BotClient()
client.run(token)
