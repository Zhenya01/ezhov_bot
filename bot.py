import asyncio
import os
import sys
import traceback

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


async def post_stream_notification(data):
    try:
        res = twitchAPI_integration.twitch.get_channel_information(regs.zhenya_broadcaster_id)
    except (TwitchAPIException, UnauthorizedException,
            TwitchAuthorizationException, TwitchBackendException) as err:
        logger.error(f"APP] {regs.zhenya_broadcaster_id} get stream_info failed with error {type(err).__name__}: '{err}'")
        return None, None
    game = res["data"][0]["game_name"]
    title = res["data"][0]["title"]
    logger.info((f"APP] Broadcaster Zhenya_2001: game: {game}, title: '{title}'"))
    twitchAPI_integration.twitch.get_channel_information(regs.zhenya_broadcaster_id)
    notification_text = f'🔴🔴🔴 Cтремлер запустил поток: "{title}"'
    if game:
        notification_text += f'\nСегодня играем в "{game}"'
    notification_text += '\nЛови ссылкочку и забегай скорее: https://www.twitch.tv/zhenya_2001'
    updater.dispatcher.bot.send_message(-1001879046742, notification_text)


def rename_channel():
    with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
        print('renaming channel_name')
        result = client(functions.channels.EditTitleRequest(
            channel='ezhov_test',
            title='ZdarovNeEzhov')
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
# updater.start_polling()
# twitchAPI_integration.webhook.listen_stream_online(regs.zhenya_broadcaster_id,
#                              callback=post_stream_notification)
# twitchAPI_integration.webhook.listen_channel_subscribe(regs.ezhov_broadcaster_id, post_stream_notification)
# updater.idle()
