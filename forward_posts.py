from telegram import Update
from telegram.ext import ContextTypes

import regs
from helpers_module import logger


async def forward_post(update:Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f'forward_post_triggered')
    thread_id = update.message.message_thread_id
    logger.debug(f'Thread_id - {thread_id}, Posts_thread_id - {regs.ezhov_forum_threads["posts"]}')
    if thread_id == regs.ezhov_forum_threads['posts']:
        context.bot.forward_message(update.message.chat_id,
                                    update.message.chat_id,
                                    update.message.message_id)
