import asyncio

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import cfg
import channel_points_module

from logging_settings import logger
from telethon.sync import TelegramClient
from telethon import functions, types


async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await channel_points_module.add_points_for_comment(update, context)
    thread_id = update.message.message_thread_id
    threads = cfg.config_data['CHATS']['FORUM_THREADS']
    logger.debug(f'Thread_id - {thread_id}, Posts_thread_id - {threads["posts"]}')
    if thread_id in [threads['posts'], threads['tiktoks'], threads['ezhov_news'],
                     threads['frontend_vlog'], threads['zhizhov']]:
        logger.debug('Forwarding post to comments(checking streamer)')
        if update.effective_user.id in [cfg.STREAMER_USER_ID]:
            logger.debug('forwarding post to comments')
            await context.bot.forward_message(update.message.chat_id,
                                              update.message.chat_id,
                                              update.message.message_id)
            logger.debug('forwarding post to channel')
            await asyncio.sleep(3)
            msg = await context.bot.forward_message(cfg.CHANNEL_ID,
                                                    update.message.chat_id,
                                                    update.message.message_id)
            await asyncio.sleep(3)
            # forum_dict = {
            #     threads['posts']: 'постики',
            #     threads['tiktoks']: 'тиктоки',
            #     threads['ezhov_news']: 'новости',
            #     threads['frontend_vlog']: 'новости по программированию',
            #     threads['stream_time']: 'посты о стримах и их обсуждения',
            #     threads['life']: 'постики о жизни',
            # }
            # print(f'<a href = "t.me/ezhov_test_chat/{thread_id}">➡️остальные {forum_dict[thread_id]} тут⬅️</a>')
            print(f'msg - {msg}')
            context.bot_data['searching_for_post'] = True
            context.bot_data['post_message_text'] = msg.text


async def comment_under_the_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('entered comments function')
    print(update.effective_user)
    if 'searching_for_post' not in context.bot_data.keys():
        searching_for_post = False
    else:
        searching_for_post = context.bot_data['searching_for_post']
    if searching_for_post:
        if update.effective_message.text == context.bot_data['post_message_text']:
            context.bot_data['searching_for_post'] = False
            message_id = update.effective_message.message_id
            context.application.job_queue.run_once(callback=reply_to_message,
                                                   when=20,
                                                   data={
                                                       'message_id': message_id})


async def reply_to_message(context: ContextTypes.DEFAULT_TYPE):
    message_id = context.job.data['message_id']
    await context.bot.send_message(cfg.CHANNEL_GROUP_ID,
                                               f'<a href = "https://t.me/zdarovezhov_cummunity">👉 Всё наше каммунити тут!👈</a>\n'
                                               f'Сейчас ты в канале с уведомлениями, здесь мы особо не общаемся, он создан для удобства получения всех постов',
                                               reply_to_message_id=message_id,
                                               parse_mode=ParseMode.HTML)


# async def forward_to_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # forward_thread_id = regs.ezhov_forum_threads['comments']
#     # forward_channel_id = cfg.FORUM_ID
#     # forwarded_message_channel_id = cfg.CHANNEL_ID
#     forward_thread_id = None
#     forward_channel_id = cfg.TEST_FORUM_ID
#     forwarded_channel_id = cfg.TEST_CHANNEL_ID
#     if update.effective_chat.id == forwarded_channel_id:
#         logger.debug(f'forwarding post from main channel')
#         await context.bot.forward_message(forward_channel_id,
#                                           update.effective_chat.id,
#                                           update.effective_message.id,
#                                           message_thread_id=forward_thread_id)
