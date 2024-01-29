import asyncio
import logging
import os
import sys
import traceback
import asyncio
import requests

import cfg

import twitchAPI
from twitchAPI.eventsub import webhook
from twitchAPI.twitch import Twitch
from twitchAPI.twitch import AuthScope, TwitchUser
from logging_settings import logger
# global twitch

TWITCH_TOKEN = cfg.config_data['KEYS']['TWITCH_TOKEN']
TWITCH_CLIENT_ID = cfg.config_data['KEYS']['TWITCH_CLIENT_ID']
TWITCH_CLIENT_SECRET = cfg.config_data['KEYS']['TWITCH_CLIENT_SECRET']

global app_twitch, app_webhook


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
    subscribe_webhook = webhook.EventSubWebhook(cfg.config_data['KEYS']['TWITH_CALLBACK_URL'],
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


# twitch_object_ = setup_twitch()
# user: TwitchUser = asyncio.run(twitch_object_.get_users(logins=['Zhenya_2001']).__anext__())
# print(user.id)



# print(f'webhook url - {webhook.callback_url}')

