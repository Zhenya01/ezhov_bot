import datetime
import uuid
from pprint import pprint

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, \
    ForceReply
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext

import cfg
import database
import cfg
from database import Reward
from database import update_user_info
# Points management states
from cfg import ADD_OR_SUBTRACT_POINTS, ADD_POINTS, SUBTRACT_POINTS, ENTER_POINTS_MANAGEMENT, SELECT_USER
from cfg import (SELECT_REWARD_TO_EDIT, PICK_ACTION, EDIT_REWARD, ADDING_REWARD, CHANGE_NAME,
                 CHANGE_DESCRIPTION, CHANGE_PRICE, REMOVE_REWARD, BACK_TO_REWARDS, CANCEL_BUTTON,
                 CHANGE_NUMBER_LEFT, CHANGE_PERSON_TOTAL_LIMIT, CHANGE_TOTAL_COOLDOWN, CHANGE_PERSON_COOLDOWN)
from cfg import (SEE_REWARDS, SEE_POINTS_INFO, USER_POINTS_MENU, WAITING_FOR_REWARD_DECISION,
                 SELECT_REWARD_TO_BUY, BUY_REWARD)
from cfg import ADD_REWARD_NAME, ADD_REWARD_DESCRIPTION, ADD_REWARD_PRICE
from cfg import EDIT, VIEW
CHATS = cfg.config_data['CHATS']

# -----------------------------------------------------Админ---------------------------------------------------------- #

@update_user_info
async def points_manual_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_list = await database.get_users()
    if users_list is None:
        await context.bot.send_message(update.effective_chat.id,
                                       'Что-то пошло не так, либо в базе данных нет участников. Обращаться к Женьку')
        return ConversationHandler.END
    users_dict = {}
    for user in users_list:
        if user['nickname'] is not None:
            name = f'{user["nickname"]} ({user["full_name"]})'
        else:
            name = user["full_name"]
        users_dict[name] = user["user_id"]
    users_keyboard = [['Отменить']]
    for user in users_dict.keys():
        users_keyboard.append([user])
    context.user_data['users_dict'] = users_dict
    await context.bot.send_message(update.effective_chat.id,
                                   'Выбери участника камути для изменения его баланса баллов:',
                                   reply_markup=ReplyKeyboardMarkup(users_keyboard))
    return SELECT_USER


async def show_user_points_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    users_dict = context.user_data['users_dict']
    if name not in users_dict.keys():
        await context.bot.send_message(update.effective_chat.id,
                                       'Что-то пошло не так. Этого пользователя нет в списке пользователей камунити. Выбери из списка, либо отмени выбор, если передумал')
        return SELECT_USER
    user_id = users_dict[name]
    user = await database.get_user_info(user_id)
    if user is None:
        await context.bot.send_message(update.effective_chat.id,
                                       'Что-то пошло не так. Этого пользователя нет в списке пользователей камунити. Выбери из списка, либо отмени выбор, если передумал')
        return SELECT_USER
    await context.bot.send_message(update.effective_chat.id,
                                   f'Пользователь {name}. {"Звание - " if user["title"] is not None else ""} {user["title"]+"." if user["title"] is not None else ""}'
                                   f'Количество баллов - {user["tg_points"]}. Добавить или отнять баллы у пользователя?',
                                   reply_markup=ReplyKeyboardMarkup([['➕ Добавить'], ['➖ Отнять'], ['Отменить']],
                                                                    resize_keyboard=True))
    context.user_data['points_management_user_id'] = user["user_id"]
    return ADD_OR_SUBTRACT_POINTS


async def choose_points_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == 'Отменить':
        await context.bot.send_message(update.effective_chat.id,
                                       'Начисление/вычитание баллов отменено',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    action = update.message.text[2:].lower()
    context.user_data['action'] = action
    print(context.user_data['action'])
    await context.bot.send_message(update.effective_chat.id,
                                   f'Введите количество баллов, которые вы хотите {action}',
                                   reply_markup=ReplyKeyboardRemove())
    if action == 'добавить':
        return ADD_POINTS
    else:
        return SUBTRACT_POINTS


async def add_or_subtract_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data['action']
    points = update.message.text
    user_id = update.effective_user.id
    if not points.isdigit():
        await context.bot.send_message(update.effective_chat.id,
                                       f'Ваш ответ - не число. Введите количество баллов числом',
                                       reply_markup=ReplyKeyboardRemove())
        if action == 'добавить':
            return ADD_POINTS
        else:
            return SUBTRACT_POINTS
    points = int(points)
    user_id = context.user_data['points_management_user_id']
    user = await database.get_user_info(user_id)
    if user['nickname'] is not None:
        name = f'{user["nickname"]} ({user["full_name"]})'
    else:
        name = user["full_name"]
    if action == 'добавить':
        database.add_points(user_id, points)
        total_points = user['tg_points'] + points
        await context.bot.send_message(update.effective_chat.id,
                                       f'На счёт пользователя {name} добавлено {points} балла/ов. Нынешний баланс - {total_points}',
                                       reply_markup=ReplyKeyboardRemove())
    else:
        database.subtract_points(user_id, points)
        total_points = user['tg_points'] - points
        await context.bot.send_message(update.effective_chat.id,
                                       f'Со счёта пользователя {name} снято {points} балла/ов. Нынешний баланс - {total_points}',
                                       reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def rewards_command_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['rewards_reason'] = EDIT
    result = await show_rewards(update, context)
    return result

@update_user_info
async def show_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rewards_list = await database.get_rewards()
    if rewards_list is None:
        await context.bot.send_message(update.effective_chat.id,
                                       'Что-то пошло не так, либо в базе данных нет доступных наград. Обращаться к Женьку')
        return ConversationHandler.END
    rewards_dict = {}
    for reward in rewards_list:
        name = reward['name']
        rewards_dict[name] = reward["reward_id"]
    reason = context.user_data['rewards_reason']
    if reason == str(EDIT):
        rewards_keyboard = [[CANCEL_BUTTON], [cfg.ADD_REWARD_BUTTON]]
    else:
        rewards_keyboard = [[CANCEL_BUTTON]]
    for reward in rewards_dict.keys():
        rewards_keyboard.append([reward])
    context.user_data['rewards_dict'] = rewards_dict
    await context.bot.send_message(update.effective_chat.id,
                                   'Выбери награду для просмотра/изменения:',
                                   reply_markup=ReplyKeyboardMarkup(rewards_keyboard))
    if reason == str(EDIT):
        return SELECT_REWARD_TO_EDIT
    elif reason == str(VIEW):
        return SELECT_REWARD_TO_BUY

async def generate_reward_text(reward: Reward, is_extended=False):
    keyboard = [
        [InlineKeyboardButton('❌ Отменить', callback_data='cancel')],
        [InlineKeyboardButton('➖ Удалить', callback_data='delete')],
        [
            InlineKeyboardButton('✏️ Название', callback_data='edit_name'),
            InlineKeyboardButton('✏️ Описание', callback_data='edit_description'),
            InlineKeyboardButton('✏️ Цена', callback_data='edit_price')
        ]
    ]
    if is_extended:
        keyboard += (
            [
             [InlineKeyboardButton('Скрыть лимиты ⤴️', callback_data='hide_limits_info')],
             [InlineKeyboardButton('Остаток', callback_data='edit_number_left')],
             [InlineKeyboardButton("➖", callback_data='subtract_number_left'),
              InlineKeyboardButton(f'{reward.number_left}', callback_data='edit_number_left'),
              InlineKeyboardButton("➕", callback_data='add_number_left')],
             [InlineKeyboardButton('Лимит на человека', callback_data='edit_person_total_limit')],
             [InlineKeyboardButton("◀️", callback_data='subtract_person_total_limit'),
              InlineKeyboardButton(f'{reward.person_total_limit}', callback_data='edit_person_total_limit'),
              InlineKeyboardButton("▶️", callback_data='add_person_total_limit')],
             [InlineKeyboardButton('Кулдаун на человека', callback_data='edit_person_cooldown')],
             [InlineKeyboardButton("◀️", callback_data='subtract_person_cooldown'),
              InlineKeyboardButton(f'{reward.person_cooldown}', callback_data='edit_person_cooldown'),
              InlineKeyboardButton("▶️", callback_data='add_person_cooldown')],
             [InlineKeyboardButton('Кулдаун на награду', callback_data='edit_total_cooldown')],
             [InlineKeyboardButton("◀️", callback_data='subtract_total_cooldown'),
              InlineKeyboardButton(f'{reward.total_cooldown}', callback_data='edit_total_cooldown'),
              InlineKeyboardButton("▶️", callback_data='add_total_cooldown')]
             ]
                     )
    else:
        keyboard.append([InlineKeyboardButton('Лимиты ⤵️', callback_data='extend_limits_info')])
    keyboard.append([InlineKeyboardButton('💾 Сохранить', callback_data='save_changes')])
    text = f'<b>Награда:</b> <code>{reward.name}</code>\n' \
           f'<b>Описание: </b> <code>{reward.description}</code>\n' \
           f'<b>Цена: </b> {reward.price} баллов.\n'

    return text, keyboard

@update_user_info
async def show_reward(update: Update, context: ContextTypes.DEFAULT_TYPE, reward=None):
    if update.message.text == cfg.ADD_REWARD_BUTTON:
        result = await start_adding_reward(update, context)
        return result
    if reward is None:
        if update.message.text == CANCEL_BUTTON:
            await context.bot.send_message(update.effective_chat.id,
                                           'Выбор награды завершён',
                                           reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        name = update.message.text
        rewards_dict = context.user_data['rewards_dict']
        print(rewards_dict)
        print(rewards_dict.keys())
        if name not in rewards_dict.keys():
            await context.bot.send_message(update.effective_chat.id,
                                           'Что-то пошло не так. Этой награды нет в списке наград. Выбери из списка, либо отмени выбор, если передумал')
            return SELECT_REWARD_TO_EDIT
        reward_id = rewards_dict[name]
        reward = await database.get_reward_info(reward_id)
        if reward is None:
            await context.bot.send_message(update.effective_chat.id,
                                           'Что-то пошло не так. Этой награды нет в списке наград. Выбери из списка, либо отмени выбор, если передумал')
            return SELECT_REWARD_TO_EDIT
    text, keyboard = await generate_reward_text(reward, is_extended=False)
    context.user_data['is_extended'] = False
    # reply_markup = [[CHANGE_NAME], [CHANGE_DESCRIPTION], [CHANGE_PRICE], [REMOVE_REWARD], [BACK_TO_REWARDS]]
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f'Изменение настроек для награды "{reward.name}"',
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=ReplyKeyboardRemove())
    await context.bot.send_message(update.effective_chat.id,
                                   text,
                                   reply_markup=InlineKeyboardMarkup(keyboard),
                                   parse_mode=ParseMode.HTML)
    context.user_data['managed_reward'] = reward
    return PICK_ACTION

@update_user_info
async def reward_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reward = context.user_data['managed_reward']
    if update.callback_query.data == 'extend_limits_info':
        context.user_data['is_extended'] = True
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'hide_limits_info':
        context.user_data['is_extended'] = False
        text, keyboard = await generate_reward_text(reward, is_extended=False)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'subtract_number_left':
        if reward.number_left == 0:
            await update.callback_query.answer('❌ Отстаток нельзя установить ниже 0')
            return
        else:
            reward.number_left -= 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'add_number_left':
        reward.number_left += 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))

    elif update.callback_query.data == 'subtract_person_total_limit':
        if reward.person_total_limit == 0:
            await update.callback_query.answer('❌ Лимит на человека нельзя установить ниже 0')
            return
        else:
            reward.person_total_limit -= 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'add_person_total_limit':
        reward.person_total_limit += 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))

    elif update.callback_query.data == 'subtract_person_cooldown':
        if reward.person_cooldown == 0:
            await update.callback_query.answer('❌ Кулдаун нельзя установить ниже 0')
            return
        else:
            reward.person_cooldown -= 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'add_person_cooldown':
        reward.person_cooldown += 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'subtract_total_cooldown':
        if reward.total_cooldown == 0:
            await update.callback_query.answer('❌ Кулдаун нельзя установить ниже 0')
            return
        else:
            reward.total_cooldown -= 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'add_total_cooldown':
        reward.total_cooldown += 1
        text, keyboard = await generate_reward_text(reward, is_extended=True)
        await update.callback_query.message.edit_text(text,
                                                      parse_mode=ParseMode.HTML,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query.data == 'edit_name':
        await update.callback_query.message.reply_text(f'Введи новое название для награды (старое название: <code>{reward.name}</code>)',
                                                       reply_markup=ForceReply(input_field_placeholder='Название'),
                                                       parse_mode=ParseMode.HTML)
        context.user_data['reward_message_id'] = update.effective_message.message_id
        context.user_data['reward_action'] = CHANGE_NAME
        return EDIT_REWARD

    elif update.callback_query.data == 'edit_description':
        await update.callback_query.message.reply_text(f'Введи новое описание для награды (старое описание: <code>{reward.description}</code>)',
                                                       reply_markup=ForceReply(input_field_placeholder='Описание'),
                                                       parse_mode=ParseMode.HTML)
        context.user_data['reward_message_id'] = update.effective_message.message_id
        context.user_data['reward_action'] = CHANGE_DESCRIPTION
        return EDIT_REWARD
    elif update.callback_query.data == 'edit_price':
        await update.callback_query.message.reply_text(f'Введи новую цену для награды',
                                                       reply_markup=ForceReply(input_field_placeholder='Цена'),
                                                       parse_mode=ParseMode.HTML)
        context.user_data['reward_message_id'] = update.effective_message.message_id
        context.user_data['reward_action'] = CHANGE_PRICE
        return EDIT_REWARD
    elif update.callback_query.data == 'edit_number_left':
        await update.callback_query.message.reply_text(f'Введи новый остаток для награды',
                                                       reply_markup=ForceReply(input_field_placeholder='Остаток'),
                                                       parse_mode=ParseMode.HTML)
        context.user_data['reward_message_id'] = update.effective_message.message_id
        context.user_data['reward_action'] = CHANGE_NUMBER_LEFT
        return EDIT_REWARD
    elif update.callback_query.data == 'edit_person_total_limit':
        await update.callback_query.message.reply_text(f'Введи новый лимит на участника для награды',
                                                       reply_markup=ForceReply(input_field_placeholder='Лимит'),
                                                       parse_mode=ParseMode.HTML)
        context.user_data['reward_message_id'] = update.effective_message.message_id
        context.user_data['reward_action'] = CHANGE_PERSON_TOTAL_LIMIT
        return EDIT_REWARD
    elif update.callback_query.data == 'edit_person_cooldown':
        await update.callback_query.message.reply_text(f'Введи новый кулдаун (на человека) для награды',
                                                       reply_markup=ForceReply(input_field_placeholder='Кулдаун'),
                                                       parse_mode=ParseMode.HTML)
        context.user_data['reward_message_id'] = update.effective_message.message_id
        context.user_data['reward_action'] = CHANGE_PERSON_COOLDOWN
        return EDIT_REWARD
    elif update.callback_query.data == 'edit_total_cooldown':
        await update.callback_query.message.reply_text(f'Введи новый кулдаун (общий) для награды',
                                                       reply_markup=ForceReply(input_field_placeholder='Кулдаун'),
                                                       parse_mode=ParseMode.HTML)
        context.user_data['reward_message_id'] = update.effective_message.message_id
        context.user_data['reward_action'] = CHANGE_TOTAL_COOLDOWN
        return EDIT_REWARD
    elif update.callback_query.data == 'save_changes':
        group_id = CHATS['FORUM_GROUP']
        unupdated_reward = await database.get_reward_info(reward.reward_id)
        if reward.number_left > unupdated_reward.number_left:
            await context.bot.send_message(group_id, f'Добавилось количество награды "{reward.name}". Бегом покупать!!')
        text, markup = await generate_reward_text(reward)
        reward.update_in_db()
        await update.callback_query.message.edit_text('\n'.join(text.split('\n')[:-1]) + '\n\n<i>Изменения сохранены</i>',
                                                      parse_mode=ParseMode.HTML)
        context.user_data['rewards_reason'] = EDIT
        result = await show_rewards(update, context)
        return result
    elif update.callback_query.data == 'cancel':
        reward = await database.get_reward_info(reward.reward_id)
        # TODO обработать исключения
        text, markup = await generate_reward_text(reward)
        await update.callback_query.message.edit_text(
            '\n'.join(text.split('\n')[:-1]) + '\n\n<i>Редактирование отменено. Все изменения отменены</i>',
            parse_mode=ParseMode.HTML)
        context.user_data['rewards_reason'] = EDIT
        result = await show_rewards(update, context)
        return result
    elif update.callback_query.data == 'delete':
        text, markup = await generate_reward_text(reward)
        reward.delete_from_db()
        await update.callback_query.message.edit_text(
            '\n'.join(text.split('\n')[:-1]) + '\n\n<i>Награда удалена</i>',
            parse_mode=ParseMode.HTML)
        context.user_data['rewards_reason'] = EDIT
        result = await show_rewards(update, context)
        return result


async def wrong_action_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id,
                                   'Сначала сохраните настройки награды, либо отмените изменение')


async def save_new_reward_char(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data['reward_action']
    reward = context.user_data['managed_reward']
    if not isinstance(reward, Reward):
        reward = await database.get_reward_info(reward['reward_id'])
        context.user_data['managed_reward'] = reward
    if action == CHANGE_NAME:
        reward.name = update.message.text
        # reward.update_in_db()
        edited_string = f'Имя награды изменено на {update.message.text}.'
    elif action == CHANGE_DESCRIPTION:
        reward.description = update.message.text
        # reward.update_in_db()
        edited_string = f'Описание награды изменено на {update.message.text}.'
    elif action == CHANGE_PRICE:
        if not update.message.text.isdigit():
            await context.bot.send_message(update.effective_chat.id,
                                           f'Введите цену награды в баллах (число)',
                                           reply_markup=ReplyKeyboardRemove())
            return EDIT_REWARD
        reward.price = int(update.message.text)
        # reward.update_in_db()
        edited_string = f'Цена награды изменена на {update.message.text} б.'
    elif action == CHANGE_NUMBER_LEFT:
        if not update.message.text.isdigit():
            await context.bot.send_message(update.effective_chat.id,
                                           f'Введите остаток награды числом',
                                           reply_markup=ReplyKeyboardRemove())
            return EDIT_REWARD
        reward.number_left = int(update.message.text)
        # reward.update_in_db()
        edited_string = f'Остаток награды изменен на {update.message.text}.'
    elif action == CHANGE_PERSON_TOTAL_LIMIT:
        if not update.message.text.isdigit():
            await context.bot.send_message(update.effective_chat.id,
                                           f'Введите лимит на человека числом (шт.)',
                                           reply_markup=ReplyKeyboardRemove())
            return EDIT_REWARD
        reward.person_total_limit = int(update.message.text)
        # reward.update_in_db()
        edited_string = f'Лимит на человека изменен на {update.message.text}.'
    elif action == CHANGE_PERSON_COOLDOWN:
        if not update.message.text.isdigit():
            await context.bot.send_message(update.effective_chat.id,
                                           f'Введите кулдаун (на человека) награды числом (дни)',
                                           reply_markup=ReplyKeyboardRemove())
            return EDIT_REWARD
        reward.person_cooldown = int(update.message.text)
        # reward.update_in_db()
        edited_string = f'Остаток кулдаун (на человека) награды изменен на {update.message.text}.'
    else:
        if not update.message.text.isdigit():
            await context.bot.send_message(update.effective_chat.id,
                                           f'Введите кулдацун (общий) награды числом (дни )',
                                           reply_markup=ReplyKeyboardRemove())
            return EDIT_REWARD
        reward.total_cooldown = int(update.message.text)
        # reward.update_in_db()
        edited_string = f'Кулдаун (общий) награды изменен на {update.message.text}.'
    await context.bot.send_message(update.effective_chat.id,
                                   edited_string)
    message_id = context.user_data['reward_message_id']
    text, markup = await generate_reward_text(reward, context.user_data['is_extended'])
    await context.bot.edit_message_text(text, update.effective_chat.id, message_id,
                                        parse_mode=ParseMode.HTML,
                                        reply_markup=InlineKeyboardMarkup(markup))
    return PICK_ACTION


async def start_adding_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id,
                                   'Введи название награды:',
                                   reply_markup=ReplyKeyboardMarkup([[CANCEL_BUTTON]],
                                                                    resize_keyboard=True))
    return ADD_REWARD_NAME


async def reward_name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL_BUTTON:
        await context.bot.send_message(update.effective_chat.id,
                                       'Создание награды отменено',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    reward_name = update.message.text
    reward = Reward(reward_name)
    context.user_data['reward_to_add'] = reward
    await context.bot.send_message(update.effective_chat.id,
                                   f'Название награды сохранено: "{reward_name}". Введи описание награды:',
                                   reply_markup=ReplyKeyboardMarkup([[CANCEL_BUTTON]],
                                                                    resize_keyboard=True))
    return ADD_REWARD_DESCRIPTION


async def reward_description_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL_BUTTON:
        await context.bot.send_message(update.effective_chat.id,
                                       'Создание награды отменено',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    reward_description = update.message.text
    reward = context.user_data['reward_to_add']
    reward.description = reward_description
    await context.bot.send_message(update.effective_chat.id,
                                   f'Описание награды сохранено: "{reward_description}". Введи цену награды:',
                                   reply_markup=ReplyKeyboardMarkup([[CANCEL_BUTTON]],
                                                                    resize_keyboard=True))
    return ADD_REWARD_PRICE


async def reward_price_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL_BUTTON:
        await context.bot.send_message(update.effective_chat.id,
                                       'Создание награды отменено',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    reward_price = update.message.text
    if not reward_price.isdigit():
        await context.bot.send_message(update.effective_chat.id,
                                       f'Цена введена не числом. Введи цену в баллах:',
                                       reply_markup=ReplyKeyboardMarkup([[CANCEL_BUTTON]],
                                                                        resize_keyboard=True))
        return ADD_REWARD_PRICE
    reward = context.user_data['reward_to_add']
    reward.price = reward_price
    await context.bot.send_message(update.effective_chat.id,
                                   f'Цена награды сохранена: {reward_price}',
                                   reply_markup=ReplyKeyboardMarkup([[CANCEL_BUTTON]],
                                                                    resize_keyboard=True))
    defaults = cfg.config_data['REWARDS']
    number_left = 999
    person_total_limit = defaults['DEFAULT_PERSON_TOTAL_LIMIT']
    person_cooldown = defaults['DEFAULT_PERSON_COOLDOWN']
    total_cooldown = defaults['DEFAULT_TOTAL_COOLDOWN']

    reward.number_left = number_left
    reward.person_total_limit = person_total_limit
    reward.person_cooldown = person_cooldown
    reward.total_cooldown = total_cooldown
    reward.put_to_db()
    await context.bot.send_message(update.effective_chat.id,
                                   f'Награда добавлена. Теперь настрой лимиты награды:')
    result = await show_reward(update, context, reward)
    return result


# ------------------------------------------------Участники----------------------------------------------------------- #
@update_user_info
async def add_points_for_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO поменять на prestige level
    for_limit = False
    points_to_reward = int(cfg.BASE_COMMENT_POINTS) + (int(cfg.PRESTIGE_LEVEL_ADDED_MULTIPLIER) * 1)
    if update.message.sticker is not None:
        for_limit = True
    elif update.message.text is not None:
        symbols_number = len(update.effective_message.text.strip().split(' '))
        if symbols_number >= 10:
            database.add_points(update.effective_user.id, points_to_reward)
            print('POINTS ADDED')
            return
    else:
        for_limit = False
    pprint(update.effective_message)
    if not for_limit:
        database.add_points(update.effective_user.id, points_to_reward)
        print('POINTS ADDED')
    else:
        if 'last_flood_time' not in context.user_data.keys():
            print('LAST FLOOD TIME NOT IN DATA')
            database.add_points(update.effective_user.id, points_to_reward)
            print('POINTS ADDED')
            context.user_data['last_flood_time'] = datetime.datetime.now()
            return
        last_flood_time = context.user_data['last_flood_time']
        print(f'LAST FLOOD TIME - {last_flood_time}')
        time_from_last = datetime.datetime.now() - last_flood_time
        if time_from_last >= datetime.timedelta(seconds=30):
            database.add_points(update.effective_user.id, points_to_reward)
            print('POINTS ADDED')
            context.user_data['last_flood_time'] = datetime.datetime.now()
        else:
            print('POINTS NOT ADDED')


@database.update_user_info
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = await database.get_user_info(user_id)
    user_point = int(user['tg_points'])
    if user_point % 10 == 1 and user_point % 100 != 11:
        word = "балл"
    elif 2 <= user_point % 10 <= 4 and (user_point % 100 < 10 or user_point % 100 >= 20):
        word = "балла"
    else:
        word = "баллов"
    await context.bot.send_message(update.effective_chat.id,
                                   f'Добро пожаловать в модуль управления баллами!\n'
                                   f'<b>Твой баланс:</b> {int(user["tg_points"])} {word}.\n'
                                   f'Здесь можно посмотреть и приобрести доступные награды или посмотреть подробную '
                                   f'информацию о баллах и их способах получения',
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=ReplyKeyboardMarkup([[SEE_REWARDS], [SEE_POINTS_INFO], [CANCEL_BUTTON]],
                                                                    resize_keyboard=True))
    context.user_data['points_management_user_id'] = user["user_id"]
    return USER_POINTS_MENU


@update_user_info
async def points_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == CANCEL_BUTTON:
        await context.bot.send_message(update.effective_chat.id,
                                       'Вы вышли из меню управления баллами',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    elif update.effective_message.text == SEE_POINTS_INFO:
        text = ('<b>Что такое баллы, почему и зачем они:</b>\n'
                '1 балл камунити - это одно твое сообщение в группе (в основном так, но есть и другие способы получения).\n'
                'Баллы созданы потому что я худший стример. Мало стримлю, не зарабатываю на вас, а наоборот трачу на вас 🤦‍♂️\n'
                'За баллы канала ты сможешь получать всякие ништяки, смотри в наградах что есть сейчас \n'
                '<b>Существующие способы набора баллов</b>:\n'
                '  1 балл за 1 сообщение\n' 
                '  10 баллов за 1 тик-ток\n'
                '  100 баллов за супертикток\n'
                '<b>Вычитаются баллы </b>за мут и за покупку награды\n'
                'Это еще не все способы получения и потери баллов :) Ведётся активное продумывание и разработка')
        await context.bot.send_message(update.effective_chat.id,
                                       text,
                                       parse_mode=ParseMode.HTML)
    else:
        context.user_data['rewards_reason'] = cfg.VIEW
        return_value = await show_rewards(update, context)
        return return_value

@update_user_info
async def user_chose_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL_BUTTON:
        result = await points(update, context)
        return result
    name = update.message.text
    rewards_dict = context.user_data['rewards_dict']
    print(rewards_dict)
    print(rewards_dict.keys())
    if name not in rewards_dict.keys():
        await context.bot.send_message(update.effective_chat.id,
                                       'Что-то пошло не так. Этой награды нет в списке наград. Выбери из списка, либо отмени выбор, если передумал')
        return SELECT_REWARD_TO_BUY
    reward_id = rewards_dict[name]
    reward = await database.get_reward_info(reward_id)
    if reward is None:
        await context.bot.send_message(update.effective_chat.id,
                                       'Что-то пошло не так. Этой награды нет в списке наград. Выбери из списка, либо отмени выбор, если передумал')
        return SELECT_REWARD_TO_BUY
    latest_reward_of_type = await database.get_latest_reward_by_id(reward.reward_id)
    total_cooldown_passed = latest_reward_of_type is None or (latest_reward_of_type is not None and (datetime.datetime.now() - latest_reward_of_type['purchase_time'] > datetime.timedelta(days=reward.total_cooldown)))
    latest_user_reward_of_type = await database.get_latest_ur_by_id(reward.reward_id, update.effective_user.id)
    total_user_cooldown_passed = latest_user_reward_of_type is None or (latest_user_reward_of_type is not None and (datetime.datetime.now() - latest_reward_of_type['purchase_time'] > datetime.timedelta(days=reward.person_cooldown)))
    user_rewards_count = await database.get_user_reward_count(reward_id, update.effective_user.id)
    user_rewards_count = user_rewards_count['count']
    has_user_limit_left = (user_rewards_count < reward.person_total_limit) if reward.person_total_limit != 0 else True
    number_left = reward.number_left > 0
    if total_cooldown_passed and total_user_cooldown_passed and has_user_limit_left and number_left:
        await context.bot.send_message(update.effective_chat.id,
                                       f'<b>Награда:</b> {name}\n'
                                       f'<b>Описание: </b> {reward.description}\n'
                                       f'<b>Цена: </b> {reward.price} баллов.\n'
                                       f'\nКупить?',
                                       # f'\n<i>Покупка наград временно не доступна</i>',
                                       reply_markup=ReplyKeyboardMarkup([[BUY_REWARD], [BACK_TO_REWARDS]],
                                                                        resize_keyboard=True),
                                       parse_mode=ParseMode.HTML)
        # return SELECT_REWARD_TO_BUY
        context.user_data['managed_reward'] = reward
        return WAITING_FOR_REWARD_DECISION
    else:
        async def exit_with_limit(text):
            await context.bot.send_message(update.effective_chat.id,
                                           f'<b>Награда:</b> {name}\n'
                                           f'<b>Описание: </b> {reward.description}\n'
                                           f'<b>Цена: </b> {reward.price} баллов.\n',
                                           parse_mode=ParseMode.HTML)
            await context.bot.send_message(update.effective_chat.id,
                                           text)
            await show_rewards(update, context)

        if not number_left:
            state = await exit_with_limit(
                'Эта награда временно распродана, но я дам знать, когда она появится в наличии')
            return state
        elif not total_user_cooldown_passed:
            latest_bought_time = latest_user_reward_of_type["purchase_time"].strftime('%Y-%m-%d %H:%M:%S')
            cooldown_end_time = (latest_user_reward_of_type["purchase_time"] + datetime.timedelta(
                days=reward.person_cooldown)).strftime('%Y-%m-%d %H:%M:%S')
            state = await exit_with_limit(
                f'Сейчас не можешь взять эту награду, потому что на неё действует твой персональный '
                f'кулдаун {reward.person_cooldown} дней. В последний раз ты её брал {latest_bought_time} дней назад. '
                f'Подождем до {cooldown_end_time}')
            return state
        elif not total_cooldown_passed:
            latest_bought_time = latest_reward_of_type["purchase_time"].strftime('%Y-%m-%d %H:%M:%S')
            cooldown_end_time = (latest_reward_of_type["purchase_time"] + datetime.timedelta(days=reward.total_cooldown)).strftime('%Y-%m-%d %H:%M:%S')
            state = await exit_with_limit(
                f'Эта награда сейчас недоступна из-за общего времени ожидания {reward.total_cooldown} дней. '
                f'Последний раз её взяли {latest_bought_time}. Ждем до {cooldown_end_time}')
            return state
        elif not has_user_limit_left:
            state = await exit_with_limit(
                f'К сожалению, сейчас нельзя взять эту награду, потому что ты достиг(ла) своего личного лимита в {reward.person_total_limit} шт.')
            return state

@update_user_info
async def reward_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_TO_REWARDS:
        result = await show_rewards(update, context)
        return result
    else:
        reward = context.user_data['managed_reward']
        if not isinstance(reward, Reward):
            reward = await database.get_reward_info(reward['reward_id'])
            context.user_data['managed_reward'] = reward
        user_info = await database.get_user_info(update.effective_user.id)
        points_balance = user_info['tg_points']
        if points_balance < reward.price:
            await context.bot.send_message(update.effective_chat.id,
                                           'На вашем счету недостаточно баллов')
            result = await show_rewards(update, context)
            return result
        user_info = await database.get_user_info(update.effective_user.id)
        if user_info['nickname'] is not None:
            name = f'{user_info["nickname"]} (<a href="tg://user?id={user_info["user_id"]}">{user_info["full_name"]}</a>)'
        else:
            name = f'<a href="tg://user?id={user_info["user_id"]}">{user_info["full_name"]}</a>'
        points = reward.price
        if points % 10 == 1 and points % 100 != 11:
            word = "балл"
        elif 2 <= points % 10 <= 4 and (points % 100 < 10 or points % 100 >= 20):
            word = "балла"
        else:
            word = "баллов"
        result = await database.add_user_reward(update.effective_user.id,
                                                reward.reward_id)
        ur_id = result[0]
        database.subtract_points(update.effective_user.id,
                                 reward.price)
        reward.number_left -= 1
        reward.update_in_db()
        threads = CHATS['FORUM_THREADS']
        group_id = CHATS['FORUM_GROUP']
        await context.bot.send_message(group_id,
                                       f'Ура! {name} приобрёл награду "{reward.name}"',
                                       message_thread_id=threads['comments'],
                                       parse_mode=ParseMode.HTML)
        await context.bot.send_message(CHATS["MODERATION_GROUP"],
                                       f'<b>Куплена награда:</b>\n'
                                       f'<b>Пользователь:</b> {name}\n'
                                       f'<b>Награда:</b> {reward.name}\n'
                                       f'<b>Цена:</b> {points} {word}',
                                       parse_mode=ParseMode.HTML,
                                       reply_markup=InlineKeyboardMarkup(
                                           [[InlineKeyboardButton('Принять',
                                                                  callback_data=f'{cfg.APPROVE_REWARD},{ur_id}'),
                                             InlineKeyboardButton('Отклонить',
                                                                  callback_data=f'{cfg.DECLINE_REWARD},{ur_id}')]
                                            ]
                                       )
                                       )
        msg = await context.bot.send_message(update.effective_chat.id,
                                             f'<b>Куплена награда:</b>\n'
                                             f'{reward.name}\n'
                                             f'<b>Цена:</b> {points} {word}\n',
                                             parse_mode=ParseMode.HTML)
        message_id = msg.message_id
        await database.add_ur_message_id(ur_id, message_id)
        result = await show_rewards(update, context)
        return result

@update_user_info
async def reward_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback_info = update.callback_query.data.split(',')
    ur_id = callback_info[1]
    user_reward = await database.get_user_reward_by_id(ur_id)
    if user_reward is not None:
        reward_id = user_reward['reward_id']
        reward = await database.get_reward_info(reward_id)
        user_info = await database.get_user_info(user_reward["user_id"])
        if user_info['nickname'] is not None:
            name = f'{user_info["nickname"]} (<a href="tg://user?id={user_info["user_id"]}">{user_info["full_name"]}</a>)'
        else:
            name = f'<a href="tg://user?id={user_info["user_id"]}">{user_info["full_name"]}</a>'
        points = reward.price
        if callback_info[0] == str(cfg.DECLINE_REWARD):
            if points % 10 == 1 and points % 100 != 11:
                word = "балл"
            elif 2 <= points % 10 <= 4 and (points % 100 < 10 or points % 100 >= 20):
                word = "балла"
            else:
                word = "баллов"
            print(points)
            database.add_points(user_info['user_id'], points)
            mention = f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.full_name}</a>' \
                if update.effective_user.id is not None else f'{update.effective_user.full_name}'
            await database.reject_user_reward(ur_id)
            await context.bot.edit_message_text(
                f'<b>Куплена награда:</b>\n'
                f'{reward.name}\n'
                f'<b>Пользователь:</b> {name}\n'
                f'<b>Цена:</b> {points} {word}\n\n'
                f'<i>Награда отменена модератором {mention}</i>',
                update.effective_chat.id,
                update.effective_message.id,
                parse_mode=ParseMode.HTML)
            await context.bot.send_message(user_info['user_id'],
                                           "К сожалению, ваша награда была отклонена администратором",
                                           reply_to_message_id=user_reward["message_id"])
            threads = CHATS['FORUM_THREADS']
            group_id = CHATS['FORUM_GROUP']
            await context.bot.send_message(group_id,
                                           f'Награда пользователя {name}, "{reward.name}", была отклонена модераторами :(',
                                           message_thread_id=threads['comments'],
                                           parse_mode=ParseMode.HTML)
            reward.number_left += 1
            reward.update_in_db()
        else:
            if points % 10 == 1 and points % 100 != 11:
                word = "балл"
            elif 2 <= points % 10 <= 4 and (points % 100 < 10 or points % 100 >= 20):
                word = "балла"
            else:
                word = "баллов"
            print(points)
            mention = f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.full_name}</a>' \
                if update.effective_user.id is not None else f'{update.effective_user.full_name}'
            await database.approve_user_reward(ur_id)
            await context.bot.edit_message_text(
                f'<b>Куплена награда:</b>\n'
                f'{reward.name}\n'
                f'<b>Пользователь:</b> {name}\n'
                f'<b>Цена:</b> {points} {word}\n\n'
                f'<i>Награда подтверждена модератором {mention}</i>',
                update.effective_chat.id,
                update.effective_message.id,
                parse_mode=ParseMode.HTML)








