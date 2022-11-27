import os
import sys
import traceback

import regs
from telegram.ext import Updater, CallbackContext, CommandHandler, \
    MessageHandler, Filters, PicklePersistence
from telegram import Update
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s: %(levelname)s, %(threadName)s, %(filename)s, %(funcName)s, %(message)s',
    handlers=[
        logging.FileHandler(f'{os.path.abspath(os.path.dirname(__file__))}/ezhov_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


def logging_uncaught_exceptions(ex_type, ex_value, trace_back):
    if issubclass(ex_type, KeyboardInterrupt):
        sys.__excepthook__(ex_type, ex_value, trace_back)
        return
    logging.critical(''.join(traceback.format_tb(trace_back)))
    logging.critical('{0}: {1}'.format(ex_type, ex_value))


sys.excepthook = logging_uncaught_exceptions

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет. Я Жижов. Добро пожаловать!")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Кстааати, купи слона!")


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми да и купи слона!')


bot_persistence = PicklePersistence(filename=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')
updater = Updater(token=regs.bot_token,
                  persistence=bot_persistence)
updater.dispatcher.bot.send_message(93906905, 'Бот перезагружен')
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
updater.start_polling()

updater.idle()