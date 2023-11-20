from aiogram import types, Dispatcher
from Bot_telegram.create_bot import bot
from datetime import datetime
import pymongo
from Bot_telegram.handlers.password import mangodbpassword
import re
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext


mongo_client = pymongo.MongoClient(f"mongodb+srv://{mangodbpassword}@cluster0.inrqtd0.mongodb.net/")
db = mongo_client.Telegram_bot
collection = db["Telegram_bot"]

date = datetime.now().date()
formatted_date = date.strftime("%d-%m-%Y")

keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
btn1 = types.InlineKeyboardButton("За сьогодні", callback_data="today")
btn2 = types.InlineKeyboardButton("За цей місяць", callback_data="tomonth")
keyboard.add(btn1, btn2)


class Form(StatesGroup):
    waiting_conduct_expenses = State()
    waiting_find_cost = State()
    waiting_delete_data = State()
    waiting_past_day = State()
    waiting_product_past_day = State()


async def add_user(user_id):
    existing_user = collection.find_one({"_id": user_id})
    if existing_user:
        print(f"Користувач {user_id} вже існує в базі даних.")
    else:
        print(f"Додавання користувача {user_id} з датою {formatted_date} до бази даних.")
        result = collection.insert_one({
            "_id": user_id,
            "date": str(formatted_date),
        })

        if result.acknowledged:
            print(f"Дані користувача {user_id} були успішно додані.")
        else:
            print(f"Помилка під час додавання даних користувачу {user_id}.")


# START
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mrk1 = types.KeyboardButton("Вести свої витрати")
    mrk2 = types.KeyboardButton("Дізнатися скільки витратив")
    mrk3 = types.KeyboardButton("Всього витратено")
    mrk4 = types.KeyboardButton("Видали пункт про витрати")
    mrk5 = types.KeyboardButton("Вести витрати за минулі дні")
    markup.add(mrk1, mrk2, mrk3, mrk4, mrk5)
    await bot.send_message(message.from_user.id, f"Привіт {message.from_user.first_name}! Я бот який допоможе тобі контролювати твої витрати", reply_markup=markup)
    await add_user(message.chat.id)


# ПІДКАЗКА ЩО РОБИТИ ДАЛІ
async def button_handler(message: types.Message):
    if message.text == "Вести свої витрати":
        await Form.waiting_conduct_expenses.set()
        await bot.send_message(message.from_user.id, "Ведіть дані у форматі 'продукт - ціна'")
    if message.text == "Дізнатися скільки витратив":
        await Form.waiting_find_cost.set()
        await bot.send_message(message.from_user.id, "За яке число вас цікавлять витрати? Формат повідомлення дд-мм-рр", reply_markup=keyboard)
    if message.text == "Видали пункт про витрати":
        await Form.waiting_delete_data.set()
        await bot.send_message(message.from_user.id, "За яку дату ви хочете видалити дані? Формат повідомлення дд-мм-рр.")
    if message.text == "Всього витратено":
        cost = await total_cost(message.chat.id)
        await bot.send_message(message.from_user.id, cost)
    if message.text == "Вести витрати за минулі дні":
        await Form.waiting_past_day.set()
        await bot.send_message(message.from_user.id, "За яке число ви хочете вести дані? Формат повідомлення дд.мм.рр.")


# ВЕСТИ ТОВАР
async def conduct_expenses(message: types.Message, state: FSMContext):
    if message.text == "Дізнатися скільки витратив":
        await state.finish()
        await Form.waiting_find_cost.set()
        await bot.send_message(message.from_user.id, "За яке число вас цікавлять витрати? формат повідомлення дд.мм.рр", reply_markup=keyboard)
    elif message.text == "Видали пункт про витрати":
        await Form.waiting_delete_data.set()
        await bot.send_message(message.from_user.id, "За яку дату ви хочете видалити дані? Формат повідомлення дд.мм.рр.")
    elif message.text == "Вести свої витрати":
        await state.finish()
        await Form.waiting_conduct_expenses.set()
        await bot.send_message(message.from_user.id, "Ведіть дані у форматі 'продукт - ціна'")
    elif message.text == "Всього витратено":
        await state.finish()
        cost = await total_cost(message.chat.id)
        await bot.send_message(message.from_user.id, cost)
    elif message.text == "Вести витрати за минулі дні":
        await state.finish()
        await Form.waiting_past_day.set()
        await bot.send_message(message.from_user.id, "За яке число ви хочете вести дані? Формат повідомлення дд.мм.рр.")
    else:
        pattern = re.compile(r"^(.+)\s*-\s*(\d+(\.\d{1,2})?)$")
        match = pattern.match(message.text)
        if match:
            product, price = match.groups()[0], match.groups()[1]
            await bot.send_message(message.from_user.id, f"Записую ваші данні {product}, {price}")
            existing_user = collection.find_one({"_id": message.chat.id})
            if existing_user:
                dani = f"dani{date.year}.{date.month}"
                collection.update_one(
                    {"_id": message.chat.id},
                    {"$push": {dani: f"{formatted_date}, {product} - {price}"}}
                )
            else:
                await bot.send_message(message.from_user.id, "Щось пішло не так")
        else:
            await bot.send_message(message.from_user.id, "Я вас не розумію, потрібний формат: 'продукт - ціна', не забувате про дефіс")


# ДІЗНАТИСЯ СКІЛЬКИ ВИТРАТИВ
async def find_cost(message: types.Message, state: FSMContext):
    if message.text == "Дізнатися скільки витратив":
        await state.finish()
        await Form.waiting_find_cost.set()
        await bot.send_message(message.from_user.id, "За яке число вас цікавлять витрати? формат повідомлення дд.мм.рр", reply_markup=keyboard)
    elif message.text == "Видали пункт про витрати":
        await Form.waiting_delete_data.set()
        await bot.send_message(message.from_user.id, "За яку дату ви хочете видалити дані? Формат повідомлення дд.мм.рр.")
    elif message.text == "Вести свої витрати":
        await state.finish()
        await Form.waiting_conduct_expenses.set()
        await bot.send_message(message.from_user.id, "Ведіть дані у форматі 'продукт - ціна'")
    elif message.text == "Всього витратено":
        await state.finish()
        cost = await total_cost(message.chat.id)
        await bot.send_message(message.from_user.id, cost)
    elif message.text == "Вести витрати за минулі дні":
        await state.finish()
        await Form.waiting_past_day.set()
        await bot.send_message(message.from_user.id, "За яке число ви хочете вести дані? Формат повідомлення дд.мм.рр.")
    else:
        grn = 0
        product = []
        pattern_one_data = re.compile(r"^(\d{2}-\d{2}-\d{4})")
        dani = f"dani{message.text[-4:]}"
        if pattern_one_data.match(message.text):
            document = (collection.find_one({"_id": message.chat.id}, {dani: 1, "_id": 0}))
            for entry in document[dani][message.text[3:-5]]:
                if message.text in entry:
                    comma_index = entry.find(',')
                    product.append(entry[comma_index + 2:])
                    match_grn = re.search(r"\d+$", entry)
                    if match_grn:
                        grn += int(match_grn.group(0))
            main_product = ",".join(product).replace(",", "\n")
            await bot.send_message(message.from_user.id, f"Товари які ви купляли \n {main_product} \nВсього вийшло: {grn}")
            await state.finish()
        else:
            await bot.send_message(message.from_user.id, "Я вас не розумію, потрібний формат: 'дд-мм-рр', не забувайте про дефіс ")


# ІНЛАЙН КНОПКИ ДЛЯ ДІЗНАТИСЯ СКІЛЬКИ ВИТРАТИВ
async def call_back_data(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    all_mounth = []
    all_today = []
    sum_grn = 0
    document = (collection.find_one({"_id": callback_query.message.chat.id}, {"dani2023": 1, "_id": 0}))
    if callback_query.data == "today":
        for entry in document["dani2023"][str(date.month)]:
            if entry[:10] == str(formatted_date):
                all_today.append(entry[12:])
                match_grn = re.search(r"\d+$", entry)
                sum_grn += int(match_grn.group(0))
        all_today = ",".join(all_today).replace(",", "\n")
        await bot.send_message(callback_query.message.chat.id, f"{all_today}\nВсього витрачено за сьогодні: {sum_grn}")
        await state.finish()
    if callback_query.data == "tomonth":
        for entry in document["dani2023"][str(date.month)]:
            all_mounth.append(entry[12:])
            match_grn = re.search(r"\d+$", entry)
            sum_grn += int(match_grn.group(0))
        all_mounth = ",".join(all_mounth).replace(",", "\n")
        await bot.send_message(callback_query.message.chat.id, f"{all_mounth}\nВсього витрачено за цей місяць: {sum_grn}")
        await state.finish()


# ВИДАЛЕННЯ ДАНИХ
async def delete_data(message: types.Message, state: FSMContext):
    if message.text == "Дізнатися скільки витратив":
        await state.finish()
        await Form.waiting_find_cost.set()
        await bot.send_message(message.from_user.id, "За яке число вас цікавлять витрати? формат повідомлення дд.мм.рр", reply_markup=keyboard)
    elif message.text == "Видали пункт про витрати":
        await Form.waiting_delete_data.set()
        await bot.send_message(message.from_user.id, "За яку дату ви хочете видалити дані? Формат повідомлення дд.мм.рр.")
    elif message.text == "Вести свої витрати":
        await state.finish()
        await Form.waiting_conduct_expenses.set()
        await bot.send_message(message.from_user.id, "Ведіть дані у форматі 'продукт - ціна'")
    elif message.text == "Всього витратено":
        await state.finish()
        cost = await total_cost(message.chat.id)
        await bot.send_message(message.from_user.id, cost)
    elif message.text == "Вести витрати за минулі дні":
        await state.finish()
        await Form.waiting_past_day.set()
        await bot.send_message(message.from_user.id, "За яке число ви хочете вести дані? Формат повідомлення дд.мм.рр.")
    else:
        pattern_one_data = re.compile(r"^(\d{2}-\d{2}-\d{4})")
        if pattern_one_data.match(message.text):
            delete_keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
            document = (collection.find_one({"_id": message.chat.id}, {"dani2023": 1, "_id": 0}))
            for entry in document["dani2023"][message.text[3:-5]]:
                if message.text in entry:
                    delete_button = types.InlineKeyboardButton(entry[12:], callback_data=entry)
                    delete_keyboard.add(delete_button)
            await bot.send_message(message.from_user.id, "Що саме ви хочете видалити", reply_markup=delete_keyboard)
        else:
            await bot.send_message(message.from_user.id, "Я вас не розумію, потрібний формат: 'дд-мм-рр', не забувайте про дефіс ")


# ІНЛАЙН КНОПКИ ДЛЯ ВИДАЛЕННЯ ОБ'ЄКТА
async def delete_call_bacl_data(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    callback_data = callback_query.data
    dani = ("dani2023."+str(date.month))
    collection.update_one(
        {"_id": callback_query.message.chat.id},
        {"$pull": {dani: callback_data}}
    )
    await bot.send_message(callback_query.message.chat.id, f"Ви видалили :{callback_data[12:]}")


# ВСЬОГО ВИТРАТИЛИ
async def total_cost(user_id):
    total_grn = 0
    document = (collection.find_one({"_id": user_id}, {"dani2023": 1, "_id": 0}))
    for entry in document["dani2023"]:
        for month in document["dani2023"][entry]:
            match_grn = re.search(r"\d+$", month)
            if match_grn:
                total_grn += int(match_grn.group(0))
    date_document = (collection.find_one({"_id": 873674161}))
    start_data = date_document["date"]
    return f"З періодна з {start_data} по {formatted_date} ви витратилм: {total_grn}"


# УКАЗАТИ ДЕНЬ ЗА ЯКІ ВОДИТИ ДАНІ
async def past_days(message: types.Message, state: FSMContext):
    if message.text == "Дізнатися скільки витратив":
        await state.finish()
        await Form.waiting_find_cost.set()
        await bot.send_message(message.from_user.id, "За яке число вас цікавлять витрати? формат повідомлення дд.мм.рр", reply_markup=keyboard)
    elif message.text == "Видали пункт про витрати":
        await Form.waiting_delete_data.set()
        await bot.send_message(message.from_user.id, "За яку дату ви хочете видалити дані? Формат повідомлення дд.мм.рр.")
    elif message.text == "Вести свої витрати":
        await state.finish()
        await Form.waiting_conduct_expenses.set()
        await bot.send_message(message.from_user.id, "Ведіть дані у форматі 'продукт - ціна'")
    elif message.text == "Всього витратено":
        await state.finish()
        cost = await total_cost(message.chat.id)
        await bot.send_message(message.from_user.id, cost)
    elif message.text == "Вести витрати за минулі дні":
        await state.finish()
        await Form.waiting_past_day.set()
        await bot.send_message(message.from_user.id, "За яке число ви хочете вести дані? Формат повідомлення дд.мм.рр.")
    else:
        pattern_one_data = re.compile(r"^(\d{2}-\d{2}-\d{4})")
        if pattern_one_data.match(message.text):
            async with state.proxy() as data:
                data['date'] = message.text
            await state.finish()
            await Form.waiting_product_past_day.set()
            await bot.send_message(message.from_user.id, "Ведіть дані у форматі 'продукт - ціна'")
        else:
            await bot.send_message(message.from_user.id, "Я вас не розумію, потрібний формат: 'дд-мм-рр', не забувайте про дефіс ")


# ВЕСТИ ДАНІ ЗА ІНШИЙ ДЕНЬ
async def product_past_days(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data_past_day = data.get('date', None)
    pattern = re.compile(r"^(.+)\s*-\s*(\d+(\.\d{1,2})?)$")
    match = pattern.match(message.text)
    if match:
        product, price = match.groups()[0], match.groups()[1]
        await bot.send_message(message.from_user.id, f"Записую ваші данні {product}, {price} за дату {data_past_day}")
        dani = f"dani2023.{data_past_day[3:5]}"
        collection.update_one(
            {"_id": message.chat.id},
            {"$push": {dani: f"{ data_past_day}, {product} - {price}"}}
        )


# РЕГІСТР
def register_handler_client(dp: Dispatcher):
    dp.register_message_handler(start, commands=["start"])
    dp.register_message_handler(button_handler, lambda message: message.text in ["Вести свої витрати", "Дізнатися скільки витратив", "Всього витратено", "Видали пункт про витрати", "Вести витрати за минулі дні"], state=None)
    dp.register_message_handler(conduct_expenses, state=Form.waiting_conduct_expenses)
    dp.register_message_handler(find_cost, state=Form.waiting_find_cost)
    dp.register_message_handler(delete_data, state=Form.waiting_delete_data)
    dp.register_callback_query_handler(call_back_data, lambda c: c.data in ['tomonth', "today"], state=Form.waiting_find_cost)
    dp.register_callback_query_handler(delete_call_bacl_data, state=Form.waiting_delete_data)
    dp.register_message_handler(past_days, state=Form.waiting_past_day)
    dp.register_message_handler(product_past_days, state=Form.waiting_product_past_day)
