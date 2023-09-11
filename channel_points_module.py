from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

import cfg
import database
import helpers_module
# Points management states
from helpers_module import ADD_OR_SUBTRACT_POINTS, ADD_POINTS, SUBTRACT_POINTS, ENTER_POINTS_MANAGEMENT, SELECT_USER
from helpers_module import SELECT_REWARD_TO_EDIT, PICK_ACTION, EDIT_REWARD, ADDING_REWARD, CHANGE_NAME, CHANGE_DESCRIPTION, CHANGE_PRICE, REMOVE_REWARD, BACK_TO_REWARDS, CANCEL_BUTTON
from helpers_module import LOOK_FOR_REWARDS, SEE_POINTS_INFO, USER_POINTS_MENU, WAITING_FOR_REWARD_DECISION, SELECT_REWARD_TO_BUY, BUY_REWARD
from helpers_module import EDIT, VIEW


# -----------------------------------------------------Админ---------------------------------------------------------- #


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
    rewards_keyboard = [[CANCEL_BUTTON]]
    for reward in rewards_dict.keys():
        rewards_keyboard.append([reward])
    context.user_data['rewards_dict'] = rewards_dict
    await context.bot.send_message(update.effective_chat.id,
                                   'Выбери награду для просмотра/изменения:',
                                   reply_markup=ReplyKeyboardMarkup(rewards_keyboard))
    reason = context.user_data['rewards_reason']
    if reason == str(EDIT):
        return SELECT_REWARD_TO_EDIT
    elif reason == str(VIEW):
        return SELECT_REWARD_TO_BUY


async def show_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await context.bot.send_message(update.effective_chat.id,
                                   f'<b>Награда:</b> {name}\n'
                                   f'<b>Описание: </b> {reward["description"]}\n'
                                   f'<b>Цена: </b> {reward["price"]} баллов.\n'
                                   f'Выбери что сделать с этой наградой:',
                                   reply_markup=ReplyKeyboardMarkup([[CHANGE_NAME], [CHANGE_DESCRIPTION], [CHANGE_PRICE], [REMOVE_REWARD], [BACK_TO_REWARDS]],
                                                                    resize_keyboard=True),
                                   parse_mode=ParseMode.HTML)
    context.user_data['managed_reward'] = reward
    return PICK_ACTION


async def manage_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.message.text
    context.user_data['reward_action'] = action
    reward = context.user_data['managed_reward']
    if action == BACK_TO_REWARDS:
        await show_rewards(update, context)
        return SELECT_REWARD_TO_EDIT
    elif action == REMOVE_REWARD:
        await database.remove_reward(reward['reward_id'])
        await context.bot.send_message(update.effective_chat.id,
                                       'Ачивка успешно удалена')
        await show_rewards(update, context)
        return SELECT_REWARD_TO_EDIT
    else:
        await context.bot.send_message(update.effective_chat.id,
                                       'Введи новое значение:',
                                       reply_markup=ReplyKeyboardMarkup([['Отменить']], resize_keyboard=True))
        return EDIT_REWARD


async def save_new_reward_char(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data['reward_action']
    reward = context.user_data['managed_reward']
    if action == CHANGE_NAME:
        await database.update_reward(reward['reward_id'], name=update.message.text)
        edited_string = f'Имя награды изменено на {update.message.text}.'
    elif action == CHANGE_DESCRIPTION:
        await database.update_reward(reward['reward_id'], description=update.message.text)
        edited_string = f'Имя награды изменено на {update.message.text}.'
    else:
        if not update.message.text.isdigit():
            await context.bot.send_message(update.effective_chat.id,
                                           f'Введите цену награды в баллах (число)',
                                           reply_markup=ReplyKeyboardRemove())
            return EDIT_REWARD
        await database.update_reward(reward['reward_id'], price=int(update.message.text))
        edited_string = f'Имя награды изменено на {update.message.text}.'
    await context.bot.send_message(update.effective_chat.id,
                                   edited_string)
    reward = await database.get_reward_info(reward['reward_id'])
    await context.bot.send_message(update.effective_chat.id,
                                   f'<b>Награда:</b> {reward["name"]}\n'
                                   f'<b>Описание:</b> {reward["description"]}\n'
                                   f'<b>Цена:</b> {reward["price"]} баллов.\n'
                                   f'Выбери что сделать с этой наградой:',
                                   reply_markup=ReplyKeyboardMarkup(
                                       [[CHANGE_NAME], [CHANGE_DESCRIPTION], [CHANGE_PRICE], [REMOVE_REWARD],
                                        [BACK_TO_REWARDS]],
                                       resize_keyboard=True),
                                   parse_mode=ParseMode.HTML)
    context.user_data['managed_reward'] = reward
    return PICK_ACTION


async def start_adding_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(update.effective_chat.id,
                                   'Введи название награды, описание и цену через точку с запятой (пример: Пицца;Разыгрываем пиццу на стриме;5000)',
                                   reply_markup=ReplyKeyboardMarkup([[CANCEL_BUTTON]],
                                                                    resize_keyboard=True))
    return ADDING_REWARD


async def add_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL_BUTTON:
        await context.bot.send_message(update.effective_chat.id,
                                       'Создание награды отменено',
                                       reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    reward_parts_list = update.message.text.split(';')
    if len(reward_parts_list) != 3:
        await context.bot.send_message(update.effective_chat.id,
                                       'Ты добавил слишком много/мало точек с запятой. Должно быть 3 пункта: название, описание и цена. Пример: Пицца;Разыгрываем пиццу на стриме;5000',)
        return ADDING_REWARD
    elif not reward_parts_list[2].isdigit():
        await context.bot.send_message(update.effective_chat.id,
                                       f'Цена награды в баллах должна быть числом. Попробуй еще раз. Пример: Пицца;Разыгрываем пиццу на стриме;5000')
        return ADDING_REWARD
    else:
        name = reward_parts_list[0]
        description = reward_parts_list[1]
        price = int(reward_parts_list[2])
        await database.add_reward(name, description, price)
        await context.bot.send_message(update.effective_chat.id,
                                       f'Награда добавлена!\n'
                                       f'<b>Награда:</b> {name}\n'
                                       f'<b>Описание:</b> {description}\n'
                                       f'<b>Цена:</b> {price} баллов.',
                                       reply_markup=ReplyKeyboardRemove(),
                                       parse_mode=ParseMode.HTML)
        return ConversationHandler.END


async def add_points_for_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO поменять на prestige level
    points = int(cfg.BASE_COMMENT_POINTS) + (int(cfg.PRESTIGE_LEVEL_ADDED_MULTIPLIER) * 1)
    database.add_points(update.effective_user.id, points)


# ------------------------------------------------Участники----------------------------------------------------------- #

@helpers_module.update_user_info
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
                                   f'Здесь можно посмотреть и преобрести доступные награды или посмотреть подробную '
                                   f'информацию о баллах и их способах получения',
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=ReplyKeyboardMarkup([[LOOK_FOR_REWARDS], [SEE_POINTS_INFO], [CANCEL_BUTTON]],
                                                                      resize_keyboard=True))
    context.user_data['points_management_user_id'] = user["user_id"]
    return USER_POINTS_MENU


async def points_descision(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                '1 балл за 1 сообщение\n'
                '10 баллов за 1 тик-ток\n'
                '20 баллов за супертикток\n'
                '<b>Вычитаются баллы </b>за мут и за покупку награды\n'
                'Это еще не все способы получения и потери баллов :) Ведётся активное продумывание и разработка')
        await context.bot.send_message(update.effective_chat.id,
                                       text,
                                       parse_mode=ParseMode.HTML)
    else:
        context.user_data['rewards_reason'] = helpers_module.VIEW
        return_value = await show_rewards(update, context)
        return return_value


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
    await context.bot.send_message(update.effective_chat.id,
                                   f'<b>Награда:</b> {name}\n'
                                   f'<b>Описание: </b> {reward["description"]}\n'
                                   # f'<b>Цена: </b> {reward["price"]} баллов.\n'
                                   # f'\nКупить?',
                                   f'\n<i>Покупка наград временно не доступна</i>',
                                   # reply_markup=ReplyKeyboardMarkup([[BUY_REWARD], [BACK_TO_REWARDS]],
                                   #                                  resize_keyboard=True),
                                   parse_mode=ParseMode.HTML)
    return SELECT_REWARD_TO_BUY
    # context.user_data['managed_reward'] = reward
    # return WAITING_FOR_REWARD_DECISION


async def reward_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == BACK_TO_REWARDS:
        result = await show_rewards(update, context)
        return result
    else:
        managed_reward = context.user_data['managed_reward']
        user_info = await database.get_user_info(update.effective_user.id)
        points_balance = user_info['tg_points']
        if points_balance < managed_reward['price']:
            await context.bot.send_message(update.effective_chat.id,
                                           'На вашем счету недостаточно баллов')
            result = await show_rewards(update, context)
            return result
        pass

