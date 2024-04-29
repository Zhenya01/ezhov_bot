import asyncio

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import cfg
import channel_points_module

from logging_settings import logger


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
            context.bot_data['searching_for_post'] = True
            context.bot_data['post_message_text'] = msg.text


async def forward_post_from_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_me = await context.bot.get_me()
    first_name = bot_me.first_name
    print('bot_me', bot_me, first_name)
    if update.channel_post.author_signature != first_name:
        print('Forwarding post from channel')
        threads = cfg.config_data['CHATS']['FORUM_THREADS']
        # if thread_id in [threads['posts'], threads['tiktoks'], threads['ezhov_news'],
        #                  threads['frontend_vlog'], threads['zhizhov']]:
        logger.debug('forwarding post to comments')
        await context.bot.forward_message(cfg.FORUM_ID,
                                          update.effective_chat.id,
                                          update.effective_message.message_id,
                                          message_thread_id=threads['posts'])

        logger.debug('forwarding post to posts')
        await asyncio.sleep(3)
        await context.bot.forward_message(cfg.FORUM_ID,
                                          update.effective_chat.id,
                                          update.effective_message.message_id)
        await asyncio.sleep(3)
        context.bot_data['searching_for_post'] = True
        context.bot_data['post_message_text'] = update.effective_message.text


async def comment_under_the_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                                                       'message_id': message_id,
                                                       'group_id': update.effective_chat.id})


async def reply_to_message(context: ContextTypes.DEFAULT_TYPE):
    message_id = context.job.data['message_id']
    group_id = context.job.data['group_id']
    await context.bot.send_message(group_id,
                                   f'<a href = "https://t.me/zdarovezhov_cummunity">👉 Всё наше каммунити тут!👈</a>\n'
                                   f'Переходи в камунити если хочешь больше общения)',
                                   reply_to_message_id=message_id,
                                   parse_mode=ParseMode.HTML,
                                   disable_notification=True)
