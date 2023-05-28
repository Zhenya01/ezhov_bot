from telegram import Update
from telegram.ext import ContextTypes

import regs
from helpers_module import logger


async def forward_post(update:Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    logger.debug(f'Thread_id - {thread_id}, Posts_thread_id - {regs.ezhov_forum_threads["posts"]}')
    if thread_id == regs.ezhov_forum_threads['posts']:
        logger.debug(f'forward_post_triggered')
        context.bot.forward_message(update.message.chat_id,
                                    update.message.chat_id,
                                    update.message.message_id,
                                    message_thread_id=1)
