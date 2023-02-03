from pprint import pprint

from regs import cursor


def add_tiktok(message_id, sender_id, file_id, is_approved):
    command = '''
    INSERT INTO ezhov_bot.tiktoks 
    (message_id, sender_user_id, file_id, is_approved) 
    VALUES (%s, %s, %s, %s);'''
    cursor.execute(command, (message_id, sender_id, file_id, is_approved))


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


