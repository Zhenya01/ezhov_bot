import asyncio
import datetime
import os
import pprint
import sys
import traceback
import random

import pytz
import twitchAPI
from telethon.errors import ChatNotModifiedError
from telethon.sync import TelegramClient
from telethon import functions

import regs
from telegram.ext import CommandHandler, MessageHandler, filters, \
    PicklePersistence, JobQueue, Defaults, ContextTypes, ApplicationBuilder
from telegram.constants import ParseMode
from telegram import Update, ChatPermissions
import twitchAPI_integration
import logging
import asyncio
from queue import Queue

import twitch_module
import chat_management_module
from regs import logger, application





async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug('STARTING')
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет. Я Жижов. Добро пожаловать!")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Кстааати, купи слона!")
    if 'phrases_list' not in context.bot_data.keys():
        context.bot_data['phrases_list'] = []


async def post_hello_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == 93906905:
        await context.bot.send_message(93906905, 'Отправил')
        text = 'Би - бо - бу - бип\n11010000 10101111 100000 11010000 10110001 11010000 10111110 11010001 10000010 100000 11010000 10010110 11010000 10111000 11010000 10110110 11010000 10111110 11010000 10110010'
        await context.bot.send_message(id=-1001684055869, text=text)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми, да и купи слона!')


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = \
f'''Карочи это вот ссылочки на всё что связано с моим ТВОРЧЕСТВОМ.
Подпишитесь пожалуйста на всё, этим вы меня очень поддержите:

Чаще всего стримлю на twitch:
twitch.tv/zdarovezhov
Общаемся все в ТГ: 
t.me/zdarovezhov



Нарезки со стримов в YouTube: 
vk.cc/cjveTL
легендарные моменты заливаем в YouTube Shorts: 
vk.cc/cjvf3v
Я в ТикТок:
vk.cc/cjvifP
из меня делают мемы в Yappi: 
vk.cc/cjveXZ'''
    await update.message.reply_text(text)


async def send_reboot_message():
    await application.bot.send_message(93906905, 'Бот перезагружен')
    pprint.pprint(f'LOGGER_DICT - {logging.root.manager.loggerDict}')


async def functions_to_run_at_the_beginning(_):
    await twitch_module.setup_twitch_objects()
    await twitch_module.subscribe_stream_online()
    await twitch_module.subscribe_stream_offline()
    await send_reboot_message()



print('Бот перезагружен')
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('add', twitch_module.add_phrase))
application.add_handler(CommandHandler('add_first', twitch_module.add_phrase_to_start))
application.add_handler(CommandHandler('show', twitch_module.show))
application.add_handler(CommandHandler('remove', twitch_module.remove_phrase))
application.add_handler(CommandHandler('silent', twitch_module.silent))
application.add_handler(CommandHandler('loud', twitch_module.loud))
application.add_handler(CommandHandler('mute', chat_management_module.mute, filters.REPLY))

application.add_handler(CommandHandler('info', info))
application.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,
                   chat_management_module.kick_from_group))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE,
                                       twitch_module.delete_channel_rename_message))
# application.add_handler(CommandHandler('post', post_hello_message))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
job_queue: JobQueue = application.job_queue
application.job_queue.run_custom(functions_to_run_at_the_beginning, job_kwargs={})
# async def main():
#     await application.initialize()
#     await application.start()
#     await application.updater.start_polling()
#     # Start other asyncio frameworks here
#     await application.bot.send_message(93906905, 'Бот перезагружен')
#     # Add some logic that keeps the event loop running until you want to shutdown
#     # Stop the other asyncio frameworks here
#     await application.updater.stop()
#     await application.stop()
#     await application.shutdown()
application.run_polling(close_loop=False)


#TODO добавить логи
#TODO тикток вечерок



