import asyncio
import os
import sys
import traceback

import regs
from telegram.ext import Updater, CallbackContext, CommandHandler, \
    MessageHandler, Filters, PicklePersistence, Dispatcher
from telegram import Update
import twitchAPI_integration
import logging
import asyncio


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет. Я Жижов. Добро пожаловать!")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Кстааати, купи слона!")


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми, да и купи слона!')


async def post_stream_notification(data):
    await updater.dispatcher.bot.send_message(93906905, f'Стрим начался\ndata - {data}')


bot_persistence = PicklePersistence(filename=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')
updater = Updater(token=regs.bot_token,
                  persistence=bot_persistence)
updater.dispatcher.bot.send_message(93906905, 'Бот перезагружен')
print('Бот перезагружен')
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
# dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
updater.start_polling()
twitchAPI_integration.webhook.listen_stream_online(regs.zhenya_broadcaster_id,
                             callback=post_stream_notification)
# twitchAPI_integration.webhook.listen_channel_subscribe(regs.ezhov_broadcaster_id, post_stream_notification)
updater.idle()