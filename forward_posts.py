from telegram import Update
from telegram.ext import ContextTypes

import regs
from helpers_module import logger


async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    logger.debug(f'Thread_id - {thread_id}, Posts_thread_id - {regs.ezhov_forum_threads["posts"]}')
    if thread_id == regs.ezhov_forum_threads['posts']:
        logger.debug(f'forward_post_triggered')
        await context.bot.forward_message(update.message.chat_id,
                                          update.message.chat_id,
                                          update.message.message_id)


async def forward_to_comments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # forward_thread_id = regs.ezhov_forum_threads['comments']
    # forward_channel_id = regs.ezhov_forum_id
    # forwarded_message_channel_id = regs.zdarovezhov_channel_id
    forward_thread_id = None
    forward_channel_id = regs.zhenya_forum_id
    forwarded_channel_id = regs.zhenya_channel_id
    if update.effective_chat.id == forwarded_channel_id:
        logger.debug(f'forwarding post from main channel')
        await context.bot.forward_message(update.effective_chat.id,
                                          forward_channel_id,
                                          update.effective_message.id,
                                          message_thread_id=forward_thread_id)
