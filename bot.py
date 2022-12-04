import asyncio
import os
import sys
import traceback
import random

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


def post_hello_message(update: Update, context: CallbackContext):
    if update.effective_user.id == 93906905:
        context.bot.send_message(93906905, 'Отправил')
        text = 'Би - бо - бу - бип\n11010000 10101111 100000 11010000 10110001 11010000 10111110 11010001 10000010 100000 11010000 10010110 11010000 10111000 11010000 10110110 11010000 10111110 11010000 10110010'
        context.bot.send_message(id=-1001684055869, text=text)


def echo(update: Update, context: CallbackContext):
    if update.effective_chat.type == 'private':
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми, да и купи слона!')


async def post_stream_live_notification(data):
    if 'silent' not in updater.dispatcher.bot_data.keys() or updater.dispatcher.bot_data['silent'] is False:
        emoji = random.choice(regs.emoji_list)
        phrase = random.choice(updater.dispatcher.bot_data['phrases_list'])
        notification_text = f'{emoji} {phrase}'
        notification_text += '\ntwitch.tv/zdarovezhov'
        updater.dispatcher.bot.send_message(-1001684055869, notification_text)
    else:
        updater.dispatcher.bot_data['silent'] = True
    await rename_channel(live=True)


async def post_stream_offline_notification(data):
    await rename_channel(live=False)


async def rename_channel(live: bool):
    title = '🔴 zdarovezhov' if live else 'zdarovezhov'
    async with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
        await client(functions.channels.EditTitleRequest(
            channel='zdarovezhov',
            title=title)
            )


def silent(update: Update, context: CallbackContext):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = True
        update.message.reply_text('Следующий стрим пройдёт без уведомления')
        context.bot.restrict_chat_member()


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
            filename=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')

        dispatcher = EzhovDispatcher(bot, update_queue=Queue(),
                                     job_queue=JobQueue(), persistence=persistence)

        super().__init__(dispatcher=dispatcher, workers=None)

updater = EzhovUpdater(regs.bot_token)
updater.dispatcher.bot.send_message(93906905, 'Бот перезагружен')
print('Бот перезагружен')
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('add', add_phrase))
dispatcher.add_handler(CommandHandler('show', show))
dispatcher.add_handler(CommandHandler('remove', remove_phrase))
dispatcher.add_handler(CommandHandler('silent', silent))
dispatcher.add_handler(CommandHandler('loud', loud))
# dispatcher.add_handler(CommandHandler('post', post_hello_message))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
updater.start_polling()
twitchAPI_integration.webhook.listen_stream_online(
        regs.ezhov_broadcaster_id,
        callback=post_stream_live_notification)

twitchAPI_integration.webhook.listen_stream_offline(
        regs.ezhov_broadcaster_id,
        callback=post_stream_offline_notification)
subscribe_stream_offline()
logger.debug('STARTING TO SUBSCRIBE TO STREAM ONLINE')
# subscribe_stream_online()
logger.debug('STARTING TO SUBSCRIBE TO STREAM OFFLINE')
# subscribe_stream_offline()
# twitchAPI_integration.webhook.listen_channel_subscribe(regs.ezhov_broadcaster_id, post_stream_notification)
updater.idle()
