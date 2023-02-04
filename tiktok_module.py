# -*- coding: utf-8 -*-
import datetime
import os
import re
import shutil

import pytz
import requests
import telegram.error
import urllib3
from pytube import YouTube
from pytube import exceptions as pytube_exceptions
from telegram import Update, InputMediaVideo, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from telegram.helpers import create_deep_linked_url

import database
import helpers_module
import regs

from helpers_module import logger
from helpers_module import SEND_TIKTOK_DEEPLINK
from helpers_module import WAITING_FOR_TIKTOK, WAITING_FOR_TIKTOK_DESISION
from helpers_module import SKIP_TIKTOK, APPROVE_TIKTOK, REJECT_TIKTOK, STOP_TIKTOKS_APPROVAL


async def start_ticktock_evening(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    if regs.ezhov_broadcaster_id not in context.bot_data:
        context.bot_data[regs.ezhov_broadcaster_id] = {}
    context.bot_data[regs.ezhov_broadcaster_id][
        'ticktock_evening_active'] = True
    bot = await context.bot.get_me()
    url = create_deep_linked_url(bot.username, f'{SEND_TIKTOK_DEEPLINK}')
    text = f'Начался набор тиктоков на тикток вечерок. ' \
           f'Заходите в бот и предлагайте свои тиктоки'
    await context.bot.send_message(regs.zhenya_channel_id, text,
                                   reply_markup=InlineKeyboardMarkup(
                                       [[InlineKeyboardButton(
                                           "Отправить тикток", url=url)]]))


async def waiting_for_ticktock(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    logger.debug(
        f'{update.effective_user.name}({update.effective_user.id}) перешел по ссылке или по команде /send_tiktok')
    if not ('ticktock_evening_active' in context.bot_data[
        regs.ezhov_broadcaster_id] and
            context.bot_data[regs.ezhov_broadcaster_id][
                'ticktock_evening_active'] is True):
        logger.debug(
            f'{update.effective_user.name}({update.effective_user.id}). Тикток вечерок не запущен. Отменяем')
        await context.bot.send_message(update.effective_chat.id,
                                       'Сейчас нельзя отправлять тиктоки.'
                                       'Дождитесь объявления на канале')
        return ConversationHandler.END
    unapproved_tiktoks_count = database.count_unapproved_tiktoks(update.effective_user.id)['count']
    if unapproved_tiktoks_count <= 9:
        logger.debug(
            f'{update.effective_user.name}({update.effective_user.id}) Запрашиваем ссылку или файл')
        await context.bot.send_message(update.effective_chat.id,
                                       'Отправьте сюда тикток файлом или ссылкой')
        return WAITING_FOR_TIKTOK
    else:
        await context.bot.send_message(update.effective_chat.id,
                                       'Вы уже отправили 10 видео, но не один пока не подтвердили. Пока больше нельзя отправлять тиктоки.')


async def download_youtube_short(update: Update,
                           context: ContextTypes.DEFAULT_TYPE,
                           video_url):
    if not (re.match("^https://(www.)?youtube\.", video_url) or re.match(
            "^https://youtu.be", video_url)):
        await context.bot.send_message(update.effective_chat.id,
                                       "Ссылка не из youtube shorts. Я пока умею обрабатывать только ссылки из youtube shorts. Отправьте другую ссылку или файл или отмените через /cancel")
        return WAITING_FOR_TIKTOK

    try:
        video = YouTube(video_url)
        print(f'video - {video}')
        if video.length > 60:
            await context.bot.send_message(update.effective_chat.id, "Видео слишком длинное. Поддерживаются видео до 1 минуты. Отправьте заново или нажмите /cancel")
            return WAITING_FOR_TIKTOK
        try:
            stream = video.streams.filter(progressive=True,
                                       file_extension='mp4').order_by(
                'resolution').desc().first()
            return stream.download()
        except pytube_exceptions.VideoUnavailable:
            await context.bot.send_message(update.effective_chat.id, 'Это видео не поддерживается. Отправьте другую ссылку или файл или отмените через /cance;')
            return WAITING_FOR_TIKTOK
    except pytube_exceptions.RegexMatchError:
        await context.bot.send_message(update.effective_chat.id, "Пока поддержиавются только ссылки из youtube shorts. Отправьте файлом или ссылкой из youtube shorts либо отмените с помошью /cancel")
        return WAITING_FOR_TIKTOK


async def download_tiktok_video(update: Update,
                                context: ContextTypes.DEFAULT_TYPE,
                                tiktok_url):
    api_url = "https://aiov-download-youtube-videos.p.rapidapi.com/GetVideoDetails"
    querystring = {"URL": tiktok_url}
    headers = {
        "X-RapidAPI-Key": regs.x_rapid_api_key,
        "X-RapidAPI-Host": "aiov-download-youtube-videos.p.rapidapi.com"
    }
    response = requests.request("GET", api_url, headers=headers,
                                params=querystring)
    if response.status_code != 200:
        await context.bot.send_message(update.effective_chat.id,
                                       'Что-то не так с серверами. Лучше отправте видео файлом')
        return None
    response = response.json()
    if response['extractor'] != 'TikTok':
        await context.bot.send_message(update.effective_chat.id,
                                       'Файл из ссылки не из тиктока. Я пока могу скачивать только тиктоки 😢. Скачайте его и отправьте как видео')
        return None
    extension = response['ext']
    if extension != 'mp4' and extension != 'mov':
        await context.bot.send_message(update.effective_chat.id,
                                       'Я не поддерживаю такие расширения файлов как в файле из ссылки. Скачайте его и отправьте как видео')
        return None
    if response['filesize'] > 52428800:
        await context.bot.send_video(update.effective_chat.id,
                                     'Файл из ссылки весит больше 50 мб. Скачайте его и отправьте как видео')
        return None
    file_name = f'tiktok_video-{update.effective_user.id}.mp4' if extension == 'mp4' else f'tiktok_video_{update.effective_user.id}.mov'
    url = response['formats'][0]['url']
    print(url)
    connection = urllib3.PoolManager()
    with connection.request('GET', url, preload_content=False) as resp, open(
            file_name, 'wb') as out_file:
        shutil.copyfileobj(resp, out_file)

    resp.release_conn()
    return file_name


async def got_tiktok_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = await got_tiktok(update, context, is_file=True)
    return state


async def got_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = await got_tiktok(update, context, is_file=False)
    return state


async def got_tiktok(update: Update,
                     context: ContextTypes.DEFAULT_TYPE,
                     is_file):
    if is_file:
        message = await context.bot.forward_message(regs.ezhov_files_group_id,
                                                    update.effective_chat.id,
                                                    update.effective_message.id)
    else:
        result = await download_youtube_short(update, context,
                                              update.effective_message.text)
        if result == WAITING_FOR_TIKTOK:
            return WAITING_FOR_TIKTOK
        file_path = result
        message = await context.bot.send_video(regs.ezhov_files_group_id,
                                               video=file_path,
                                               caption=update.message.text)
        os.remove(file_path)
    file_id = message.video.file_id
    forwarded_message_id = message.message_id
    is_approved = update.effective_user.id == regs.ezhov_user_id or update.effective_user.id == regs.zhenya_user_id
    database.add_tiktok(forwarded_message_id, update.effective_user.id, file_id,
                        is_approved, update.effective_message.id)
    message_text = 'Тикток отправлен на одобрение Ежову.' if not is_approved \
        else 'Тикток добавлен в очередь на отправление.'
    message_text += ' Чтобы отправить ещё один, нажмите /send_tiktok или перейдите по кнопке в посте на канале'

    await context.bot.send_message(update.effective_chat.id, message_text)
    return ConversationHandler.END


async def got_wrong_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.effective_attachment is not None:
        await context.bot.send_message(update.effective_chat.id,
                                       'Вы отправили не видео, а другое вложение. Отправьте видео тиктока')
    else:
        await context.bot.send_message(update.effective_chat.id,
                                       'Я жду видео ссылку или команду /cancel')
    return WAITING_FOR_TIKTOK


async def cancel_waiting_for_tiktok(update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id,
                                   'Ок. Отменил. Теперь я ничего не жду')
    return ConversationHandler.END


async def publish_ticktocks(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    media = []
    ticktoks = database.select_tiktoks_to_send()
    if ticktoks is not None:
        for ticktok in ticktoks:
            media.append(InputMediaVideo(ticktok['file_id'],
                                         caption=f'Тикток отправлен пользователем {ticktok["sender_user_id"]}'))
        await update.effective_chat.send_media_group(media)
    else:
        await context.bot.send_message(update.effective_chat.id,
                                       'В базе данных нет тиктоков для отправки')


async def show_tiktok_to_approve(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    tiktok = database.select_tiktok_to_approve()
    if tiktok is None:
        await context.bot.send_message(update.effective_chat.id,
                                 'Еще нет тиктоков, требующих подтверждения')
        return ConversationHandler.END
    await context.bot.send_video(update.effective_chat.id,
                           video=tiktok['file_id'],
                           caption=f"Отправил - {tiktok['sender_user_id']}",
                           reply_markup=InlineKeyboardMarkup(
                               [
                                   [
                                       InlineKeyboardButton("👍", callback_data=f'{APPROVE_TIKTOK}_{tiktok["tiktok_id"]}'),
                                       InlineKeyboardButton("👎", callback_data=f'{REJECT_TIKTOK}_{tiktok["tiktok_id"]}')
                                   ],
                                   [InlineKeyboardButton("Забанить человека", callback_data=f'{STOP_TIKTOKS_APPROVAL}_|')],
                                   [InlineKeyboardButton("Закончить отбор", callback_data=f'{STOP_TIKTOKS_APPROVAL}_|')]
                               ]
                           )
                           )
    return WAITING_FOR_TIKTOK_DESISION


async def tiktok_approval_callback_handler(update: Update,
                                           context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    panel_message_id = update.effective_message.message_id
    data = update.callback_query.data.split('_')
    action = data[0]
    print(f'action - {action}')
    if action == str(APPROVE_TIKTOK) or action == str(REJECT_TIKTOK):
        tiktok_id = int(data[1])
        tiktok = database.find_tiktok(tiktok_id)
        if tiktok is None:
            await context.bot.send_message(chat_id, 'Что-то пошло не так с предыдущим тиктоком. Скипаем')
        else:
            sender_user_id = tiktok['sender_user_id']
            is_approved = action == str(APPROVE_TIKTOK)
            # try:
            #     await context.bot.forward_message(regs.ezhov_technical_group_id,
            #                                       sender_user_id,
            #                                       tiktok['in_chat_message_id'])
            #     sender_message_id = tiktok['in_chat_message_id']
            # except:
            try:
                message = context.bot.get_message(chat_id=sender_user_id,
                                                  message_id=tiktok['in_chat_message_id'])
                sender_message_id = tiktok['in_chat_message_id']
            except Exception as e:
                logger.error(e)
                print("Message not found or has been deleted")
                sender_message = await context.bot.forward_message(sender_user_id,
                                                  regs.ezhov_files_group_id,
                                                  tiktok['message_id'])
                sender_message_id = sender_message.message_id
            if is_approved:
                database.approve_tiktok(tiktok_id)
                await context.bot.send_message(sender_user_id,
                                               'Поздравляем. Стримлер одобрил твой тикток. Можно отправить ещё через /send_tiktok',
                                               reply_to_message_id=sender_message_id)
            else:
                database.reject_tiktok(tiktok_id)
                await context.bot.send_message(sender_user_id,
                                               'Cтримеру не понравился твой тикток. Можно отправить ещё через /send_tiktok',
                                               reply_to_message_id=sender_message_id)
        next_tiktok = database.select_tiktok_to_approve()
        if next_tiktok is not None:
            await next_tiktok_to_approve(update, context, next_tiktok)
        else:
            await context.bot.delete_message(chat_id, panel_message_id)
            await context.bot.send_message(chat_id, 'Тиктоки на одобрение закончились')
            return ConversationHandler.END
    elif action == str(STOP_TIKTOKS_APPROVAL):
        await context.bot.delete_message(chat_id, panel_message_id)
        await context.bot.send_message(chat_id,
                                       'Хорошо. Отбор тиктоков завершён')
        return ConversationHandler.END


async def next_tiktok_to_approve(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE,
                                 next_tiktok):
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👍",
                                     callback_data=f'{APPROVE_TIKTOK}_{next_tiktok["tiktok_id"]}'),
                InlineKeyboardButton("👎",
                                     callback_data=f'{REJECT_TIKTOK}_{next_tiktok["tiktok_id"]}')
            ],

            [InlineKeyboardButton("Закончить отбор",
                                  callback_data=f'{STOP_TIKTOKS_APPROVAL}_')]
        ]
    )
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    await context.bot.edit_message_media(
        InputMediaVideo(next_tiktok['file_id'],
                        caption=f'Отправил - {next_tiktok["sender_user_id"]}'),
        chat_id,
        message_id)
    await context.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=reply_markup)
    # await context.bot.send_video(
    #     chat_id=chat_id,
    #     video=next_tiktok['file_id'],
    #     caption=f'Отправил - {next_tiktok["sender_user_id"]}',
    #     reply_markup=reply_markup)






