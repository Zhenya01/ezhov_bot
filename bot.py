import asyncio
import datetime
import os
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
from regs import logger

twitch = None
webhook = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет. Я Жижов. Добро пожаловать!")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Кстааати, купи слона!")
    if 'phrases_list' not in context.bot_data.keys():
        context.bot_data['phrases_list'] = []


async def add_phrase_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            'Укажите фразу после /add_first (Например: /add_first привет)')
    else:
        phrases = ' '.join(context.args).split(';')
        context.bot_data['phrases_list'] = phrases + context.bot_data['phrases_list']
        await update.message.reply_text("Добавил")


async def add_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            'Укажите фразу после /add (Например: /add привет)')
    else:
        phrases = ' '.join(context.args).split(';')
        context.bot_data['phrases_list'] += phrases
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


async def post_hello_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == 93906905:
        await context.bot.send_message(93906905, 'Отправил')
        text = 'Би - бо - бу - бип\n11010000 10101111 100000 11010000 10110001 11010000 10111110 11010001 10000010 100000 11010000 10010110 11010000 10111000 11010000 10110110 11010000 10111110 11010000 10110010'
        await context.bot.send_message(id=-1001684055869, text=text)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми, да и купи слона!')


async def post_stream_live_notification(data):
    if 'silent' not in application.bot_data.keys() or application.bot_data['silent'] is False:
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


async def silent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = True
        await update.message.reply_text('Следующий стрим пройдёт без уведомления')


async def loud(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in regs.admins_list:
        context.bot_data['silent'] = False
        await update.message.reply_text('Следующий стрим пройдёт c уведомлением')



async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await context.bot.restrict_chat_member(update.effective_chat.id, mute_id,
                                         permissions, until_date)
        muted_message_id = update.message.reply_to_message.message_id
        await context.bot.delete_message(update.effective_chat.id, muted_message_id)
        muter_message_id = update.message.message_id
        await context.bot.delete_message(update.effective_chat.id, muter_message_id)
        await send_muted_message(update, context, duration)
    else:
        await update.message.delete()


async def send_muted_message(update: Update, context: ContextTypes.DEFAULT_TYPE, duration):
    muted_user = update.message.reply_to_message.from_user
    muted_name = muted_user.name
    muted_username = muted_user.username
    muted_id = muted_user.id
    muted_mention = f"\@{muted_username}" \
        if (
            muted_username != 'None' and muted_username is not None) else f'[{muted_name}](tg://user?id={muted_id})'
    muted_mention = reformat_name(muted_mention)
    text = f'{muted_mention}, чел ты в муте на {duration} мин\. Заслужил\.\nЗамутил: {reformat_name(update.effective_user.name)}'
    print(text)
    message = await context.bot.send_message(update.effective_chat.id, text, parse_mode=ParseMode.MARKDOWN_V2)
    message_id = message.message_id
    context.application.job_queue.run_once(callback=delete_muted_message,
                                           when=60,
                                           data={'chat_id': update.effective_chat.id,
                                                 'message_id': message_id})


async def delete_muted_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data['chat_id']
    message_id = context.job.data['message_id']
    await context.bot.delete_message(chat_id, message_id)


def reformat_name(name:str):
    replacement_dict = {'_': '\_', '*': '\*', '[': '\[', ']': '\]', '(': '\(',
                    ')': '\)', '~': '\~', '`': '\`', '>': '\>', '#': '\#',
                    '+': '\+', '-': '\-', '=': '\=', '|': '\|', '{': '\{',
                    '}': '\}', '.': '\.', '!': '\!'}
    for i, j in replacement_dict.items():
        name = name.replace(i, j)
    return name


async def kick_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('KICK_FROM_GROUP')
    if update.effective_chat.id in [regs.zdarovezhov_group_id, regs.zhenya_group_id]:
        print('KICK_FROM_GROUP_START')
        if update.effective_user.id not in regs.group_list:
            message = await update.message.reply_photo(open('uhodi.png', 'rb'), 'Этот чат не чат, тут Eжов за сообщениями в группе следит')
            message_id = message.message_id
            # message_id = await update.message.reply_text('Этот чат не чат, тут ежов за сообщениями в группе следит').message_id
            context.bot_data['user_to_kick'] = update.message.from_user.id
            context.bot_data['chat_to_kick_from'] = update.message.chat.id
            context.application.job_queue.run_once(callback=kick_after_wait,
                                                   when=datetime.timedelta(seconds=10),
                                                   name='kick_after_wait',
                                                   data={'user_to_kick': update.message.from_user.id,
                                                         'chat_to_kick_from': update.message.chat.id,
                                                         'message_to_delete': message_id})


async def kick_after_wait(context: ContextTypes.DEFAULT_TYPE):
    # await asyncio.sleep(15)
    chat_id = context.job.data['chat_to_kick_from']
    user_id = context.job.data['user_to_kick']
    message_id = context.job.data['message_to_delete']
    await context.bot.unban_chat_member(chat_id, user_id)
    await context.bot.delete_message(chat_id, message_id)


async def delete_chat_rename_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.delete()


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
# class EzhovDispatcher(Dispatcher):
#     def start(self, ready=None):
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         super().start(ready)

#
# class EzhovUpdater(Updater):
#     def __init__(self, token):
#         # con_pool_size = 4 + 4
#         # request_kwargs = {"con_pool_size": con_pool_size}
#         bot = ExtBot(token, defaults=Defaults(tzinfo=pytz.timezone('Europe/Moscow'),
#                                               run_async=True))
#         persistence = PicklePersistence(
#             filename=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')
#
#         application = EzhovDispatcher(bot, update_queue=Queue(),
#                                      job_queue=JobQueue(), persistence=persistence)
#
#         super().__init__(application=application, workers=None)


async def subscribe_stream_online():
    print(webhook)
    await webhook.listen_stream_online(
        regs.ezhov_broadcaster_id,
        callback=post_stream_live_notification)


async def subscribe_stream_offline():
    global webhook
    await webhook.listen_stream_offline(
        regs.ezhov_broadcaster_id,
        callback=post_stream_offline_notification)


async def send_reboot_message():
    await application.bot.send_message(93906905, 'Бот перезагружен')


async def main(_):
    await setup_twitch_objects()
    await subscribe_stream_online()
    await subscribe_stream_offline()
    await send_reboot_message()


async def setup_twitch_objects():
    global twitch, webhook
    twitch = twitchAPI_integration.setup_twitch()
    await twitch.authenticate_app([])
    print('setting up webhook')
    webhook = await twitchAPI_integration.setup_subscribe_webhook(twitch)


defaults=Defaults(tzinfo=pytz.timezone('Europe/Moscow'))
persistence = PicklePersistence(filepath=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')
token=regs.bot_token_main

application = ApplicationBuilder().token(token).persistence(persistence).defaults(defaults).build()
print('Бот перезагружен')
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('add', add_phrase))
application.add_handler(CommandHandler('add_first', add_phrase_to_start))
application.add_handler(CommandHandler('show', show))
application.add_handler(CommandHandler('remove', remove_phrase))
application.add_handler(CommandHandler('silent', silent))
application.add_handler(CommandHandler('loud', loud))
application.add_handler(CommandHandler('mute', mute, filters.REPLY))

application.add_handler(CommandHandler('info', info))
application.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, kick_from_group))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE,
                                      delete_chat_rename_message))
# application.add_handler(CommandHandler('post', post_hello_message))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
job_queue: JobQueue = application.job_queue
application.job_queue.run_custom(main, job_kwargs={})
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




# asyncio.run(main())
# application.create_task(main())
