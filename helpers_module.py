import logging
import os
import sys
import traceback
import platform

import pytz
import telegram.ext
from telegram.ext import Defaults, PicklePersistence, ApplicationBuilder

import database
import regs
from regs import cursor

# Deeplink_types
SEND_TIKTOK_DEEPLINK, ANONIMOUS_QUESTIONS_DEEPLINK = \
    (int(f'10{number}') for number in range(1, 2 + 1))
# Tiktok handler states
WAITING_FOR_TIKTOK, WAITING_FOR_TIKTOK_DESISION = \
    (int(f'20{number}') for number in range(1, 2 + 1))
# Tiktok approval query states
TIKTOK_APPROVAL_STATES = '3'
APPROVE_TIKTOK, REJECT_TIKTOK, BAN_TIKTOK_SENDER, STOP_TIKTOKS_APPROVAL, SUPER_APPROVE_TIKTOK = \
    (int(f'30{number}') for number in range(1, 5 + 1))


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


# Users
async def get_user_info(user_id):
    user_id = str(user_id)
    command = '''
    SELECT * FROM ezhov_bot.users
    WHERE user_id = %s
    '''
    print(command)
    cursor.execute(command, (user_id,))
    user_info = cursor.fetchone()
    print(user_info)
    return user_info


async def add_user(user_id, full_name):
    user_id = str(user_id)
    command = '''
    INSERT INTO ezhov_bot.users (user_id, full_name)
    VALUES (%s, %s)'''
    cursor.execute(command, (user_id, full_name,))


async def update_user(user_id, nickname='', place_of_living='', bio='',
                     is_moderator='', is_admin='', can_send_tiktok='',
                     tiktoks_banned_until='', full_name='', title=''):
    user_id = str(user_id)
    where_clause = f"user_id = %s"
    fields_dict = {'nickname': nickname,
                   'place_of_living': place_of_living,
                   'bio': bio,
                   'is_moderator': is_moderator,
                   'is_admin': is_admin,
                   'can_send_tiktok': can_send_tiktok,
                   'tiktoks_banned_until': tiktoks_banned_until,
                   'full_name': full_name,
                   'title': title}
    set_string = ''
    fields_tuple = ()
    for key in fields_dict:
        if fields_dict[key] != '':
            set_string = set_string + f"{key} = %s, "
            fields_tuple = fields_tuple + (fields_dict[key],)
    fields_tuple = fields_tuple + (user_id,)
    set_string = set_string[0:-2]
    print(set_string)
    command = f'UPDATE ezhov_bot.users SET {set_string} WHERE {where_clause}'
    print(command)
    print(fields_tuple)
    cursor.execute(command, fields_tuple)
    cursor.execute('commit')


def update_user_info(function):
    async def wrapper(*args, **kwargs):
        print(f'decorated function - {function.__name__}')
        update: telegram.Update = args[0]
        context: telegram.ext.ContextTypes.DEFAULT_TYPE = args[1]
        user_id = update.effective_user.id
        user_info = await get_user_info(user_id)
        if user_info is None:
            await add_user(user_id, update.effective_user.full_name)
        else:
            if user_info['full_name'] != update.effective_user.full_name:
                await update_user(user_id, full_name=update.effective_user.full_name)
            context.user_data['user_info'] = user_info
        return await function(*args, **kwargs)
    return wrapper


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
current_os = platform.system()
token = regs.bot_token_zhenya if current_os == 'Windows' else regs.bot_token_main

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


def generate_tiktok_senders_string(names):
    name_dict = {}

    for i, name in enumerate(names):
        if name in name_dict:
            name_dict[name].append(i+1)
        else:
            name_dict[name] = [i+1]

    sorted_result = sorted(name_dict.items(), key=lambda item: item[1][0])
    print(sorted_result)
    string = ''
    for value in sorted_result:
        indexes_sting = ''
        name = value[0]
        indexes_list = value[1]
        for index in indexes_list:
            indexes_sting += f'{index}й, '
        indexes_sting = indexes_sting[:-2]
        string += f'{indexes_sting} тикток{"и" if len(indexes_list) > 1 else ""} отправил(а) {name}\n'
    string = string[:-1]
    logger.debug(f'string - {string}')

    return string









