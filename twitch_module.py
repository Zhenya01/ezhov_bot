import random

import twitchAPI
from telegram import Update
from telegram.ext import ContextTypes
from telethon import TelegramClient, functions

import regs
import twitchAPI_integration
import zhenya_test
from bot import application
from regs import logger

twitch: twitchAPI.twitch = None
webhook: twitchAPI.eventsub = None


async def setup_twitch_objects():
    global twitch, webhook
    twitch = twitchAPI_integration.setup_twitch()
    await twitch.authenticate_app([])
    print('setting up webhook')
    webhook = await twitchAPI_integration.setup_subscribe_webhook(twitch)


async def subscribe_stream_online():
    print(webhook)
    await webhook.listen_stream_online(
        regs.ezhov_broadcaster_id,
        callback=post_stream_live_notification)
    await webhook.listen_stream_online(
        regs.zhenya_broadcaster_id,
        callback=zhenya_test.post_stream_live_notification)


async def subscribe_stream_offline():
    global webhook
    await webhook.listen_stream_offline(
        regs.ezhov_broadcaster_id,
        callback=post_stream_offline_notification)
    await webhook.listen_stream_offline(
        regs.zhenya_broadcaster_id,
        callback=zhenya_test.post_stream_offline_notification)


async def post_stream_live_notification(data):
    logger.info('Streamer is online. Changing information')
    logger.debug(f'Twitch data - {data}')
    if 'silent' not in application.bot_data.keys() or application.bot_data['silent'] is False:
        logger.info('Loudness is set to "loud". Posting notification')
        emoji = random.choice(regs.emoji_list)
        phrases_list = application.bot_data['phrases_list']
        if len(phrases_list) == 0:
            phrase = 'Присоединяйтесь к моей трансляции Twitch!'
        else:
            phrase = application.bot_data['phrases_list'][0]
            del application.bot_data['phrases_list'][0]
        notification_text = f'{emoji} {phrase}'
        notification_text += '\ntwitch.tv/zdarovezhov'
        await application.bot.send_message(regs.zdarovezhov_channel_id, notification_text)
    else:
        logger.info('Loudness is set to "silent". Setting loudness to "loud"')
        application.bot_data['silent'] = False
    await rename_channel(live=True)


async def post_stream_offline_notification(data):
    await rename_channel(live=False)


async def rename_channel(live: bool):
    title = '🔴 zdarovezhov' if live else 'zdarovezhov'
    try:
        async with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='zdarovezhov',
                title=title)
                )
    except:
        pass


async def delete_channel_rename_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.delete()


async def silent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = True
        await update.message.reply_text('Следующий стрим пройдёт без уведомления')


async def loud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = False
        await update.message.reply_text('Следующий стрим пройдёт c уведомлением')


async def loudness(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Следующий стрим пройдёт'
                                    + f' c уведомлением' if context.bot_data['silent'] == False
                                    else ' без уведомления')


async def add_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            'Укажите фразу после /add (Например: /add привет)')
    else:
        phrases = ' '.join(context.args).split(';')
        context.bot_data['phrases_list'] += phrases
        await update.message.reply_text("Добавил")


async def add_phrase_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            'Укажите фразу после /add_first (Например: /add_first привет)')
    else:
        phrases = ' '.join(context.args).split(';')
        context.bot_data['phrases_list'] = phrases + context.bot_data['phrases_list']
        await update.message.reply_text("Добавил")


async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.bot_data['phrases_list'] != []:
        for phrase in context.bot_data['phrases_list']:
            await update.message.reply_text(f"{context.bot_data['phrases_list'].index(phrase) + 1}: {phrase}")
    else:
        await update.message.reply_text('В списке нет ни одной фразы используйте /add фраза')


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