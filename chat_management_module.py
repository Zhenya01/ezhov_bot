import datetime

import pytz
from telegram import Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import cfg
import database
import cfg

from logging_settings import logger

CHATS = cfg.config_data['CHATS']


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins_list = cfg.config_data['CHATS']['ADMINS_LIST'] + cfg.config_data['CHATS']['MODERATORS_LIST']
    print('STARTING MUTE. CHECKING ADMINS')
    if update.message.from_user.id in admins_list:
        print('IS_ADMIN. MUTING')
        if len(context.args) == 0:
            duration = 30
        else:
            duration = int(context.args[0])
        print(duration)
        points_to_deduct = duration
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
        database.subtract_points(mute_id, points_to_deduct)
    else:
        await update.message.delete()


async def send_muted_message(update: Update, context: ContextTypes.DEFAULT_TYPE, duration):
    muted_user = update.message.reply_to_message.from_user
    muted_name = muted_user.full_name
    muted_username = muted_user.username
    muted_id = muted_user.id
    muted_mention = f"@{muted_username} ({muted_name})" \
        if (
            muted_username != 'None' and muted_username is not None) else f'<a href="tg://user?id={muted_id}">{muted_name}</a>'
    if duration % 10 == 1 and duration % 100 != 11:
        word = "балл"
    elif 2 <= duration % 10 <= 4 and (duration % 100 < 10 or duration % 100 >= 20):
        word = "балла"
    else:
        word = "баллов"
    text = f'{muted_mention}, чел ты в муте на {duration} мин, так еще и потерял {duration} {word}. Заслужил.\nЗамутил: {update.effective_user.name}'
    print(text)
    message = await context.bot.send_message(update.effective_chat.id, text, parse_mode=ParseMode.HTML)
    moderation_group = CHATS['MODERATION_GROUP']
    until_time = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow")) + datetime.timedelta(minutes=duration)
    print(f'USER_INFO{cfg.UNBAN_CHATTER},{update.effective_chat.id},{muted_id}')
    muted_mod_text = f'<b>Мут участника:</b>\n' \
                     f'<b>Замучен</b> {muted_mention}\n' \
                     f'<b>Время:</b> {duration} мин. (до {datetime.datetime.strftime(until_time, "%m-%d-%Y, %H:%M")})'
    await context.bot.send_message(
        moderation_group,
        muted_mod_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('Размутить',
                                      callback_data=f'{cfg.UNBAN_CHATTER},{update.effective_chat.id},{muted_id}')]
            ]
        ))
    if 'muted_messages' not in context.bot_data.keys():
        context.bot_data['muted_messages'] = {}
    context.bot_data['muted_messages'][f'{cfg.UNBAN_CHATTER},{update.effective_chat.id},{muted_id}'] = muted_mod_text
    # message_id = message.message_id
    # context.application.job_queue.run_once(callback=delete_muted_message,
    #                                        when=60,
    #                                        data={'chat_id': update.effective_chat.id,
    #                                              'message_id': message_id})


async def unmute_chatter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.bot_data['muted_messages'][update.callback_query.data]
    del context.bot_data['muted_messages'][update.callback_query.data]
    callback_info = update.callback_query.data.split(',')
    chat_id = callback_info[1]
    user_id = callback_info[2]
    permissions = ChatPermissions().all_permissions()
    await context.bot.restrict_chat_member(chat_id, user_id, permissions)
    text += f'\n<i>Размучен модератором {update.effective_user.name}</i>'
    await context.bot.edit_message_text(text,
                                        update.effective_chat.id,
                                        update.effective_message.id,
                                        reply_markup=None,
                                        parse_mode=ParseMode.HTML)


async def delete_muted_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data['chat_id']
    message_id = context.job.data['message_id']
    await context.bot.delete_message(chat_id, message_id)


async def kick_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('KICK_FROM_GROUP_START')
    if update.effective_user.id not in cfg.config_data['GROUP_LIST']:
        await remove_join_left_message(update, context)
        message = await update.message.reply_photo(open('uhodi.png', 'rb'),
                                                    'Этот чат не чат, тут Eжов за сообщениями в группе следит')
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


async def remove_join_left_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug('Удаляем сообщение о заходе/выходе участника')
    await schedule_remove_rename_message(update, context)


async def schedule_remove_rename_message(update: Update,
                                         context: ContextTypes.DEFAULT_TYPE):
    logger.debug('Добавляем таск на удаление сообщения в job_queue')
    logger.debug(f'До удаления: chat_id - {update.effective_chat.id}\n'
                 f'             message_id - {update.effective_message.message_id}')
    context.application.job_queue.run_once(callback=remove_message,
                                           when=5,
                                           data={
                                               'chat_id_to_remove': update.effective_chat.id,
                                               'message_id_to_remove': update.effective_message.message_id})


async def remove_message(context: ContextTypes.DEFAULT_TYPE):
    logger.debug('Удаляем сообщение о переименовании канала/заходе участника')
    chat_id = context.job.data['chat_id_to_remove']
    message_id = context.job.data['message_id_to_remove']
    logger.debug(f'Во время удаления: chat_id - {chat_id}\n'
                 f'                   message_id - {message_id}')

    await context.bot.delete_message(chat_id, message_id)
