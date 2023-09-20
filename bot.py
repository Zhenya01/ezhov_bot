import pprint
from telegram.ext import CommandHandler, MessageHandler, filters, JobQueue, \
    ContextTypes, ConversationHandler, CallbackQueryHandler
from telegram import Update, BotCommandScopeDefault, BotCommandScopeChatMember, BotCommandScope, BotCommand, \
    InputMediaVideo
import logging

import platform

import cfg
import channel_points_module
import forward_posts
import regs
import tiktok_module
import twitch_module
import chat_management_module
from helpers_module import logger, application, update_user_info
from helpers_module import WAITING_FOR_TIKTOK_DESISION
from helpers_module import TIKTOK_APPROVAL_STATES
from helpers_module import SEND_TIKTOK_DEEPLINK
from helpers_module import SELECT_USER, ADD_OR_SUBTRACT_POINTS, ADD_POINTS, SUBTRACT_POINTS, ENTER_POINTS_MANAGEMENT
from helpers_module import SELECT_REWARD_TO_EDIT, PICK_ACTION, EDIT_REWARD, ADDING_REWARD, CHANGE_NAME, CHANGE_DESCRIPTION, CHANGE_PRICE, REMOVE_REWARD, BACK_TO_REWARDS, BUY_REWARD
import info_messages
from helpers_module import LOOK_FOR_REWARDS, SEE_POINTS_INFO, USER_POINTS_MENU, SELECT_REWARD_TO_BUY, WAITING_FOR_REWARD_DECISION, CANCEL_BUTTON

@update_user_info
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug('STARTING')
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет. Я Жижов. Добро пожаловать!")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Кстааати, купи слона!")
    if 'phrases_list' not in context.bot_data.keys():
        context.bot_data['phrases_list'] = []


@update_user_info
async def post_hello_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == 93906905:
        await context.bot.send_message(93906905, 'Отправил')
        text = 'Би - бо - бу - бип\n11010000 10101111 100000 11010000 10110001 11010000 10111110 11010001 10000010 100000 11010000 10010110 11010000 10111000 11010000 10110110 11010000 10111110 11010000 10110010'
        await context.bot.send_message(id=-1001684055869, text=text)


@update_user_info
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Все говорят: "{update.message.text}", а ты возьми, да и купи слона!')


@update_user_info
async def bugs_and_improvements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = 'Ссылка на группу с багами и предложениями: https://t.me/+7dycu9-YYJUxMGMy'
    await update.message.reply_text(text)


async def send_reboot_message(_):
    await application.bot.send_message(93906905, 'Бот перезагружен')
    pprint.pprint(f'LOGGER_DICT - {logging.root.manager.loggerDict}')


async def set_commands(_):
    await application.bot.set_my_commands([BotCommand('points', 'Управление баллами')],
                                          scope=BotCommandScopeDefault())
    # media = []
    # for i in range(10):
    #     media.append(InputMediaVideo('BAACAgIAAx0EV48wTAADd2Pr6oQ_OS4TFDlAZ4vElYs5upFrAAJgKAADp2BLD8lITWKCAUYuBA'))
    # print(media)
    # msg = await application.bot.send_media_group(93906905,
    #                                              media=media, caption='abc')
    # print(msg)
    # await application.bot.set_my_commands([BotCommand('points', 'Управление баллами'),
    #                                        BotCommand('pm', 'Управление баллами (администратор)')],
    #                                       scope=BotCommandScopeChatMember(regs.ezhov_user_id, regs.ezhov_user_id))
    # await application.bot.set_my_commands([BotCommand('points', 'Управление баллами')],
    #                                       scope=BotCommandScopeChatMember(regs.zhenya_user_id, regs.zhenya_user_id))
    print('set commands success')


async def functions_to_run_at_the_beginning(_):
    await twitch_module.setup_twitch_objects()
    await twitch_module.subscribe_stream_online()
    await twitch_module.subscribe_stream_offline()
    await set_commands(_)
    await send_reboot_message(_)


conv_handler = ConversationHandler(
        entry_points=[
                      CommandHandler("send_tiktok", tiktok_module.waiting_for_tiktok, filters=filters.ChatType.PRIVATE),
                      CommandHandler("start", tiktok_module.waiting_for_tiktok,
                                     filters=filters.Regex(rf'{SEND_TIKTOK_DEEPLINK}') & filters.ChatType.PRIVATE),
                      CommandHandler('start_approval', tiktok_module.show_tiktok_to_approve),
                      CommandHandler('pm', channel_points_module.points_manual_management,
                                     filters=filters.User(user_id=regs.ezhov_user_id) & filters.ChatType.PRIVATE),
                      CommandHandler('pm', channel_points_module.points_manual_management,
                                     filters=filters.User(user_id=regs.zhenya_user_id) & filters.ChatType.PRIVATE),
                      CommandHandler('rm', channel_points_module.rewards_command_entered,
                                     filters=filters.User(user_id=regs.ezhov_user_id) & filters.ChatType.PRIVATE),
                      CommandHandler('rm', channel_points_module.rewards_command_entered,
                                     filters=filters.User(user_id=regs.zhenya_user_id) & filters.ChatType.PRIVATE),
                      CommandHandler('add_reward', channel_points_module.start_adding_reward,
                                     filters=filters.User(user_id=regs.ezhov_user_id) & filters.ChatType.PRIVATE),
                      CommandHandler('add_reward', channel_points_module.start_adding_reward,
                                     filters=filters.User(user_id=regs.zhenya_user_id) & filters.ChatType.PRIVATE),
                      CommandHandler('points', channel_points_module.points,
                                     filters=filters.ChatType.PRIVATE)
        ],

        states={
            # WAITING_FOR_TIKTOK:
            # [
            #     CommandHandler('cancel', tiktok_module.cancel_waiting_for_tiktok),
            #     MessageHandler(filters.Entity('url'), tiktok_module.got_tiktok_link),
            #     MessageHandler(filters.VIDEO, tiktok_module.got_tiktok_file),
            #     MessageHandler(filters.ALL, tiktok_module.got_wrong_answer),
            # ],
            WAITING_FOR_TIKTOK_DESISION:
            [
                CallbackQueryHandler(tiktok_module.tiktok_approval_callback_handler,
                                     pattern=rf'^{TIKTOK_APPROVAL_STATES}')
            ],
            SELECT_USER:
            [
                MessageHandler(filters.TEXT,
                               channel_points_module.show_user_points_info)
            ],
            ADD_OR_SUBTRACT_POINTS:
            [
                MessageHandler(filters.Text(['➕ Добавить', '➖ Отнять']),
                               channel_points_module.choose_points_action)
            ],
            ADD_POINTS:
            [
                MessageHandler(filters.TEXT,
                               channel_points_module.add_or_subtract_points)
            ],
            SUBTRACT_POINTS:
            [
                MessageHandler(filters.TEXT,
                               channel_points_module.add_or_subtract_points)
            ],
            SELECT_REWARD_TO_EDIT:
            [
               MessageHandler(filters.TEXT,
                              channel_points_module.show_reward)
            ],
            PICK_ACTION:
            [
                MessageHandler(filters.Text([CHANGE_NAME, CHANGE_DESCRIPTION, CHANGE_PRICE, REMOVE_REWARD, BACK_TO_REWARDS]),
                               channel_points_module.manage_reward)
            ],
            EDIT_REWARD:
            [
                MessageHandler(filters.TEXT,
                               channel_points_module.save_new_reward_char)
            ],
            ADDING_REWARD:
            [
                MessageHandler(filters.TEXT & filters.User(user_id=[regs.ezhov_user_id, regs.zhenya_user_id]),
                               channel_points_module.add_reward)
            ],
            USER_POINTS_MENU:
            [
                MessageHandler(filters.Text([CANCEL_BUTTON, LOOK_FOR_REWARDS, SEE_POINTS_INFO]),
                               channel_points_module.points_descision)
            ],
            SELECT_REWARD_TO_BUY:
            [
                MessageHandler(filters.TEXT,
                               channel_points_module.user_chose_reward)
            ],
            WAITING_FOR_REWARD_DECISION:
            [
                MessageHandler(filters.Text([BUY_REWARD, BACK_TO_REWARDS]),
                               channel_points_module.reward_decision)
            ]

        },
        fallbacks=[],
        name="main_conversation",
        persistent=True,
        allow_reentry=True
    )


print('Бот перезагружен')
os = platform.system()
print(f'os - {os}')
application.add_handler(conv_handler)
application.add_handler(CommandHandler('start', start))
application.add_handler(MessageHandler(filters.Chat(chat_id=regs.zhenya_group_id) and filters.User(user_id=777000), forward_posts.comment_under_the_post))
application.add_handler(MessageHandler(filters.Chat(chat_id=regs.zdarovezhov_group_id) and filters.User(user_id=777000), forward_posts.comment_under_the_post))
application.add_handler(CommandHandler('start_tiktoks', tiktok_module.start_ticktock_evening,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('add', twitch_module.add_phrase,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('add_first', twitch_module.add_phrase_to_start,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('show', twitch_module.show,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('remove', twitch_module.remove_phrase,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('silent', twitch_module.silent,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('loud', twitch_module.loud,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('commands', info_messages.commands,
                                       filters=filters.Chat(chat_id=regs.twitch_commands_users_list)))
application.add_handler(CommandHandler('bugs', bugs_and_improvements))
application.add_handler(CommandHandler('test_message', tiktok_module.test_thread_sending))
application.add_handler(CommandHandler('improvements', bugs_and_improvements))
application.add_handler(CommandHandler('mute', chat_management_module.mute, filters.REPLY))

application.add_handler(CommandHandler('info', info_messages.info))
application.add_handler(CommandHandler('publish', tiktok_module.publish_ticktocks))
# CommandHandler("send_tiktok", tiktok_module.waiting_for_tiktok, filters=filters.ChatType.PRIVATE),
# CommandHandler("start", tiktok_module.waiting_for_tiktok, filters=filters.Regex(rf'{SEND_TIKTOK_DEEPLINK}') & filters.ChatType.PRIVATE),
application.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.Chat(chat_id=regs.zdarovezhov_group_id),
                   chat_management_module.kick_from_group))
application.add_handler(
    MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.Chat(chat_id=regs.zhenya_group_id),
                   chat_management_module.kick_from_group))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.StatusUpdate.LEFT_CHAT_MEMBER,
                                       chat_management_module.remove_join_left_message))
# application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER,
#                                        chat_management_module.remove_join_left_message))
application.add_handler(MessageHandler(filters.Chat(chat_id=regs.zhenya_forum_id) & filters.User(user_id=regs.zhenya_user_id), forward_posts.forward_post))
application.add_handler(MessageHandler(filters.Chat(chat_id=regs.ezhov_forum_id) & filters.User(user_id=[regs.ezhov_user_id, regs.zdarovezhov_channel_id]), forward_posts.forward_post))
application.add_handler(MessageHandler(filters.Chat(chat_id=regs.zhenya_forum_id) & filters.User(user_id=regs.ezhov_user_id), forward_posts.forward_post))
# application.add_handler(MessageHandler(filters.Chat(chat_id=regs.zhenya_channel_id), forward_posts.forward_to_comments))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE,
                                       chat_management_module.schedule_remove_rename_message))
application.add_handler(MessageHandler(filters.VIDEO & filters.ChatType.PRIVATE,
                                       tiktok_module.got_tiktok_file))
application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER,
                                       chat_management_module.remove_join_left_message))
application.add_handler(MessageHandler(filters.Chat(regs.ezhov_forum_id) & filters.ALL,
                                       channel_points_module.add_points_for_comment))
# application.add_handler(CommandHandler('file', tiktok_module.get_ticktock_file))
# application.add_handler(CommandHandler('post', post_hello_message))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
job_queue: JobQueue = application.job_queue
if os != 'Windows':
    application.job_queue.run_custom(functions_to_run_at_the_beginning, job_kwargs={})
else:
    application.job_queue.run_custom(set_commands, job_kwargs={})
    application.job_queue.run_custom(send_reboot_message, job_kwargs={})
application.run_polling()



# TODO добавить логи

