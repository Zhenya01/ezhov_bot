import logging
import os
import sys
import traceback
import platform

import pytz
import telegram.ext
from telegram.ext import Defaults, PicklePersistence, ApplicationBuilder
from telethon.tl.types.messages import Chats


import yaml

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
# Points management
ADD_OR_SUBTRACT_POINTS, ADD_POINTS, SUBTRACT_POINTS, ENTER_POINTS_MANAGEMENT, SELECT_USER =  \
    (int(f'40{number}') for number in range(1, 5 + 1))
# Rewards management
SELECT_REWARD_TO_EDIT, PICK_ACTION, EDIT_REWARD, ADDING_REWARD = \
    (int(f'50{number}') for number in range(1, 4 + 1))
# User points interface
USER_POINTS_MENU, SELECT_REWARD_TO_BUY, WAITING_FOR_REWARD_DECISION, WAITING_FOR_REWARD_BUY_ACCEPT = (int(f'60{number}') for number in range(1, 4 + 1))
APPROVE_REWARD, DECLINE_REWARD = (int(f'70{number}') for number in range(1, 2 + 1))
UNBAN_CHATTER = '801'
ADD_REWARD_NAME, ADD_REWARD_DESCRIPTION, ADD_REWARD_PRICE = \
    (int(f'90{number}') for number in range(1, 3 + 1))
# Rewards vars
(CHANGE_NAME, CHANGE_DESCRIPTION, CHANGE_PRICE, CHANGE_NUMBER_LEFT, CHANGE_PERSON_TOTAL_LIMIT,
 CHANGE_PERSON_COOLDOWN, CHANGE_TOTAL_COOLDOWN) = ('Изменить название', 'Изменить описание', 'Изменить цену',
                                                   'Изменить остаток', 'Изменить лимит на человека',
                                                   'Изменить кулдаун на человека', 'Изменить кулдаун на награду')
REMOVE_REWARD, BACK_TO_REWARDS = 'Удалить награду', '⬅️ К списку наград'
# Points vars
SEE_REWARDS, SEE_POINTS_INFO = '🏆 Посмотреть награды', 'ℹ️ Посмотреть подробную информацию'
# Common buttons vars
CANCEL_BUTTON = '❌ Отменить'
ADD_REWARD_BUTTON = '➕ Добавить награду'
BUY_REWARD = '💰 Купить'
# Reward reasons
VIEW, EDIT = 'view', 'edit'


config_data = {}
config_test_data = {}
current_os = platform.system()
config_name = 'config_test.yaml' if current_os == 'Windows' else 'config.yaml'
config_test_name = 'config.yaml' if current_os == 'Windows' else 'config_test.yaml'

with open(config_name, "r") as yamlfile:
    config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)

with open(config_test_name, "r") as yamlfile:
    config_test_data = yaml.load(yamlfile, Loader=yaml.FullLoader)

API_TOKEN = config_data["BOT"]["TOKEN"]

TG_POINTS = config_data["TG_POINTS"]
BASE_COMMENT_POINTS = TG_POINTS["BASE_COMMENT_POINTS"]
PRESTIGE_LEVEL_ADDED_MULTIPLIER = TG_POINTS["PRESTIGE_LEVEL_ADDED_MULTIPLIER"]
BASE_ACCEPTED_TIKTOK_PRAISE = TG_POINTS["BASE_ACCEPTED_TIKTOK_PRAISE"]
BASE_FIRE_TIKTOK_PRAISE = TG_POINTS["BASE_FIRE_TIKTOK_PRAISE"]
BASE_REJECTED_TIKTOK_PRAISE = TG_POINTS["BASE_REJECTED_TIKTOK_PRAISE"]
BASE_MAX_TIKTOK_POINTS = TG_POINTS["BASE_MAX_TIKTOK_POINTS"]


CHATS = config_data['CHATS']
TEST_CHATS = config_test_data['CHATS']

FORUM_ID = CHATS['FORUM_GROUP']
CHANNEL_ID = CHATS['CHANNEL_ID']
CHANNEL_GROUP_ID = CHATS['CHANNEL_GROUP_ID']
STREAMER_USER_ID = CHATS['STREAMER_USER_ID']

TIKTOK_FILES_GROUP_ID = CHATS['TIKTOK_FILES_GROUP_ID']

TEST_FORUM_ID = TEST_CHATS['FORUM_GROUP']
TEST_CHANNEL_ID = TEST_CHATS['CHANNEL_ID']
TEST_CHANNEL_GROUP_ID = TEST_CHATS['CHANNEL_GROUP_ID']
TEST_STREAMER_USER_ID = TEST_CHATS['STREAMER_USER_ID']

# Users
defaults = Defaults(tzinfo=pytz.timezone('Europe/Moscow'))
persistence = PicklePersistence(filepath=f'{os.path.abspath(os.path.dirname(__file__))}/bot_persistence')
current_os = platform.system()


application = ApplicationBuilder().token(API_TOKEN).persistence(persistence).defaults(defaults).build()


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

    return string









