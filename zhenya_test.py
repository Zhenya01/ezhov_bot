import asyncio
import random

from telethon import TelegramClient, functions

import info_messages
import regs
from cfg_1 import logger, application


async def post_stream_live_notification(data):
    info_messages.info('Streamer is online. Changing information')
    logger.debug(f'Twitch data - {data}')
    if 'silent' not in application.bot_data.keys() or application.bot_data['silent'] is False:
        info_messages.info('Loudness is set to "loud". Posting notification')
        emoji = random.choice(regs.emoji_list)
        phrases_list = application.bot_data['phrases_list']
        if len(phrases_list) == 0:
            phrase = 'Присоединяйтесь к моей трансляции Twitch!'
        else:
            phrase = application.bot_data['phrases_list'][0]
            del application.bot_data['phrases_list'][0]
        notification_text = f'{emoji} {phrase}'
        notification_text += '\ntwitch.tv/zdarovezhov'
        threads = ['posts', 'comments']
        for thread in threads:
            await application.bot.send_message(regs.zhenya_forum_id,
                                               notification_text,
                                               message_thread_id=regs.zhenya_forum_threads[thread])
            await asyncio.sleep(5)
        await asyncio.sleep(5)
        msg = await application.bot.send_message(regs.zhenya_channel_id, notification_text)
        application.bot_data['searching_for_post'] = True
        application.bot_data['post_message_text'] = msg.text
    else:
        info_messages.info('Loudness was set to "silent". Setting loudness to "loud"')
        application.bot_data['silent'] = False
    await rename_channel(live=True)


async def post_stream_offline_notification(data):
    await rename_channel(live=False)


async def rename_channel(live: bool):
    title = '🔴 zdarovNeEzhov' if live else 'zdarovNeEzhov'
    try:
        async with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='ezhov_test',
                title=title)
                )
    except:
        pass
    await asyncio.sleep(10)
    title = '🔴 NeEzhovForum' if live else 'NeEzhovForum'
    try:
        async with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='ezhov_test_chat',
                title=title)
            )
    except:
        pass
