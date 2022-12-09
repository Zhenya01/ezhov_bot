import asyncio
import os
import sys
import traceback
import random
import datetime

import pytz
from telethon.errors import ChatNotModifiedError
from telethon.sync import TelegramClient
from telethon import functions

import regs
from telegram.ext import Updater, CallbackContext, CommandHandler, \
    MessageHandler, Filters, PicklePersistence, Dispatcher, ExtBot, JobQueue, \
    Defaults
from telegram import Update, Bot, ChatPermissions, ParseMode
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
    if 'stickers_counters' not in context.bot_data.keys():
        context.bot_data['stickers_counters'] = {}


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
        phrases_list = updater.dispatcher.bot_data['phrases_list']
        if len(phrases_list) == 0:
            phrase = 'Присоединяйтесь к моей трансляции Twitch!'
        else:
            phrase = updater.dispatcher.bot_data['phrases_list'][0]
            del updater.dispatcher.bot_data['phrases_list'][0]
        notification_text = f'{emoji} {phrase}'
        notification_text += '\ntwitch.tv/zdarovezhov'
        updater.dispatcher.bot.send_message(-1001879046742, notification_text)
    else:
        updater.dispatcher.bot_data['silent'] = True
    await rename_channel_zhenya(live=True)


async def post_stream_offline_notification_zhenya(data):
    await rename_channel_zhenya(live=False)


def mute(update: Update, context: CallbackContext):
    admins_list = regs.admins_list + regs.moders_list
    print('STARTING MUTE. CHECKING ADMINS')
    if update.message.from_user.id in admins_list:
        print('IS_ADMIN. MUTING')
        if len(context.args) == 0:
            duration = 30
        else:
            duration = int(context.args[0])
        mute_id = update.message.reply_to_message.from_user.id
        until_date = datetime.datetime.now() + datetime.timedelta(minutes=duration)
        permissions = ChatPermissions(can_send_messages=False)
        context.bot.restrict_chat_member(regs.zhenya_group_id, mute_id,
                                         permissions, until_date)
        asyncio.run(send_muted_message(update, context, duration))
    else:
        print('NOT_ADMIN. SKIPPING')


async def send_muted_message(update: Update, context: CallbackContext, duration):
    muted_user = update.message.reply_to_message.from_user
    muted_name = muted_user.name
    muted_username = muted_user.username
    muted_id = muted_user.id
    muted_mention = f"\@{muted_username}" \
        if (
            muted_username != 'None' and muted_username is not None) else f'[{muted_name}](tg://user?id={muted_id})'
    text = f'{muted_mention}, чел ты в муте на {duration} мин\. Заслужил\.'
    message_id = context.bot.send_message(update.effective_chat.id, text, parse_mode=ParseMode.MARKDOWN_V2).message_id
    await delete_muted_message(update, context, message_id)


async def delete_muted_message(update: Update, context: CallbackContext, message_id):
    await asyncio.sleep(300)
    context.bot.delete_message(update.effective_chat.id, message_id)
    update.effective_message.reply_text('Удалил сообщение')


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


def show_stickers_counters(update: Update, context: CallbackContext):
    if context.bot_data['stickers_counters'] == {}:
        update.message.reply_text('Нет записей')
    else:
        text = ''
        for user_name in context.bot_data['stickers_counters']:
            text += f'{user_name}: {context.bot_data["stickers_counters"][user_name]}\n'
        update.message.reply_text(text)


def clear_counters(update: Update, context: CallbackContext):
    context.bot_data["stickers_counters"] = {}

def sticker_handler(update: Update, context: CallbackContext):
    full_name = update.effective_user.full_name
    if full_name not in context.bot_data['stickers_counters'].keys():
        context.bot_data['stickers_counters'][full_name] = 1
    else:
        context.bot_data['stickers_counters'][full_name] += 1


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
        bot = Bot(token,
                  defaults=Defaults(tzinfo=pytz.timezone('Europe/Moscow')))
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
dispatcher.add_handler(CommandHandler('show_sticks', show_stickers_counters))
dispatcher.add_handler(CommandHandler('clear_counters', clear_counters))
dispatcher.add_handler(CommandHandler('remove', remove_phrase))
dispatcher.add_handler(CommandHandler('silent', silent))
dispatcher.add_handler(CommandHandler('loud', loud))
dispatcher.add_handler(CommandHandler('mute', mute, Filters.reply))
# dispatcher.add_handler(CommandHandler('post', post_hello_message))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
dispatcher.add_handler(MessageHandler(Filters.sticker, sticker_handler))
updater.start_polling()
# asyncio.run(main())
logger.debug('STARTING TO SUBSCRIBE TO STREAM ONLINE')
# subscribe_stream_online()
logger.debug('STARTING TO SUBSCRIBE TO STREAM OFFLINE')
# subscribe_stream_offline()
# twitchAPI_integration.webhook.listen_channel_subscribe(regs.ezhov_broadcaster_id, post_stream_notification)
updater.idle()
