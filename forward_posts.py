from telegram import Update
from telegram.ext import ContextTypes

import regs


async def forward_post(update:Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if thread_id == regs.ezhov_forum_threads['posts']:
        context.bot.forward_message(update.message.chat_id,
                                    update.message.chat_id,
                                    update.message.message_id)
