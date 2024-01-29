import asyncio
import random

import twitchAPI
from twitchAPI.twitch import Twitch
from twitchAPI.eventsub import webhook as webhook_
from twitchAPI.object import eventsub as eventsub_object
from twitchAPI.oauth import AuthScope
from telegram import Update
from telegram.ext import ContextTypes
from telethon import TelegramClient, functions

import cfg
import info_messages
from database import update_user_info


import twitchAPI_integration
import zhenya_test
from cfg import application
from logging_settings import logger

app_twitch: Twitch
app_webhook: webhook_.EventSubWebhook

MAIN_BROADCASTER_ID = cfg.config_data['TWITCH_NOTIFICATIONS']['MAIN_BROADCASTER_ID']
TEST_BROADCASTER_ID = cfg.config_data['TWITCH_NOTIFICATIONS']['TEST_BROADCASTER_ID']


async def setup_twitch_objects():
    global app_twitch, app_webhook
    app_twitch = twitchAPI_integration.setup_twitch()
    await app_twitch.authenticate_app([])
    print('setting up webhook')
    app_webhook = await twitchAPI_integration.setup_subscribe_webhook(app_twitch)


async def subscribe_stream_online():
    global app_webhook
    await app_webhook.listen_stream_online(
        MAIN_BROADCASTER_ID,
        callback=post_stream_live_notification)
    await app_webhook.listen_stream_online(
        TEST_BROADCASTER_ID,
        callback=zhenya_test.post_stream_live_notification)


async def subscribe_stream_offline():
    global app_webhook
    await app_webhook.listen_stream_offline(
        MAIN_BROADCASTER_ID,
        callback=post_stream_offline_notification)
    await app_webhook.listen_stream_offline(
        TEST_BROADCASTER_ID,
        callback=zhenya_test.post_stream_offline_notification)


async def subscribe_reward_redemption():
    global app_webhook
    await app_twitch.authenticate_app([AuthScope.CHANNEL_READ_REDEMPTIONS])
    await app_webhook.listen_channel_points_custom_reward_redemption_add(MAIN_BROADCASTER_ID,
                                                                         add_points_from_twitch_reward)


async def get_user_id_by_name(username):
    user = await app_twitch.get_users(logins=[username]).__anext__()
    print(f'user - {user}')


async def add_points_from_twitch_reward(data: eventsub_object.ChannelPointsCustomRewardRedemptionAddEvent):
    logger.info('User bought twitch reward for tg_points')
    application.bot.send_message(cfg.TEST_STREAMER_USER_ID,
                                 'Куплена награда')
    logger.info(f'CHANNEL REWARD DATA - {data}')

async def post_stream_live_notification(data):
    logger.info('Streamer is online. Changing information')
    logger.debug(f'Twitch data - {data}')
    if 'silent' not in application.bot_data.keys() or application.bot_data['silent'] is False:
        logger.info('Loudness is set to "loud". Posting notification')
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
            await application.bot.send_message(cfg.FORUM_ID, notification_text,
                                               message_thread_id=cfg.config_data['CHATS']['FORUM_THREADS'][thread])
            await asyncio.sleep(5)
        msg = await application.bot.send_message(cfg.CHANNEL_ID, notification_text)
        application.bot_data['searching_for_post'] = True
        application.bot_data['post_message_text'] = msg.text
    else:
        logger.info('Loudness is set to "silent". Setting loudness to "loud"')
        application.bot_data['silent'] = False
    await rename_channel(live=True)


async def post_stream_offline_notification(data):
    await rename_channel(live=False)


async def rename_channel(live: bool):
    telegram_app_api_id = cfg.config_data['KEYS']['TELEGRAM_APP_API_ID']
    telegram_app_api_hash = cfg.config_data['KEYS']['TELEGRAM_APP_API_HASH']
    title = '🔴 zdarovezhov камунити' if live else 'zdarovezhov камунити'
    try:
        async with TelegramClient('ezhovApp', telegram_app_api_id, telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='zdarovezhov_cummunity',
                title=title)
                )
    except:
        pass
    await asyncio.sleep(5)
    title = '🔴 zdarovezhov' if live else 'zdarovezhov'
    try:
        async with TelegramClient('ezhovApp', telegram_app_api_id, telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='zdarovezhov',
                title=title)
            )
    except:
        pass

ADMINS_LIST = cfg.config_data['CHATS']['ADMINS_LIST']

@update_user_info
async def silent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMINS_LIST:
        context.bot_data['silent'] = True
        await update.message.reply_text('Следующий стрим пройдёт без уведомления')


@update_user_info
async def loud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMINS_LIST:
        context.bot_data['silent'] = False
        await update.message.reply_text('Следующий стрим пройдёт c уведомлением')


@update_user_info
async def loudness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Следующий стрим пройдёт'
                                    + f' c уведомлением' if context.bot_data['silent'] == False
                                    else ' без уведомления')


@update_user_info
async def add_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            'Укажите фразу после /add (Например: /add привет)')
    else:
        phrases = ' '.join(context.args).split(';')
        context.bot_data['phrases_list'] += phrases
        await update.message.reply_text("Добавил")


@update_user_info
async def add_phrase_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            'Укажите фразу после /add_first (Например: /add_first привет)')
    else:
        phrases = ' '.join(context.args).split(';')
        context.bot_data['phrases_list'] = phrases + context.bot_data['phrases_list']
        await update.message.reply_text("Добавил")


@update_user_info
async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.bot_data['phrases_list'] != []:
        for phrase in context.bot_data['phrases_list']:
            await update.message.reply_text(f"{context.bot_data['phrases_list'].index(phrase) + 1}: {phrase}")
    else:
        await update.message.reply_text('В списке нет ни одной фразы используйте /add фраза')


@update_user_info
async def remove_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text('Укажите индекс фразы после /remove (Например: /remove 2)')
    else:
        index = context.args[0]
        try:
            int(index)
        except:
            await update.message.reply_text('Укажите индекс фразы после /remove (Например: /remove 2)')
        index = int(index) - 1
        del context.bot_data['phrases_list'][index]
        await update.message.reply_text('Удалил')

