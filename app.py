import os
import threading
import asyncio
from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
import datetime

# ================= НАСТРОЙКИ =================
TOKEN = os.environ.get("BOT_TOKEN", "9000461813:AAE0yOATM_H7QLmFpIqO0HV1qd79HRewS3A") 
ADMIN_ID = 6886855546 
CHANNEL_ID = "@rabotanomer1_2026"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= ГОРОДА =================
REGIONS = {
    "Казахстан": ["Алматы", "Астана", "Караганда", "Шымкент", "Актобе", "Атырау", "Павлодар", "Усть-Каменогорск", "Костанай", "Тараз"],
    "Россия": ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Уфа", "Казань"],
    "Узбекистан": ["Ташкент", "Самарканд", "Бухара"],
    "Кыргызстан": ["Бишкек", "Ош", "Сокулук"],
    "Беларусь": ["Минск", "Гомель", "Брест"],
    "Украина": ["Киев", "Львов", "Харьков"],
    "Азербайджан": ["Баку", "Гянджа"]
}
COUNTRIES = list(REGIONS.keys())

# ================= ВАКАНСИИ =================
JOBS = [
    ("Казахстан", "оффлайн", "Алматы", "Администратор — ИП Моисеева", "💰 от 400 000 ₸.", "💬 @Www_rkR"),
    ("Казахстан", "оффлайн", "Астана", "Продавец-кассир — Fix Price", "💰 250 000–280 000 ₸.", "💬 @Www_rkR"),
    ("Казахстан", "оффлайн", "Караганда", "Водитель автомобиля", "ЗП: 367 000 - 400 000 ₸.", "📞 +7 (7212) 55-66-77"),
    ("Казахстан", "оффлайн", "Шымкент", "Кассир-регистратор — Neurolife", "💰 240 000–280 000 ₸.", "💬 @Www_rkR"),
    ("Казахстан", "онлайн", "Алматы", "Оператор call-центра — I-Con", "💰 400 000–700 000 ₸.", "💬 @Www_rkR"),
    ("Казахстан", "онлайн", "Астана", "Менеджер по клиентам — ИП Пак", "💰 100 000–200 000 ₸.", "💬 @Www_rkR"),
    ("Казахстан", "онлайн", "Караганда", "Менеджер телемаркетинга", "ЗП: 150 000 - 250 000 ₸.", "💬 @Www_rkR"),
    ("Россия", "оффлайн", "Москва", "Сборщик заказов «ВкусВилл»", "💰 78 400–134 400 ₽.", "💬 @Www_rkR"),
    ("Россия", "оффлайн", "Санкт-Петербург", "Продавец-кассир Befree", "💰 ЗП не указана.", "💬 @Www_rkR"),
    ("Россия", "онлайн", "Москва", "Оператор поддержки МТС", "💰 35 000–55 000 ₽.", "💬 @Www_rkR"),
    ("Россия", "онлайн", "Уфа", "Консультант «Т-Банк»", "💰 47 000–60 000 ₽.", "💬 @Www_rkR"),
    ("Узбекистан", "оффлайн", "Ташкент", "Кассир TIIN OPTOM", "💰 4–5 млн сум.", "💬 @Www_rkR"),
    ("Узбекистан", "онлайн", "Ташкент", "Оператор call-центра", "💰 7–8,5 млн сум.", "💬 @Www_rkR"),
    ("Кыргызстан", "оффлайн", "Бишкек", "Пиццайоло — Блин Бульвар", "💰 2 000–2 500 сом.", "💬 @Www_rkR"),
    ("Кыргызстан", "онлайн", "Бишкек", "Переводчик — Global Oxilium", "💰 43 000–87 450 сом.", "💬 @Www_rkR"),
    ("Беларусь", "онлайн", "Минск", "Менеджер по продажам IT", "💰 2 170–9 870 Br.", "💬 @Www_rkR"),
    ("Украина", "онлайн", "Киев", "Оператор call-центра", "💰 15 000–30 000 ₴.", "💬 @Www_rkR"),
    ("Азербайджан", "оффлайн", "Баку", "Специалист по охране труда", "💰 1700–2200 AZN.", "💬 @Www_rkR"),
]

# ================= БАЗА ДАННЫХ =================
def init_db():
    conn = sqlite3.connect('jobs.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, country TEXT, jtype TEXT, city TEXT, title TEXT, desc TEXT, contact TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, reg_date TEXT)''')
    conn.commit()
    conn.close()

def seed_jobs():
    conn = sqlite3.connect('jobs.db')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO jobs (country, jtype, city, title, desc, contact) VALUES (?, ?, ?, ?, ?, ?)", JOBS)
        conn.commit()
    conn.close()

init_db()
seed_jobs()

def get_jobs_db(country, jtype, city=None):
    conn = sqlite3.connect('jobs.db')
    cur = conn.cursor()
    if city:
        cur.execute("SELECT title, desc, contact FROM jobs WHERE country=? AND jtype=? AND city=?", (country, jtype, city))
    else:
        cur.execute("SELECT title, desc, contact FROM jobs WHERE country=? AND jtype=?", (country, jtype))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_job_db(country, jtype, city, title, desc, contact):
    conn = sqlite3.connect('jobs.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs (country, jtype, city, title, desc, contact) VALUES (?, ?, ?, ?, ?, ?)", (country, jtype, city, title, desc, contact))
    conn.commit()
    conn.close()

# ================= СОСТОЯНИЯ =================
class JobState(StatesGroup):
    choosing_country = State()
    choosing_type = State()

class AdminState(StatesGroup):
    country = State()
    jtype = State()
    city = State()
    title = State()
    desc = State()
    contact = State()

# ================= ПРОВЕРКА ПОДПИСКИ =================
async def check_sub(user_id):
    if not CHANNEL_ID: return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]: return True
    except Exception: pass
    return False

# ================= КЛАВИАТУРЫ =================
def countries_kb(back_data=None):
    buttons = []
    row = []
    for i, c in enumerate(COUNTRIES, 1):
        row.append(InlineKeyboardButton(text=c, callback_data=f"country:{c}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    if back_data:
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=back_data)])
    else:
        buttons.append([InlineKeyboardButton(text="👨‍💻 Админ-панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def types_kb(country):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Онлайн", callback_data=f"type:онлайн:{country}")],
        [InlineKeyboardButton(text="🏢 Оффлайн", callback_data=f"type:оффлайн:{country}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back:countries")],
    ])

def cities_kb(country, cities, jtype):
    buttons = []
    row = []
    for i, city in enumerate(cities, 1):
        row.append(InlineKeyboardButton(text=city, callback_data=f"city:{city}:{jtype}:{country}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    if jtype == "онлайн":
        buttons.append([InlineKeyboardButton(text="🌐 Все города", callback_data=f"city:all:онлайн:{country}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:countries")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def restart_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔁 В начало", callback_data="restart")]])

def sub_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/rabotanomer1_2026")],
        [InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub")]
    ])

# ================= ХЕНДЛЕРЫ =================
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    if not await check_sub(msg.from_user.id):
        await msg.answer("⚠️ Для использования бота подпишись на наш канал!", reply_markup=sub_kb())
        return
    await msg.answer(f"👋 Привет, <b>{msg.from_user.first_name}</b>!\nВыбери страну 👇", reply_markup=countries_kb(), parse_mode="HTML")
    await state.set_state(JobState.choosing_country)

@dp.callback_query(F.data == "check_sub")
async def cb_check_sub(cb: CallbackQuery, state: FSMContext):
    if await check_sub(cb.from_user.id):
        await cb.message.edit_text("✅ Подписка подтверждена!\nВыбери страну 👇", reply_markup=countries_kb())
        await state.set_state(JobState.choosing_country)
    else:
        await cb.answer("❌ Ты еще не подписался!", show_alert=True)

@dp.callback_query(F.data.startswith("country:"))
async def choose_country(cb: CallbackQuery, state: FSMContext):
    country = cb.data.split(":")[1]
    await state.update_data(country=country)
    await cb.message.edit_text(f"🌍 Страна: <b>{country}</b>\nВыбери тип 👇", reply_markup=types_kb(country), parse_mode="HTML")
    await state.set_state(JobState.choosing_type)

@dp.callback_query(F.data.startswith("type:"))
async def choose_type(cb: CallbackQuery, state: FSMContext):
    _, jtype, country = cb.data.split(":", 2)
    cities = REGIONS.get(country, [])
    await cb.message.edit_text(f"🌍 Страна: <b>{country}</b> | {'💻 Онлайн' if jtype == 'онлайн' else '🏢 Оффлайн'}\nВыбери город 👇", reply_markup=cities_kb(country, cities, jtype), parse_mode="HTML")

@dp.callback_query(F.data.startswith("city:"))
async def choose_city(cb: CallbackQuery, state: FSMContext):
    _, city, jtype, country = cb.data.split(":", 3)
    jobs = get_jobs_db(country, jtype) if city == "all" else get_jobs_db(country, jtype, city)
    title_text = f"🌐 Все города | {country}\n🔎 Найдено: <b>{len(jobs)}</b>" if city == "all" else f"🏙 Город: <b>{city}</b>\n🔎 Найдено: <b>{len(jobs)}</b>"
    if not jobs:
        await cb.message.edit_text(f"😔 Пока нет вакансий ({city}).", reply_markup=restart_kb(), parse_mode="HTML")
        return
    await cb.message.edit_text(title_text, parse_mode="HTML")
    for job in jobs:
        await cb.message.answer(f"💼 <b>{job[0]}</b>\n\n📝 {job[1]}\n\n📞 <b>Контакты:</b>\n{job[2]}", parse_mode="HTML")
    await cb.message.answer("Хочешь ещё? 👇", reply_markup=restart_kb())
    await state.clear()

@dp.callback_query(F.data == "restart")
async def restart(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Выбери страну 👇", reply_markup=countries_kb())

@dp.callback_query(F.data == "back:countries")
async def back_countries(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Выбери страну 👇", reply_markup=countries_kb())
    await state.set_state(JobState.choosing_country)

# ================= АДМИНКА =================
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("⛔ У тебя нет прав!", show_alert=True)
        return
    await cb.message.edit_text("👨‍💻 <b>Админ-панель</b>\nВыбери страну:", reply_markup=countries_kb(back_data="restart"), parse_mode="HTML")
    await state.set_state(AdminState.country)

@dp.callback_query(AdminState.country, F.data.startswith("country:"))
async def admin_country(cb: CallbackQuery, state: FSMContext):
    country = cb.data.split(":")[1]
    await state.update_data(country=country)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💻 Онлайн", callback_data="adm_type:онлайн")], [InlineKeyboardButton(text="🏢 Оффлайн", callback_data="adm_type:оффлайн")], [InlineKeyboardButton(text="🔙 Назад", callback_data="restart")]])
    await cb.message.edit_text(f"Страна: {country}\nВыбери тип:", reply_markup=kb)
    await state.set_state(AdminState.jtype)

@dp.callback_query(AdminState.jtype, F.data.startswith("adm_type:"))
async def admin_type(cb: CallbackQuery, state: FSMContext):
    jtype = cb.data.split(":")[1]
    await state.update_data(jtype=jtype)
    data = await state.get_data()
    cities = REGIONS.get(data['country'], [])
    await cb.message.edit_text(f"Страна: {data['country']}\nВыбери город:", reply_markup=cities_kb(data['country'], cities, jtype))
    await state.set_state(AdminState.city)

@dp.callback_query(AdminState.city, F.data.startswith("city:"))
async def admin_city(cb: CallbackQuery, state: FSMContext):
    _, city, jtype, country = cb.data.split(":", 3)
    await state.update_data(city=city if city != "all" else "—")
    await cb.message.edit_text("Введи название вакансии:")
    await state.set_state(AdminState.title)

@dp.message(AdminState.title)
async def admin_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Введи описание (график, зарплата):")
    await state.set_state(AdminState.desc)

@dp.message(AdminState.desc)
async def admin_desc(msg: Message, state: FSMContext):
    await state.update_data(desc=msg.text)
    await msg.answer("Введи контакты (телефон или @username):")
    await state.set_state(AdminState.contact)

@dp.message(AdminState.contact)
async def admin_contact(msg: Message, state: FSMContext):
    data = await state.get_data()
    add_job_db(data['country'], data['jtype'], data['city'], data['title'], data['desc'], msg.text)
    await msg.answer("✅ <b>Вакансия успешно добавлена!</b>", reply_markup=restart_kb(), parse_mode="HTML")
    await state.clear()

# ================= ЗАПУСК (FLASK + BOT) =================
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_bot():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
