import logging
import os
import sys
import traceback

import pytz
from telegram.ext import Defaults, PicklePersistence, ApplicationBuilder

import regs

# Deeplink_types
SEND_TIKTOK_DEEPLINK, ANONIMOUS_QUESTIONS_DEEPLINK = \
    (int(f'10{number}') for number in range(1, 2 + 1))
# Tiktok handler states
WAITING_FOR_TIKTOK, WAITING_FOR_TIKTOK_DESISION = \
    (int(f'20{number}') for number in range(1, 2 + 1))
# Tiktok approval query states
APPROVE_TIKTOK, REJECT_TIKTOK, SKIP_TIKTOK, STOP_TIKTOKS_APPROVAL = \
    (int(f'30{number}') for number in range(1, 4 + 1))


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s: %(levelname)s, %(threadName)s, %(filename)s, %(funcName)s] %(message)s',
    handlers=[
        logging.FileHandler(f'{os.path.abspath(os.path.dirname(__file__))}/ezhov_bot.log', encoding='utf8'),
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






class FilterRepeatingBot(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return not (record.getMessage().endswith('Entering: get_updates')
                    or record.getMessage().endswith('Exiting: get_updates')
                    or record.getMessage().endswith('No new updates found.')
                    or record.getMessage().endswith('()')
                    or record.getMessage().endswith('Entering: send_message')
                    or record.getMessage().endswith('Exiting: send_message'))


class FilterRepeatingApplication(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return not (record.getMessage().endswith('Starting next run of updating the persistence.')
                    or record.getMessage().endswith('Finished updating persistence.'))


class FilterRepeatingClient(logging.Filter):
    def filter(self, record: logging.LogRecord):
        return not (record.getMessage().endswith('"HTTP/1.1 200 OK"')
                    or record.getMessage().endswith('"HTTP/1.1 200 OK"'))


logging.getLogger('telegram._bot').addFilter(FilterRepeatingBot())
logging.getLogger('telegram.ext._application').addFilter(FilterRepeatingApplication())
logging.getLogger('httpx._client').addFilter(FilterRepeatingClient())
logging.getLogger('mtprotosender').setLevel(logging.INFO)


defaults=Defaults(tzinfo=pytz.timezone('Europe/Moscow'))
persistence = PicklePersistence(filepath=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')
token = regs.bot_token_zhenya

application = ApplicationBuilder().token(token).persistence(persistence).defaults(defaults).build()


def reformat_name(name:str):
    replacement_dict = {'_': '\_', '*': '\*', '[': '\[', ']': '\]', '(': '\(',
                    ')': '\)', '~': '\~', '`': '\`', '>': '\>', '#': '\#',
                    '+': '\+', '-': '\-', '=': '\=', '|': '\|', '{': '\{',
                    '}': '\}', '.': '\.', '!': '\!'}
    for i, j in replacement_dict.items():
        name = name.replace(i, j)
    return name


def seconds_to_delta(duration):
    days = duration // (24 * 3600)
    duration = duration % (24 * 3600)
    hours = duration // 3600
    duration %= 3600
    minutes = duration // 60
    duration %= 60
    seconds = duration
    return {'days': int(days),
            'hours': int(hours),
            'minutes': int(minutes),
            'seconds': int(seconds)}







