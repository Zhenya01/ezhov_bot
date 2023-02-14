import datetime
from pprint import pprint

import helpers_module
from regs import cursor


async def get_user_info(user_id):
    return await helpers_module.get_user_info(user_id)


async def add_user(user_id, full_name):
    return await helpers_module.add_user(user_id, full_name)


async def update_user(user_id, nickname='', place_of_living='', bio='',
                     is_moderator='', is_admin='', can_send_tiktok='',
                     tiktoks_banned_until='', full_name='', title=''):
    return await helpers_module.update_user(user_id, nickname, place_of_living, bio,
                     is_moderator, is_admin, can_send_tiktok,
                     tiktoks_banned_until, full_name, title)


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



