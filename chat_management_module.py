import datetime

import pytz
from telegram import Update, ChatPermissions
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import regs
from helpers_module import reformat_name, logger


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins_list = regs.admins_list + regs.moders_list
    print('STARTING MUTE. CHECKING ADMINS')
    if update.message.from_user.id in admins_list:
        print('IS_ADMIN. MUTING')
        if len(context.args) == 0:
            duration = 30
        else:
            duration = int(context.args[0])
        mute_id = update.message.reply_to_message.from_user.id
        until_date = datetime.datetime.now(tz=pytz.timezone('Europe/Moscow')) + datetime.timedelta(minutes=duration)
        permissions = ChatPermissions(can_send_messages=False)
        await context.bot.restrict_chat_member(update.effective_chat.id, mute_id,
                                         permissions, until_date)
        muted_message_id = update.message.reply_to_message.message_id
        await context.bot.delete_message(update.effective_chat.id, muted_message_id)
        muter_message_id = update.message.message_id
        await context.bot.delete_message(update.effective_chat.id, muter_message_id)
        await send_muted_message(update, context, duration)
    else:
        await update.message.delete()


async def send_muted_message(update: Update, context: ContextTypes.DEFAULT_TYPE, duration):
    muted_user = update.message.reply_to_message.from_user
    muted_name = muted_user.name
    muted_username = muted_user.username
    muted_id = muted_user.id
    muted_mention = f"\@{muted_username}" \
        if (
            muted_username != 'None' and muted_username is not None) else f'[{muted_name}](tg://user?id={muted_id})'
    muted_mention = reformat_name(muted_mention)
    text = f'{muted_mention}, чел ты в муте на {duration} мин\. Заслужил\.\nЗамутил: {reformat_name(update.effective_user.name)}'
    print(text)
    message = await context.bot.send_message(update.effective_chat.id, text, parse_mode=ParseMode.MARKDOWN_V2)
    message_id = message.message_id
    context.application.job_queue.run_once(callback=delete_muted_message,
                                           when=60,
                                           data={'chat_id': update.effective_chat.id,
                                                 'message_id': message_id})


async def delete_muted_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data['chat_id']
    message_id = context.job.data['message_id']
    await context.bot.delete_message(chat_id, message_id)


async def kick_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('KICK_FROM_GROUP')
    if update.effective_chat.id in [regs.zdarovezhov_group_id, regs.zhenya_group_id]:
        print('KICK_FROM_GROUP_START')
        if update.effective_user.id not in regs.group_list:
            message = await update.message.reply_photo(open('uhodi.png', 'rb'), 'Этот чат не чат, тут Eжов за сообщениями в группе следит')
            message_id = message.message_id
            # message_id = await update.message.reply_text('Этот чат не чат, тут ежов за сообщениями в группе следит').message_id
            context.bot_data['user_to_kick'] = update.message.from_user.id
            context.bot_data['chat_to_kick_from'] = update.message.chat.id
            context.application.job_queue.run_once(callback=kick_after_wait,
                                                   when=datetime.timedelta(seconds=10),
                                                   name='kick_after_wait',
                                                   data={'user_to_kick': update.message.from_user.id,
                                                         'chat_to_kick_from': update.message.chat.id,
                                                         'message_to_delete': message_id})


async def kick_after_wait(context: ContextTypes.DEFAULT_TYPE):
    # await asyncio.sleep(15)
    chat_id = context.job.data['chat_to_kick_from']
    user_id = context.job.data['user_to_kick']
    message_id = context.job.data['message_to_delete']
    await context.bot.unban_chat_member(chat_id, user_id)
    await context.bot.delete_message(chat_id, message_id)


async def remove_join_left_message(update:Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug('Удаляем сообщение о заходе/выходе участника')
    await context.bot.delete_message(update.message.chat_id, update.message.message_id)
