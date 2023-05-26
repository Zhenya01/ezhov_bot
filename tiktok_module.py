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
from helpers_module import update_user_info
from helpers_module import SEND_TIKTOK_DEEPLINK
from helpers_module import WAITING_FOR_TIKTOK, WAITING_FOR_TIKTOK_DESISION
from helpers_module import APPROVE_TIKTOK, REJECT_TIKTOK, \
    STOP_TIKTOKS_APPROVAL, BAN_TIKTOK_SENDER


async def start_ticktock_evening(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    if regs.ezhov_broadcaster_id not in context.bot_data:
        context.bot_data[regs.ezhov_broadcaster_id] = {}
    context.bot_data[regs.ezhov_broadcaster_id][
        'ticktock_evening_active'] = True
    bot = await context.bot.get_me()
    url = create_deep_linked_url(bot.username, f'{SEND_TIKTOK_DEEPLINK}')
    threads = ['tiktoks', 'comments']
    text = '''
Начинаем набор видео на Тик-Ток вечерок! 
Просто скиньте видео боту, нажав кнопку.
Бот принимает видео СКАЧАННЫЕ с тик-тока! Ссылки на тик-ток пока не работают)'''
    for thread in threads:
        await context.bot.send_message(regs.ezhov_forum_id, text, message_thread_id=regs.ezhov_forum_threads[thread],
                                       reply_markup=InlineKeyboardMarkup(
                                           [[InlineKeyboardButton(
                                               "Отправить тикток", url=url)]]))
    # await context.bot.send_message(regs.tiktoks_channel_id, text,
    #                                reply_markup=InlineKeyboardMarkup(
    #                                    [[InlineKeyboardButton(
    #                                        "Отправить тикток", url=url)]]))


async def test_thread_sending(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    threads = ['tiktoks', 'comments']
    text = 'Tест. Бип-боп. Сорян за флуд заранее)'
    for thread in threads:
        logger.debug(
            f'{update.effective_user.name}({update.effective_user.id}) thread_id - {regs.ezhov_forum_threads[thread]}')
        await context.bot.send_message(regs.ezhov_forum_id, text, message_thread_id=regs.ezhov_forum_threads[thread])

@update_user_info
async def waiting_for_ticktock(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    logger.debug(
        f'{update.effective_user.name}({update.effective_user.id}) перешел по ссылке или по команде /send_tiktok')
    if not ('ticktock_evening_active' in context.bot_data[regs.ezhov_broadcaster_id] and context.bot_data[regs.ezhov_broadcaster_id][
                'ticktock_evening_active'] is True):
        logger.debug(
            f'{update.effective_user.name}({update.effective_user.id}). Тикток вечерок не запущен. Отменяем')
        await context.bot.send_message(update.effective_chat.id,
                                       'Сейчас нельзя отправлять тиктоки.'
                                       'Дождитесь объявления на канале')
        return ConversationHandler.END
    unapproved_tiktoks_count = \
    database.count_unapproved_tiktoks(update.effective_user.id)['count']
    user_info = context.user_data['user_info']
    can_send_tiktok = user_info['can_send_tiktok']
    print(f'can_send_tiktok - {can_send_tiktok}')
    if not can_send_tiktok:
        tiktoks_banned_until = user_info['tiktoks_banned_until']
        print(f'tiktoks_banned_until - {tiktoks_banned_until},'
              f'datetime.now() - {datetime.datetime.now()}')
        if tiktoks_banned_until < datetime.datetime.now():
            can_send_tiktok = True
            database.unban_user_from_tiktoks(update.effective_user.id)
    if unapproved_tiktoks_count > 9:
        await context.bot.send_message(update.effective_chat.id,
                                       'Вы уже отправили 10 видео, но не один пока не подтвердили. Пока больше нельзя отправлять тиктоки')
    elif not can_send_tiktok:
        time_banned_string = tiktoks_banned_until.strftime("%Y-%m-%d %H:%M:%S")
        await context.bot.send_message(update.effective_chat.id,
                                       f'Вы не можете отправлять тиктоки, потому что вы были временно забанены стримером (до {time_banned_string})')
    else:
        logger.debug(
            f'{update.effective_user.name}({update.effective_user.id}) Запрашиваем ссылку или файл')
        await context.bot.send_message(update.effective_chat.id,
                                       'Отправьте сюда видео тиктока или ссылку на youtube shorts. Отправлять можно только по 1 видео. Если отправите много - я приму только первое')
        return WAITING_FOR_TIKTOK


@update_user_info
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
            await context.bot.send_message(update.effective_chat.id,
                                           "Видео слишком длинное. Поддерживаются видео до 1 минуты. Отправьте заново или нажмите /cancel")
            return WAITING_FOR_TIKTOK
        try:
            stream = video.streams.filter(progressive=True,
                                          file_extension='mp4').order_by(
                'resolution').desc().first()
            return stream.download()
        except pytube_exceptions.VideoUnavailable:
            await context.bot.send_message(update.effective_chat.id,
                                           'Это видео не поддерживается. Отправьте другую ссылку или файл или отмените через /cancel')
            return WAITING_FOR_TIKTOK
    except pytube_exceptions.RegexMatchError:
        await context.bot.send_message(update.effective_chat.id,
                                       "Ссылка не из youtube shorts. Я пока умею обрабатывать только ссылки из youtube shorts. Отправьте другую ссылку или файл или отмените через /cancel")
        return WAITING_FOR_TIKTOK


@update_user_info
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
                                       'Что-то не так с серверами. Лучше отправьте видео файлом')
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


@update_user_info
async def got_tiktok_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = await got_tiktok(update, context, is_file=True)
    return state


@update_user_info
async def got_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = await got_tiktok(update, context, is_file=False)
    return state


@update_user_info
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
    is_approved = update.effective_user.id == regs.ezhov_user_id
    database.add_tiktok(forwarded_message_id, update.effective_user.id,
                        file_id,
                        is_approved, update.effective_message.id)
    message_text = 'Я посмотрю, а пока' if not is_approved \
        else 'Тикток добавлен в очередь на отправление'
    unapproved_count = database.count_unapproved_tiktoks(update.effective_user.id)['count']
    if unapproved_count <= 9:
        message_text += ' можешь отправить еще) /send_tiktok'
    else:
        message_text += ' отдохни) Ты отправил(а) слишком много. Я напишу, когда можно будет отправить ещё'
    if unapproved_count == 5:
        context.bot.send_message(regs.ezhov_user_id, f'Пользователь {update.effective_user.full_name} уже имеет 5 неодобренных тиктоков. Скоро он не сможет отправлять тиктоки. Пора бы отфильтровать :)')
    await context.bot.send_message(update.effective_chat.id, message_text)
    return ConversationHandler.END


@update_user_info
async def got_wrong_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.effective_attachment is not None:
        await context.bot.send_message(update.effective_chat.id,
                                       'Вы отправили не видео, а другое вложение. Отправьте видео тиктока')
    else:
        await context.bot.send_message(update.effective_chat.id,
                                       'Я жду видео, ссылку или команду /cancel')
    return WAITING_FOR_TIKTOK


@update_user_info
async def cancel_waiting_for_tiktok(update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id,
                                   'Ок. Отменил. Теперь я ничего не жду')
    return ConversationHandler.END


@update_user_info
async def publish_ticktocks(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == regs.ezhov_user_id:
        media = []
        caption = 'Спасибо всем кто присылает видева!)\n'
        names = []
        ticktoks = database.select_tiktoks_to_send()
        if ticktoks is not None:
            for ticktok in ticktoks:
                user = await database.get_user_info(ticktok["sender_user_id"])
                media.append(InputMediaVideo(ticktok['file_id']))
                if update.effective_user.id != regs.ezhov_user_id:
                    names.append(user["full_name"])
                    # caption = caption + f'{ticktoks.index(ticktok) + 1}й тикток прислал(а) {user["full_name"]}\n'

            caption += helpers_module.generate_tiktok_senders_string(names)
            logger.debug(f'caption - {caption}')

            await context.bot.send_media_group(regs.tiktoks_channel_id,
                                               media=media, caption=caption)
            for tiktok in ticktoks:
                database.tiktok_posted(tiktok['tiktok_id'])
        else:
            await context.bot.send_message(update.effective_chat.id,
                                           'В базе данных нет тиктоков для отправки')


@update_user_info
async def show_tiktok_to_approve(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == regs.ezhov_user_id:
        tiktok = database.select_tiktok_to_approve()
        if tiktok is None:
            await context.bot.send_message(update.effective_chat.id,
                                           'Еще нет тиктоков, требующих подтверждения')
            return ConversationHandler.END
        await send_tiktok_info(update, context, tiktok, first_time=True)
        return WAITING_FOR_TIKTOK_DESISION


async def send_tiktok_info(update, context, tiktok, first_time):
    if update.effective_user.id == regs.ezhov_user_id:
        result = database.count_unsent_tiktoks()
        count = result['count'] if result is not None else None
        number_of_posts = count // 10
        sender = await database.get_user_info(tiktok['sender_user_id'])
        sender_name = sender['full_name']
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("👍", callback_data=f'{APPROVE_TIKTOK}_{tiktok["tiktok_id"]}'),
                    InlineKeyboardButton("👎", callback_data=f'{REJECT_TIKTOK}_{tiktok["tiktok_id"]}')
                ],
                [
                    InlineKeyboardButton("Забанить отправителя", callback_data=f'{BAN_TIKTOK_SENDER}_{tiktok["tiktok_id"]}')
                ],
                [
                    InlineKeyboardButton("Закончить отбор", callback_data=f'{STOP_TIKTOKS_APPROVAL}_|')
                ]
            ]
        )
        print(reply_markup)
        caption = f"Отправил - {sender_name}\n" \
                  f"Набрано постов тиктоков: {number_of_posts}\n" \
                  f"{'Отправить: /publish' if number_of_posts != 0 else ''}"
        if first_time:
            await context.bot.send_video(update.effective_chat.id,
                                         video=tiktok['file_id'],
                                         caption=caption,
                                         reply_markup=reply_markup
                                         )
        else:
            chat_id = update.effective_chat.id
            message_id = update.effective_message.message_id
            try:
                sender = await database.get_user_info(tiktok['sender_user_id'])
                print(f'sender - {sender}')
                await context.bot.edit_message_media(
                    InputMediaVideo(tiktok['file_id'],
                                    caption=caption),
                    chat_id,
                    message_id)
                await context.bot.edit_message_reply_markup(chat_id, message_id,
                                                            reply_markup=reply_markup)
            except telegram.error.BadRequest:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=tiktok['file_id'],
                    caption=caption,
                    reply_markup=reply_markup)


@update_user_info
async def tiktok_approval_callback_handler(update: Update,
                                           context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == regs.ezhov_user_id:
        print('STARTING TO DEFINE TIKTOK ACTION')
        chat_id = update.effective_chat.id
        panel_message_id = update.effective_message.message_id
        data = update.callback_query.data.split('_')
        action = data[0]
        print(f'action - {action}')
        if action == str(APPROVE_TIKTOK) or action == str(
                REJECT_TIKTOK) or action == str(BAN_TIKTOK_SENDER):
            tiktok_id = int(data[1])
            tiktok = database.find_tiktok(tiktok_id)
            if tiktok is None:
                await context.bot.send_message(chat_id,
                                               'Что-то пошло не так с предыдущим тиктоком. Скипаем')
            else:
                sender_user_id = tiktok['sender_user_id']
                is_approved = action == str(APPROVE_TIKTOK)
                is_banned = action == str(BAN_TIKTOK_SENDER)
                print(f'is_banned - {is_banned}')
                if is_approved:
                    database.approve_tiktok(tiktok_id)
                    message_text = 'ВАААААУ, тик-ток шикарен, СПО СИ БО! Скинь ещё: /send_tiktok'
                else:
                    database.reject_tiktok(tiktok_id)
                    if is_banned:
                        ban_end_time = datetime.datetime.now() + datetime.timedelta(
                            hours=1)
                        ban_end_string = ban_end_time.strftime("%Y-%m-%d %H:%M:%S")
                        database.ban_user_from_tiktoks(sender_user_id,
                                                       ban_end_time)
                        message_text = f'Что это? Фу бл! Ты в БАНЕ! Сиди жди разбана до {ban_end_string}'
                    else:
                        message_text = 'Не, ты можешь лучше, кидай другое видео) /send_tiktok'
                try:
                    await context.bot.send_message(sender_user_id,
                                                   message_text,
                                                   reply_to_message_id=tiktok[
                                                       'in_chat_message_id'],
                                                   allow_sending_without_reply=False)
                except:
                    sender_message = await context.bot.forward_message(
                        sender_user_id,
                        regs.ezhov_files_group_id,
                        tiktok['message_id'])
                    sender_message_id = sender_message.message_id
                    await context.bot.send_message(sender_user_id,
                                                   message_text,
                                                   reply_to_message_id=sender_message_id)
            next_tiktok = database.select_tiktok_to_approve()
            if next_tiktok is not None:
                await next_tiktok_to_approve(update, context, next_tiktok)
            else:
                await context.bot.delete_message(chat_id, panel_message_id)
                await context.bot.send_message(chat_id,
                                               'Тиктоки на одобрение закончились')
                return ConversationHandler.END
        elif action == str(STOP_TIKTOKS_APPROVAL):
            await context.bot.delete_message(chat_id, panel_message_id)
            await context.bot.send_message(chat_id,
                                           'Хорошо. Отбор тиктоков завершён')
            return ConversationHandler.END


@update_user_info
async def next_tiktok_to_approve(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE,
                                 next_tiktok):
    if update.effective_user.id == regs.ezhov_user_id:
        await send_tiktok_info(update, context, next_tiktok, first_time=False)

    # reply_markup = InlineKeyboardMarkup(
    #     [
    #         [
    #             InlineKeyboardButton("👍",
    #                                  callback_data=f'{APPROVE_TIKTOK}_{next_tiktok["tiktok_id"]}'),
    #             InlineKeyboardButton("👎",
    #                                  callback_data=f'{REJECT_TIKTOK}_{next_tiktok["tiktok_id"]}')
    #         ],
    #
    #         [InlineKeyboardButton("Закончить отбор",
    #                               callback_data=f'{STOP_TIKTOKS_APPROVAL}_')]
    #     ]
    # )
    # chat_id = update.effective_chat.id
    # message_id = update.effective_message.message_id
    # try:
    #     sender = await database.get_user_info(next_tiktok['sender_user_id'])
    #     print(f'sender - {sender}')
    #     await context.bot.edit_message_media(
    #         InputMediaVideo(next_tiktok['file_id'],
    #                         caption=f'Отправил - {sender["full_name"]}'),
    #         chat_id,
    #         message_id)
    #     await context.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=reply_markup)
    # except telegram.error.BadRequest:
    #     await context.bot.send_video(
    #         chat_id=chat_id,
    #         video=next_tiktok['file_id'],
    #         caption=f'Отправил - {next_tiktok["sender_user_id"]}',
    #         reply_markup=reply_markup)
