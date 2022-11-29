import logging
import os
import sys
import traceback

import requests

import bot
import regs
import twitchAPI
from twitchAPI import EventSub, TwitchAPIException, UnauthorizedException, \
    TwitchAuthorizationException, TwitchBackendException, \
    MissingScopeException, Twitch, EventSubSubscriptionConflict, \
    EventSubSubscriptionError, EventSubSubscriptionTimeout
from regs import logger


def get_user_id_by_login(login):
    url = 'https://api.twitch.tv/helix/users'
    headers = {'Authorization': f'Bearer {regs.twitch_token}',
               'Client-Id': f'{regs.twitch_client_id}'}
    params = {'login': f'{login}'}
    req = requests.get(url, headers=headers, params=params)
    print(req.status_code)
    if req.status_code == 200:
        return {'status_code': req.status_code, 'data': req.json()['data'][0]['id']}
    else:
        return {'status_code': req.status_code, 'data': None}


def get_user_login_by_id(user_id):
    url = 'https://api.twitch.tv/helix/users'
    headers = {'Authorization': f'Bearer {regs.twitch_token}',
               'Client-Id': f'{regs.twitch_client_id}'}
    params = {'id': f'{user_id}'}
    req = requests.get(url, headers=headers, params=params)
    print(req.status_code)
    if req.status_code == 200:
        return {'status_code': req.status_code, 'data': req.json()['data'][0]['login']}
    else:
        return {'status_code': req.status_code, 'data': None}


def setup_subscribe_webhook():
    webhook = EventSub(regs.twith_callback_url, regs.twitch_client_id, 5555, twitch)
    webhook.wait_for_subscription_confirm_timeout = 15
    webhook.unsubscribe_all()
    webhook.start()
    return webhook


twitch = Twitch(regs.twitch_client_id, regs.twitch_client_secret)
webhook = setup_subscribe_webhook()
webhook.listen_stream_online(regs.zhenya_broadcaster_id,
                             callback=bot.post_stream_notification)
