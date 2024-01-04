from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from cfg_1 import update_user_info


@update_user_info
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = \
f'''Карочи это вот ссылочки на всё что связано с моим ТВОРЧЕСТВОМ.
Подпишитесь пожалуйста на всё, этим вы меня очень поддержите:

Чаще всего стримлю на twitch:
twitch.tv/zdarovezhov
Общаемся все в ТГ: 
t.me/zdarovezhov
Уведомления о стримах:
t.me/zdarovezhovstreams
Дискордик:
https://discord.gg/QGsCrV2F


Нарезки со стримов в YouTube: 
vk.cc/cjveTL
легендарные моменты заливаем в YouTube Shorts: 
vk.cc/cjvf3v
Я в ТикТок:
vk.cc/cjvifP
из меня делают мемы в Yappi: 
vk.cc/cjveXZ'''
    await update.message.reply_text(text)


@update_user_info
async def commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    streamer_text = \
f'''*Комманды стримера:*

*Оповещения о стримах:*
Следующий стрим пройдёт без уведомления \- /silent
Следующий стрим пройдёт c уведомлением \- /loud
Добавить фразу последней в список оповещений о стримах \- /add
Добавить фразу первой в список оповещений о стримах \- /add\_first
Убрать последнюю фразу из списка оповещений о стримах \- /remove
Посмотреть весь список оповещений о стримах\- /show

*Тикток вечерок:*
Отправить сообщение о наборе тиктоков \- /start\_tiktoks
Начать оценивать тиктоки \- /start\_approval
Опубликовать пост с тиктоками на канал \- /publish

*Баллы:*
Зайти в меню управления наградами: \- /rewards
Добавить новую награду: \- /add\_reward
Зайти в меню управления баллами участников: \- /pm
Зайти в меню баллов \(как участник\): \- /points
'''
    await update.message.reply_text(streamer_text,
                                    parse_mode=ParseMode.MARKDOWN_V2)
