import pprint
from telegram.ext import CommandHandler, MessageHandler, filters, JobQueue, \
    ContextTypes, ConversationHandler, CallbackQueryHandler
from telegram import Update
import logging

import regs
import tiktok_module
import twitch_module
import chat_management_module
from helpers_module import logger, application
from helpers_module import WAITING_FOR_TIKTOK, WAITING_FOR_TIKTOK_DESISION
from helpers_module import APPROVE_TIKTOK, REJECT_TIKTOK, STOP_TIKTOKS_APPROVAL
from helpers_module import SEND_TIKTOK_DEEPLINK


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
    # await twitch_module.setup_twitch_objects()
    # await twitch_module.subscribe_stream_online()
    # await twitch_module.subscribe_stream_offline()
    await send_reboot_message()


conv_handler = ConversationHandler(
        entry_points=[CommandHandler("send_tiktok", tiktok_module.waiting_for_ticktock, filters=filters.ChatType.PRIVATE),
                      CommandHandler("start", tiktok_module.waiting_for_ticktock,
                                     filters=filters.Regex(rf'{SEND_TIKTOK_DEEPLINK}')&filters.ChatType.PRIVATE),
                      CommandHandler('start_approval', tiktok_module.show_tiktok_to_approve)],
        states={
            WAITING_FOR_TIKTOK:
            [
                CommandHandler('cancel', tiktok_module.cancel_waiting_for_tiktok),
                MessageHandler(filters.Entity('url'), tiktok_module.got_tiktok_link),
                MessageHandler(filters.VIDEO, tiktok_module.got_tiktok_file),
                MessageHandler(filters.ALL, tiktok_module.got_wrong_answer),
            ],
            WAITING_FOR_TIKTOK_DESISION:
            [
                CallbackQueryHandler(tiktok_module.tiktok_approval_callback_handler,
                                     pattern=rf'^.*({APPROVE_TIKTOK}_)|({REJECT_TIKTOK}_)|({STOP_TIKTOKS_APPROVAL}_)*.$')
            ]


        },
        fallbacks=[],
        name="main_conversation",
        persistent=True,
        allow_reentry=True
    )

print('Бот перезагружен')
application.add_handler(conv_handler)
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('start_tiktoks', tiktok_module.start_ticktock_evening,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('add', twitch_module.add_phrase,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('add_first', twitch_module.add_phrase_to_start,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('show', twitch_module.show,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('remove', twitch_module.remove_phrase,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('silent', twitch_module.silent,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('loud', twitch_module.loud,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))

application.add_handler(CommandHandler('mute', chat_management_module.mute, filters.REPLY))

application.add_handler(CommandHandler('info', info))
application.add_handler(CommandHandler('publish_tiktoks', tiktok_module.publish_ticktocks))
application.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,
                   chat_management_module.kick_from_group))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE,
                                       twitch_module.schedule_remove_rename_message))
# application.add_handler(MessageHandler(filters.ATTACHMENT,
#                                        tiktok_module.get_ticktock_file))
# application.add_handler(CommandHandler('file', tiktok_module.get_ticktock_file))
# application.add_handler(CommandHandler('post', post_hello_message))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
job_queue: JobQueue = application.job_queue
application.job_queue.run_custom(functions_to_run_at_the_beginning, job_kwargs={})
application.run_polling()



# TODO добавить логи
# TODO тикток вечерок



