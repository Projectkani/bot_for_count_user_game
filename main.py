import sqlite3
import time
import os

from dotenv import load_dotenv
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

load_dotenv()

# токен менять во втором файле!
bot = Bot(token= os.getenv('TOKEN'))
dp = Dispatcher(bot)

# ничего тут не трогай!!!
conn = sqlite3.connect('tea.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY, name TEXT, tea_count INTEGER, last_used INTEGER)''')
conn.commit()

# тут можешь написать свою команду для вызова
@dp.message_handler(commands=['work'])
async def drink_tea(message: types.Message):
    user_id = message.from_user.id
    now = int(time.time())

    # проверка времени
    cursor.execute('SELECT last_used FROM users WHERE id=?', (user_id,))
    last_used = cursor.fetchone()
# там где 10800 - пишешь своё значение в сек(тип через сколько можно юзать бот)
    if last_used and now - last_used[0] < 10800:
        # проверка, прошло ли 10800 сек, перед повторным использование бота
        remaining_time = timedelta(seconds=(10800 - (now - last_used[0])))
        remaining_time_str = str(remaining_time).split('.')[0]
        # в стиле маркдоун, \n - это ентер. Тут пиши что хочешь. в скобках {сколько осталось до след раза}
        # Так же тут я использую парсмод HTML, то есть все жирные шрифты и прочее делаеться по аналогии с тем,
        # что показано.
        await message.reply(f"До следующей смены ещё:<b> {remaining_time_str} </b>.\n"
                            f"Попей пока чаю, порешай сканворды, или посмотри аниме <b>@reker_anime_bot</b>", parse_mode=ParseMode.HTML)
        return

    # увеличиваем количество смен для пользователя Я везде оставлю тиа, тк боюсь трограть, хотя мог бы просто через ctrl + h заменить тиа на ворк
    cursor.execute('INSERT OR IGNORE INTO users (id, name, tea_count, last_used) VALUES (?, ?, 0, ?)',
                   (user_id, message.from_user.full_name, now))
    cursor.execute('UPDATE users SET tea_count=tea_count+1, last_used=? WHERE id=?', (now, user_id))
    conn.commit()

    # чекаем сколько всего смен отработал
    cursor.execute('SELECT tea_count FROM users WHERE id=?', (user_id,))
    tea_count = cursor.fetchone()[0]

    # пишем что смена зачтена и сколько всего отработал
    await message.reply(f"Ты отработал: {tea_count} смен в этом коллективе!")

@dp.message_handler(commands=['top_work'])
async def tea_stats(message: types.Message):
    cursor.execute('SELECT name, tea_count FROM users ORDER BY tea_count DESC')
    rows = cursor.fetchall()

    # стата топа
    text = "Список самых отбитых работяг:\n"
    for i, row in enumerate(rows):
        text += "{}. {}: {} смен\n".format(i + 1, row[0], row[1])

    # отправляем сообщение со статистикой в чат
    await message.reply(text, parse_mode=ParseMode.MARKDOWN)


executor.start_polling(dp, skip_updates=True)