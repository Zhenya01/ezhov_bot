import asyncio

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import regs
from helpers_module import logger


async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    logger.debug(f'Thread_id - {thread_id}, Posts_thread_id - {regs.ezhov_forum_threads["posts"]}')
    threads = regs.zhenya_forum_threads
    if thread_id in [threads['posts'], threads['tiktoks'], threads['ezhov_news'],
                     threads['frontend_vlog'], threads['life']]:
        if update.effective_user.id not in [regs.ezhov_user_id, regs.zhenya_user_id, regs.ezhov_user_id]:
            return
        logger.debug('forwarding post to comments')
        await context.bot.forward_message(update.message.chat_id,
                                          update.message.chat_id,
                                          update.message.message_id)
        logger.debug('forwarding post to channel')
        await asyncio.sleep(3)
        msg = await context.bot.forward_message(regs.zhenya_channel_id,
                                          update.message.chat_id,
                                          update.message.message_id)
        await asyncio.sleep(3)
        forum_dict = {
            threads['posts']: 'постики',
            threads['tiktoks']: 'тиктоки',
            threads['ezhov_news']: 'новости',
            threads['frontend_vlog']: 'новости по программированию',
            threads['stream_time']: 'посты о стримах и их обсуждения',
            threads['life']: 'постики о жизни',
        }
        print(f'<a href = "t.me/ezhov_test_chat/{thread_id}">➡️остальные {forum_dict[thread_id]} тут⬅️</a>')
        await context.bot.send_message(regs.zhenya_channel_id,
                                       f'<a href = "t.me/ezhov_test_chat/{thread_id}">➡️остальные {forum_dict[thread_id]} тут⬅️</a>',
                                       reply_markup=InlineKeyboardMarkup([
                                           [
                                               InlineKeyboardButton('Перейти в обсуждение',
                                                                    url='t.me/ezhov_test_chat/1')
                                           ]
                                       ]),
                                       parse_mode=ParseMode.HTML)


async def forward_to_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # forward_thread_id = regs.ezhov_forum_threads['comments']
    # forward_channel_id = regs.ezhov_forum_id
    # forwarded_message_channel_id = regs.zdarovezhov_channel_id
    forward_thread_id = None
    forward_channel_id = regs.zhenya_forum_id
    forwarded_channel_id = regs.zhenya_channel_id
    if update.effective_chat.id == forwarded_channel_id:
        logger.debug(f'forwarding post from main channel')
        await context.bot.forward_message(forward_channel_id,
                                          update.effective_chat.id,
                                          update.effective_message.id,
                                          message_thread_id=forward_thread_id)
