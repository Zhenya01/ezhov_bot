import asyncio
import random

import yaml
from telethon import TelegramClient, functions

import cfg
import info_messages

from logging_settings import logger
from cfg import application

with open('config_test.yaml', "r") as yamlfile:
    test_config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)


async def post_stream_live_notification(data):
    forum_threads = test_config_data['CHATS']['FORUM_THREADS']
    forum_id = test_config_data['CHATS']['FORUM_GROUP']
    channel_id = test_config_data['CHATS']['CHANNEL_ID']
    info_messages.info('Streamer is online. Changing information')
    logger.debug(f'Twitch data - {data}')
    if 'silent' not in application.bot_data.keys() or application.bot_data['silent'] is False:
        info_messages.info('Loudness is set to "loud". Posting notification')
        emoji = random.choice(cfg.config_data['TWITCH_NOTIFICATIONS']['EMOJI_LIST'])
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
            await application.bot.send_message(forum_id,
                                               notification_text,
                                               message_thread_id=forum_threads[thread])
            await asyncio.sleep(5)
        await asyncio.sleep(5)
        msg = await application.bot.send_message(channel_id, notification_text)
        application.bot_data['searching_for_post'] = True
        application.bot_data['post_message_text'] = msg.text
    else:
        info_messages.info('Loudness was set to "silent". Setting loudness to "loud"')
        application.bot_data['silent'] = False
    logger.info('Requesting to rename channel')
    await rename_channel(live=True)


async def post_stream_offline_notification(data):
    logger.info('Requesting to rename channel')
    await rename_channel(live=False)


async def rename_channel(live: bool):
    logger.info('Renaming channel')
    telegram_app_api_id = test_config_data['KEYS']['TELEGRAM_APP_API_ID']
    telegram_app_api_hash = test_config_data['KEYS']['TELEGRAM_APP_API_HASH']
    title = '🔴 zdarovNeEzhov' if live else 'zdarovNeEzhov'
    try:
        async with TelegramClient('ezhovApp', telegram_app_api_id, telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='ezhov_test',
                title=title)
                )
    except:
        pass
    await asyncio.sleep(10)
    title = '🔴 NeEzhovForum' if live else 'NeEzhovForum'
    try:
        async with TelegramClient('ezhovApp', telegram_app_api_id, telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='ezhov_test_chat',
                title=title)
            )
    except:
        pass
