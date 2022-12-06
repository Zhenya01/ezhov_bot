import asyncio
import os
import sys
import traceback
import random

from telethon.errors import ChatNotModifiedError
from telethon.sync import TelegramClient
from telethon import functions

import regs
from telegram.ext import Updater, CallbackContext, CommandHandler, \
    MessageHandler, Filters, PicklePersistence, Dispatcher, ExtBot, JobQueue
from telegram import Update, Bot
import twitchAPI_integration
import logging
import asyncio
from queue import Queue
from regs import logger


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет. Я Жижов. Добро пожаловать!")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Кстааати, купи слона!")
    if 'phrases_list' not in context.bot_data.keys():
        context.bot_data['phrases_list'] = []


def add_phrase(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text(
            'Укажите фразу после /add (Например: /add привет)')
    else:
        phrases = ' '.join(context.args).split(';')
        context.bot_data['phrases_list'] += phrases
        update.message.reply_text("Добавил")


def show(update: Update, context: CallbackContext):
    if context.bot_data['phrases_list'] != []:
        for phrase in context.bot_data['phrases_list']:
            update.message.reply_text(f"{context.bot_data['phrases_list'].index(phrase) + 1}: {phrase}")
    else:
        update.message.reply_text('В списке нет ни одной фразы используйте /add фраза')


def remove_phrase(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text('Укажите индекс фразы после /remove (Например: /remove 2)')
    else:
        index = context.args[0]
        try:
            int(index)
        except:
            update.message.reply_text('Укажите индекс фразы после /remove (Например: /remove 2)')
        index = int(index) - 1
        del context.bot_data['phrases_list'][index]
        update.message.reply_text('Удалил')


def echo(update: Update, context: CallbackContext):
    if update.effective_chat.type == 'private':
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми, да и купи слона!')


async def post_stream_live_notification_zhenya(data):
    if 'silent' not in updater.dispatcher.bot_data.keys() or updater.dispatcher.bot_data['silent'] is False:
        emoji = random.choice(regs.emoji_list)
        phrase = random.choice(updater.dispatcher.bot_data['phrases_list'])
        notification_text = f'{emoji} {phrase}'
        notification_text += '\ntwitch.tv/zdarovezhov'
        updater.dispatcher.bot.send_message(-1001684055869, notification_text)
    else:
        updater.dispatcher.bot_data['silent'] = True
    await rename_channel_zhenya(live=True)


async def post_stream_offline_notification_zhenya(data):
    await rename_channel_zhenya(live=False)


def mute(update: Update, context: CallbackContext):
    admins_list = regs.admins_list + [1255841663, 1149122366, 1238357873]
    if update.effective_user.id in admins_list:
        duration = context.args[0]
        mute_id = update.message.reply_to_message.from_user.id
        context.bot.restrict_chat_member()


async def rename_channel_zhenya(live: bool):
    title = '🔴 zdarovNeEzhov' if live else 'zdarovNeEzhov'
    try:
        async with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
            await client(functions.channels.EditTitleRequest(
                channel='ezhov_test',
                title=title)
                )
    except:
        pass


def silent(update: Update, context: CallbackContext):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = True
        update.message.reply_text('Следующий стрим пройдёт без уведомления')


def loud(update: Update, context: CallbackContext):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = False
        update.message.reply_text('Следующий стрим пройдёт c уведомлением')


class EzhovDispatcher(Dispatcher):
    def start(self, ready=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        super().start(ready)


class EzhovUpdater(Updater):
    def __init__(self, token):
        # con_pool_size = 4 + 4
        # request_kwargs = {"con_pool_size": con_pool_size}
        bot = Bot(token)
        persistence = PicklePersistence(
            filename=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence_zhenya')

        dispatcher = EzhovDispatcher(bot, update_queue=Queue(),
                                     job_queue=JobQueue(), persistence=persistence)

        super().__init__(dispatcher=dispatcher, workers=None)


async def subscribe_stream_online_zhenya():
    await twitchAPI_integration.webhook.listen_stream_online(
        regs.zhenya_broadcaster_id,
        callback=post_stream_live_notification_zhenya)


async def subscribe_stream_offline_zhenya():
    await twitchAPI_integration.webhook.listen_stream_offline(
        regs.zhenya_broadcaster_id,
        callback=post_stream_offline_notification_zhenya)


async def main():
    tasks = [subscribe_stream_online_zhenya(), subscribe_stream_offline_zhenya()]
    return asyncio.gather(*tasks)

updater = EzhovUpdater(regs.bot_token_zhenya)
updater.dispatcher.bot.send_message(93906905, 'Бот перезагружен')
print('Бот перезагружен')
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('add', add_phrase))
dispatcher.add_handler(CommandHandler('show', show))
dispatcher.add_handler(CommandHandler('remove', remove_phrase))
dispatcher.add_handler(CommandHandler('silent', silent))
dispatcher.add_handler(CommandHandler('loud', loud))
dispatcher.add_handler(CommandHandler('mute', mute, Filters.reply))
# dispatcher.add_handler(CommandHandler('post', post_hello_message))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
updater.start_polling()
asyncio.run(main())
logger.debug('STARTING TO SUBSCRIBE TO STREAM ONLINE')
# subscribe_stream_online()
logger.debug('STARTING TO SUBSCRIBE TO STREAM OFFLINE')
# subscribe_stream_offline()
# twitchAPI_integration.webhook.listen_channel_subscribe(regs.ezhov_broadcaster_id, post_stream_notification)
updater.idle()
