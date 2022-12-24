import asyncio
import datetime
import os
import sys
import traceback
import random

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
        phrases_list = updater.dispatcher.bot_data['phrases_list']
        if len(phrases_list) == 0:
            phrase = 'Присоединяйтесь к моей трансляции Twitch!'
        else:
            phrase = updater.dispatcher.bot_data['phrases_list'][0]
            del updater.dispatcher.bot_data['phrases_list'][0]
        notification_text = f'{emoji} {phrase}'
        notification_text += '\ntwitch.tv/zdarovezhov'
        updater.dispatcher.bot.send_message(regs.zdarovezhov_channel_id, notification_text)
    else:
        updater.dispatcher.bot_data['silent'] = True
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


def rename_channel_joke(update: Update, context: CallbackContext):
    title = 'loh'
    if update.effective_user.id == 93906905:
        try:
            with TelegramClient('ezhovApp', regs.telegram_app_api_id, regs.telegram_app_api_hash) as client:
                client(functions.channels.EditTitleRequest(
                    channel='ezhov_test',
                    title=title)
                    )
        except:
            pass


def silent(update: Update, context: CallbackContext):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = True
        update.message.reply_text('Следующий стрим пройдёт без уведомления')


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
        until_date = datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')) + datetime.timedelta(minutes=duration)
        permissions = ChatPermissions(can_send_messages=False)
        context.bot.restrict_chat_member(update.effective_chat.id, mute_id,
                                         permissions, until_date)
        muted_message_id = update.message.reply_to_message.message_id
        muter_message_id = update.message.message_id
        context.bot.delete_message(update.effective_chat.id, muted_message_id)
        context.bot.delete_message(update.effective_chat.id, muter_message_id)
        send_muted_message(update, context, duration)
    else:
        update.message.delete()


def send_muted_message(update: Update, context: CallbackContext, duration):
    muted_user = update.message.reply_to_message.from_user
    muted_name = muted_user.name
    muted_username = muted_user.username
    muted_id = muted_user.id
    muted_mention = f"\@{muted_username}" \
        if (
            muted_username != 'None' and muted_username is not None) else f'[{muted_name}](tg://user?id={muted_id})'
    muted_mention = reformat_name(muted_mention)
    text = f'{muted_mention}, чел ты в муте на {duration} мин\. Заслужил\.\nЗамутил: {reformat_name(update.effective_user.name)}'
    message_id = context.bot.send_message(update.effective_chat.id, text, parse_mode=ParseMode.MARKDOWN_V2).message_id
    asyncio.run(delete_muted_message(update, context, message_id))


async def delete_muted_message(update: Update, context: CallbackContext, message_id):
    await asyncio.sleep(60)
    context.bot.delete_message(update.effective_chat.id, message_id)


def loud(update: Update, context: CallbackContext):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = False
        update.message.reply_text('Следующий стрим пройдёт c уведомлением')


def reformat_name(name:str):
    replacement_dict = {'_': '\_', '*': '\*', '[': '\[', ']': '\]', '(': '\(',
                    ')': '\)', '~': '\~', '`': '\`', '>': '\>', '#': '\#',
                    '+': '\+', '-': '\-', '=': '\=', '|': '\|', '{': '\{',
                    '}': '\}', '.': '\.', '!': '\!'}
    for i, j in replacement_dict.items():
        name = name.replace(i, j)
    return name


def kick_from_group(update: Update, context: CallbackContext):
    path = f'{os.path.abspath(os.path.dirname(__file__))}\\uhodi.png'
    message_id = update.message.reply_photo(open(path, 'rb'), 'Этот чат не чат, тут Eжов за сообщениями в группе следит').message_id
    # message_id = update.message.reply_text('Этот чат не чат, тут ежов за сообщениями в группе следит').message_id
    asyncio.run(kick_after_wait(update, context, message_id))


async def kick_after_wait(update: Update, context: CallbackContext, message_id):
    await asyncio.sleep(15)
    context.bot.unban_chat_member(update.effective_chat.id, update.effective_user.id)
    context.bot.delete_message(update.effective_chat.id, message_id)


def delete_chat_rename_message(update: Update, context: CallbackContext):
    update.effective_message.delete()

def info(update: Update, context: CallbackContext):
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
    update.message.reply_text(text)
class EzhovDispatcher(Dispatcher):
    def start(self, ready=None):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        super().start(ready)


class EzhovUpdater(Updater):
    def __init__(self, token):
        # con_pool_size = 4 + 4
        # request_kwargs = {"con_pool_size": con_pool_size}
        bot = ExtBot(token, defaults=Defaults(tzinfo=pytz.timezone('Europe/Moscow'),
                                              run_async=True))
        persistence = PicklePersistence(
            filename=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')

        dispatcher = EzhovDispatcher(bot, update_queue=Queue(),
                                     job_queue=JobQueue(), persistence=persistence)

        super().__init__(dispatcher=dispatcher, workers=None)


async def subscribe_stream_online():
    await twitchAPI_integration.webhook.listen_stream_online(
        regs.ezhov_broadcaster_id,
        callback=post_stream_live_notification)


async def subscribe_stream_offline():
    await twitchAPI_integration.webhook.listen_stream_offline(
        regs.ezhov_broadcaster_id,
        callback=post_stream_offline_notification)


async def main():
    tasks = [subscribe_stream_online(), subscribe_stream_offline()]
    return asyncio.gather(*tasks)


if __name__ == 'main':
    updater = EzhovUpdater(regs.bot_token_main)
    updater.dispatcher.bot.send_message(93906905, 'Бот перезагружен')
    print('Бот перезагружен')
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('add', add_phrase))
    dispatcher.add_handler(CommandHandler('show', show))
    dispatcher.add_handler(CommandHandler('remove', remove_phrase))
    dispatcher.add_handler(CommandHandler('silent', silent))
    dispatcher.add_handler(CommandHandler('loud', loud))
    dispatcher.add_handler(CommandHandler('joke', rename_channel_joke,
                                          run_async=True))
    dispatcher.add_handler(CommandHandler('mute', mute, Filters.reply,
                                          run_async=True))
    dispatcher.add_handler(CommandHandler('info', info))
    dispatcher.add_handler(
        MessageHandler(Filters.status_update.new_chat_members, kick_from_group,
                       run_async=True))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_title,
                                          delete_chat_rename_message,
                                          run_async=True))
    # dispatcher.add_handler(CommandHandler('post', post_hello_message))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    updater.start_polling()
    # asyncio.run(main())
    logger.debug('STARTING TO SUBSCRIBE TO STREAM ONLINE')
    # subscribe_stream_online()
    logger.debug('STARTING TO SUBSCRIBE TO STREAM OFFLINE')
    # subscribe_stream_offline()
    # twitchAPI_integration.webhook.listen_channel_subscribe(regs.ezhov_broadcaster_id, post_stream_notification)
    updater.idle()
