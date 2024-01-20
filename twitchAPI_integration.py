import asyncio
import logging
import os
import sys
import traceback

import requests

import cfg

import twitchAPI
from twitchAPI import EventSub, Twitch
from logging_settings import logger
global twitch

TWITCH_TOKEN = cfg.config_data['KEYS']['TWITCH_TOKEN']
TWITCH_CLIENT_ID = cfg.config_data['KEYS']['TWITCH_CLIENT_ID']
TWITCH_CLIENT_SECRET = cfg.config_data['KEYS']['TWITCH_CLIENT_SECRET']
def get_user_id_by_login(login):
    url = 'https://api.twitch.tv/helix/users'
    headers = {'Authorization': f'Bearer {TWITCH_TOKEN}',
               'Client-Id': f'{TWITCH_CLIENT_ID}'}
    params = {'login': f'{login}'}
    req = requests.get(url, headers=headers, params=params)
    print(req.status_code)
    if req.status_code == 200:
        return {'status_code': req.status_code, 'data': req.json()['data'][0]['id']}
    else:
        return {'status_code': req.status_code, 'data': None}


def get_user_login_by_id(user_id):
    url = 'https://api.twitch.tv/helix/users'
    headers = {'Authorization': f'Bearer {TWITCH_TOKEN}',
               'Client-Id': f'{TWITCH_CLIENT_ID}'}
    params = {'id': f'{user_id}'}
    req = requests.get(url, headers=headers, params=params)
    print(req.status_code)
    if req.status_code == 200:
        return {'status_code': req.status_code, 'data': req.json()['data'][0]['login']}
    else:
        return {'status_code': req.status_code, 'data': None}


async def setup_subscribe_webhook(twitch):
    subscribe_webhook = EventSub(cfg.config_data['TWITCH_CALLBACK_URL'],
                                 TWITCH_CLIENT_ID,
                                 5555,
                                 twitch)
    subscribe_webhook.wait_for_subscription_confirm_timeout = 15
    await subscribe_webhook.unsubscribe_all()
    subscribe_webhook.start()
    return subscribe_webhook


def setup_twitch():
    twitch_object = Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
    print(f'TWITCH_OBJECT - {twitch_object}')
    return twitch_object
print('registering twitch instance')


# print(f'webhook url - {webhook.callback_url}')

