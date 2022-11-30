import asyncio
import os
import sys
import traceback
import random

from telethon.sync import TelegramClient
from telethon import functions, types

from twitchAPI import TwitchAPIException, UnauthorizedException, \
    TwitchAuthorizationException, TwitchBackendException

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


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми, да и купи слона!')


async def post_stream_live_notification(data):
    emoji = random.choice(regs.emoji_list)
    notification_text = f'{emoji} Заходи пожалуйста я играть буду в компунтер'
    notification_text += '\ntwitch.tv/zdarovezhov'
    updater.dispatcher.bot.send_message(-1001879046742, notification_text)
    await rename_channel(live=True)


async def post_stream_offline_notification(data):
    await rename_channel(live=False)


async def rename_channel(live: bool):
    title = '🔴 ZdarovNeEzhov' if live else 'ZdarovNeEzhov'
    async with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
        print('renaming channel_name')
        result = client(functions.channels.EditTitleRequest(
            channel='ezhov_test',
            title=title)
            )
        print(result.stringify()
        )


class EzhovDispatcher(Dispatcher):
    def start(self, ready=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        super().start(ready)


class EzhovUpdater(Updater):
    def __init__(self, token):
        con_pool_size = 4 + 4
        request_kwargs = {"con_pool_size": con_pool_size}
        bot = Bot(token)
        bot_persistence = PicklePersistence(filename=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')

        self.dispatcher = EzhovDispatcher(bot, update_queue=Queue(),
                                     job_queue=JobQueue(),
                                     persistence=bot_persistence)

        super().__init__(token)


updater = EzhovUpdater(regs.bot_token)
updater.dispatcher.bot.send_message(93906905, 'Бот перезагружен')
print('Бот перезагружен')
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
# dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
updater.start_polling()
twitchAPI_integration.webhook.listen_stream_online(regs.zhenya_broadcaster_id,
                             callback=post_stream_live_notification)
twitchAPI_integration.webhook.listen_stream_offline(regs.zhenya_broadcaster_id,
                             callback=post_stream_offline_notification)
# twitchAPI_integration.webhook.listen_channel_subscribe(regs.ezhov_broadcaster_id, post_stream_notification)
updater.idle()
