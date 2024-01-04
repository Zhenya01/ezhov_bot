import datetime
from pprint import pprint

import cfg_1
from regs import cursor
import uuid


# Пользователи
async def get_user_info(user_id):
    return await cfg_1.get_user_info(user_id)


async def add_user(user_id, full_name):
    return await cfg_1.add_user(user_id, full_name)


async def update_user(user_id, nickname='', place_of_living='', bio='',
                     is_moderator='', is_admin='', can_send_tiktok='',
                     tiktoks_banned_until='', full_name='', title=''):
    return await cfg_1.update_user(user_id, nickname, place_of_living, bio,
                     is_moderator, is_admin, can_send_tiktok,
                     tiktoks_banned_until, full_name, title)


async def get_users():
    command = '''
    SELECT * FROM ezhov_bot.users ORDER BY full_name'''
    cursor.execute(command)
    result = cursor.fetchall()
    if result == []:
        return None
    return result


# Tiktoks
def add_tiktok(message_id, sender_id, file_id, is_approved, in_chat_message_id):
    command = '''
    INSERT INTO ezhov_bot.tiktoks 
    (message_id, sender_user_id, file_id, is_approved, in_chat_message_id) 
    VALUES (%s, %s, %s, %s, %s);'''
    cursor.execute(command, (message_id, sender_id, file_id, is_approved, in_chat_message_id))


def find_tiktok(tiktol_id):
    command = '''
        SELECT * FROM ezhov_bot.tiktoks
        WHERE tiktok_id = %s'''
    cursor.execute(command, (tiktol_id,))
    result = cursor.fetchone()
    return result


def pick_user_latest_tiktok(user_id):
    command = '''
    SELECT * FROM ezhov_bot.tiktoks
    WHERE sender_user_id = '%s' AND is_sent = False
    ORDER BY time_sent DESC
    LIMIT 1'''
    cursor.execute(command, (user_id,))
    result = cursor.fetchone()
    return result
    # for key in result.keys():
    #     print(f'{key: {result[key]}}')
    # if not result:
    #     return None
    # else:
    #     return result


def count_unapproved_tiktoks(user_id):
    command = '''
    SELECT COUNT(tiktok_id) AS count
    FROM ezhov_bot.tiktoks
    WHERE sender_user_id = '%s' AND is_rejected = False AND is_approved = False'''
    cursor.execute(command, (user_id,))
    count = cursor.fetchone()
    return count


def count_unsent_tiktoks():
    command = '''
        SELECT COUNT(tiktok_id) AS count
        FROM ezhov_bot.tiktoks
        WHERE is_approved = True AND is_sent = False'''
    cursor.execute(command)
    count = cursor.fetchone()
    return count


def select_tiktok_to_approve():
    command = '''
    SELECT * FROM ezhov_bot.tiktoks
    WHERE is_approved = False AND is_rejected = False AND is_sent = False
    ORDER BY tiktok_id
    LIMIT 1'''
    cursor.execute(command)
    tiktok = cursor.fetchone()
    if not tiktok:
        return None
    else:
        return tiktok


def approve_tiktok(tiktok_id):
    command = '''
    UPDATE ezhov_bot.tiktoks
    SET is_approved = True
    WHERE tiktok_id = %s'''
    cursor.execute(command, (tiktok_id,))


def reject_tiktok(tiktok_id):
    command = '''
        UPDATE ezhov_bot.tiktoks
        SET is_rejected = True
        WHERE tiktok_id = %s'''
    cursor.execute(command, (tiktok_id,))


def select_tiktoks_to_send():
    command = '''
    SELECT * FROM ezhov_bot.tiktoks
    WHERE is_approved = True AND is_sent = False
    ORDER BY tiktok_id
    LIMIT 10'''
    cursor.execute(command)
    tiktoks = cursor.fetchall()
    if not tiktoks:
        return None
    else:
        return tiktoks


def tiktok_posted(tiktok_id):
    print(tiktok_id)
    command = '''
    UPDATE ezhov_bot.tiktoks
    SET is_sent = True
    WHERE tiktok_id = %s;
    '''
    cursor.execute(command, (tiktok_id,))


def ban_user_from_tiktoks(user_id, ban_end_time):
    user_id = str(user_id)
    command = '''
       UPDATE ezhov_bot.users
       SET can_send_tiktok = False, tiktoks_banned_until = %s
       WHERE user_id =%s;
    '''
    cursor.execute(command, (ban_end_time, user_id))


def unban_user_from_tiktoks(user_id):
    user_id = str(user_id)
    command = '''
       UPDATE ezhov_bot.users
       SET can_send_tiktok = True, tiktoks_banned_until = NULL
       WHERE user_id = %s;
    '''
    cursor.execute(command, (user_id,))


def delete_in_chat_message(message_id, chat_id):
    chat_id = str(chat_id)
    command = '''
        UPDATE ezhov_bot.tiktoks
        SET in_chat_message_id = NULL
        WHERE in_chat_message_id = %s AND sender_user_id = %s;
        '''
    cursor.execute(command, (message_id, chat_id))

# Баллы тг
def add_points(user_id, points):
    user_id = str(user_id)
    cfg_1.logger.debug(f'Пользователь {user_id}. Начисляем {points} баллов')
    command = '''
    SELECT * FROM ezhov_bot.tg_points
    WHERE user_id = %s'''
    cursor.execute(command, (user_id,))
    result = cursor.fetchone()
    print(result)
    if result is None:
        command = '''
        INSERT INTO ezhov_bot.tg_points 
        (user_id) VALUES (%s)'''
        cursor.execute(command, (user_id,))
    command = '''
    UPDATE ezhov_bot.tg_points
    SET tg_points = tg_points + %s
    WHERE user_id = %s'''
    cursor.execute(command, (points, user_id))


def subtract_points(user_id, points):
    user_id = str(user_id)
    command = '''
        SELECT * FROM ezhov_bot.tg_points
        WHERE user_id = %s'''
    cursor.execute(command, (user_id,))
    if cursor.fetchone() is None:
        command = '''
            INSERT INTO ezhov_bot.tg_points 
            (user_id) VALUES (%s)'''
        cursor.execute(command, (user_id,))
    # command = '''
    # UPDATE ezhov_bot.tg_points
    # SET tg_points = tg_points - %s
    # WHERE user_id = %s'''
    command = '''
    UPDATE ezhov_bot.tg_points
    SET tg_points = 
    CASE
    WHEN tg_points - %s < 0 THEN 0
    ELSE tg_points - %s
    END
    WHERE user_id = %s;'''
    cursor.execute(command, (points, points, user_id))


# Point rewards
async def get_rewards():
    command = '''
    SELECT * FROM channel_rewards
    ORDER BY name
    '''
    cursor.execute(command)
    rewards = cursor.fetchall()
    if rewards == []:
        return None
    else:
        return rewards


class Reward:
    def __init__(self, name,
                 reward_id=None,
                 description=None,
                 price=None,
                 number_left=None,
                 person_total_limit=None,
                 person_cooldown=None,
                 total_cooldown=None):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.reward_id = reward_id
        self.description = description
        self.price = price
        self.number_left = number_left
        self.person_total_limit = person_total_limit
        self.person_cooldown = person_cooldown
        self.total_cooldown = total_cooldown

    def __str__(self):
        return (f'UUID: {self.uuid}\n'
                f'Name: {self.name}\n'
                f'Description: {self.description}\n'
                f'Price: {self.price}\n'
                f'Number_left: {self.number_left}\n'
                f'Person_total_limit: {self.person_total_limit}\n'
                f'Person_cooldown: {self.person_cooldown}\n'
                f'Total cooldown: {self.total_cooldown}')

    def put_to_db(self):
        reward_id = add_reward(self.name, self.description, self.price, self.number_left, self.person_total_limit,
                               self.person_cooldown, self.total_cooldown)
        self.reward_id = reward_id

    def update_in_db(self):
        update_reward(self.reward_id, self.name, self.description, self.price, self.number_left,
                      self.person_total_limit, self.person_cooldown, self.total_cooldown)

    def delete_from_db(self):
        if self.reward_id is None:
            raise Exception('No reward_id in an object')
        remove_reward(self.reward_id)


def add_reward(name, description, price, number_left, person_total_limit, person_cooldown, total_cooldown):
    command = '''
    INSERT INTO ezhov_bot.channel_rewards 
    (name, description, price, number_left, person_total_limit, person_cooldown, total_cooldown) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING reward_id;'''
    cursor.execute(command, (name, description, price, number_left, person_total_limit, person_cooldown, total_cooldown))
    return cursor.fetchone()['reward_id']


def update_reward(reward_id, name='', description='', price='', number_left='', person_total_limit='',
                        person_cooldown='', total_cooldown=''):
    where_clause = f"reward_id = %s"
    fields_dict = {'name': name,
                   'description': description,
                   'price': price,
                   'number_left': number_left,
                   'person_total_limit': person_total_limit,
                   'person_cooldown': person_cooldown,
                   'total_cooldown': total_cooldown}
    set_string = ''
    fields_tuple = ()
    for key in fields_dict:
        if fields_dict[key] != '':
            set_string = set_string + f"{key} = %s, "
            fields_tuple = fields_tuple + (fields_dict[key],)
    fields_tuple = fields_tuple + (reward_id,)
    set_string = set_string[0:-2]
    print(set_string)
    command = f'UPDATE ezhov_bot.channel_rewards SET {set_string} WHERE {where_clause}'
    print(command)
    print(fields_tuple)
    cursor.execute(command, fields_tuple)


def remove_reward(reward_id):
    command = '''
    DELETE FROM ezhov_bot.channel_rewards             
    WHERE reward_id = %s'''
    cursor.execute(command, (reward_id,))


async def get_reward_info(reward_id) -> Reward:
    command = '''
    SELECT * FROM ezhov_bot.channel_rewards
    WHERE reward_id = %s
    '''
    print(command)
    cursor.execute(command, (reward_id,))
    reward_info = cursor.fetchone()
    print(reward_info)
    if reward_info is None:
        return None
    else:
        reward = Reward(reward_info['name'],
                        reward_info['reward_id'],
                        reward_info['description'],
                        reward_info['price'],
                        reward_info['number_left'],
                        reward_info['person_total_limit'],
                        reward_info['person_cooldown'],
                        reward_info['total_cooldown']
                        )
    return reward


async def add_user_reward(user_id, reward_id):
    command = '''
        INSERT INTO ezhov_bot.user_rewards 
        (user_id, reward_id, purchase_time)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        RETURNING ur_id
        '''
    print(command)
    cursor.execute(command, (user_id, reward_id))
    reward_id = cursor.fetchone()
    return reward_id


async def add_ur_message_id(ur_id, message_id):
    command = '''
    UPDATE ezhov_bot.user_rewards
    SET message_id = %s
    WHERE ur_id = %s'''
    cursor.execute(command, (message_id, ur_id))
    return


async def get_user_reward_by_id(ur_id):
    command = '''
    SELECT * FROM ezhov_bot.user_rewards
    WHERE ur_id = %s'''
    cursor.execute(command, (ur_id,))
    result = cursor.fetchone()
    return result


async def get_latest_reward_by_id(reward_id):
    command = '''SELECT * FROM ezhov_bot.user_rewards
                 WHERE reward_id = %s AND is_approved = true 
                 AND purchase_time = 
                 (SELECT MAX(purchase_time) FROM ezhov_bot.user_rewards
                 WHERE reward_id = %s AND is_approved = true)'''
    cursor.execute(command, (reward_id, reward_id))
    result = cursor.fetchone()
    return result


async def get_latest_ur_by_id(reward_id, user_id):
    user_id = str(user_id)
    command = '''SELECT * FROM ezhov_bot.user_rewards
                 WHERE reward_id = %s AND is_approved = true AND user_id = %s
                 AND purchase_time = 
                 (SELECT MAX(purchase_time) FROM ezhov_bot.user_rewards
                 WHERE reward_id = %s AND is_approved = true AND user_id = %s)'''
    cursor.execute(command, (reward_id, user_id, reward_id, user_id))
    result = cursor.fetchone()
    return result


async def get_user_reward_count(reward_id, user_id):
    user_id = str(user_id)
    command = '''SELECT COUNT(*) as count FROM ezhov_bot.user_rewards
                 WHERE reward_id = %s AND user_id = %s AND is_approved = True'''
    cursor.execute(command, (reward_id, user_id))
    result = cursor.fetchone()
    return result


async def approve_user_reward(ur_id):
    command = '''
    UPDATE ezhov_bot.user_rewards
    SET is_approved = True
    WHERE ur_id = %s'''
    cursor.execute(command, (ur_id,))
    return


async def reject_user_reward(ur_id):
    command = '''
    UPDATE ezhov_bot.user_rewards
    SET is_approved = False
    WHERE ur_id = %s'''
    cursor.execute(command, (ur_id,))
    return






