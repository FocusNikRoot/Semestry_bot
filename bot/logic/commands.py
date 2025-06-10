import requests, datetime, deepl
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.logic.log import log_message
from config.settings import deepl_token, kinopoisk_unofficial_token, kinopoisk_dev_token, weather_token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Привет! Доступные команды:\n" \
          "Вспомогательные:\n" \
          "  /weather <город> — Прогноз погоды\n" \
          "  /map <локация> — Координаты локации + карта\n" \
          "  /translate <текст> — Перевод текста на русский\n" \
          "  /affirmation — Случайная аффирмация\n" \
          "Основные:\n" \
          "  /movie <название> — Подробнее о фильме\n" \
          "  /most_wanted — Ожидаемые фильмы месяца"
    await update.message.reply_text(msg, reply_markup=get_main_keyboard())
    await log_message(update, f"User: {update.message.text}\nBot: {msg}")
    
async def translate(text, target_lang='ru'):
    deepl_client = deepl.DeepLClient(deepl_token)
    try:
        result = deepl_client.translate_text(text, target_lang=target_lang)
    except Exception:
        return "Ошибка соединения с переводчиком..."
    return result if result else "Не удалось перевести текст."

async def get_posters(film_id):
    return f"https://kinopoiskapiunofficial.tech/images/posters/kp/{film_id}.jpg"

async def get_details(film_id):
    url = f"https://api.kinopoisk.dev/v1.4/movie/{film_id}"
    headers = {
        'X-API-KEY': kinopoisk_dev_token,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('description', 'Нет описания')
        else:
            return "Ошибка получения данных о фильме."
    except Exception:
        return "Ошибка соединения с сервером..."

async def get_actual_month():
    month = datetime.datetime.now().month
    dict_month = {
        1: "JANUARY",
        2: "FEBRUARY",
        3: "MARCH",
        4: "APRIL",
        5: "MAY",
        6: "JUNE",
        7: "JULY",
        8: "AUGUST",
        9: "SEPTEMBER",
        10: "OCTOBER",
        11: "NOVEMBER",
        12: "DECEMBER"       
    }
    return dict_month.get(month)
    
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = "Укажите город: /weather <город>"
        await update.message.reply_text(msg)
        await log_message(update, f"User: {update.message.text}\nBot: {msg}")
        return
    city = ' '.join(context.args)
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_token}&lang=ru&units=metric"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            msg = f"Погода в {city}:\n" \
                  f"{data['weather'][0]['description'].capitalize()}\n🌡 Температура: *{data['main']['temp']}°C*\n" \
                  f"🌡 Ощущается как *{data['main']['feels_like']}°C*\n\n" \
                  f"💦 Влажность: *{data['main']['humidity']}%*\n🌫 Давление: *{data['main']['pressure']} гПа*\n\n" \
                  f"💨 Скорость ветра: *{data['wind']['speed']} м/с*\n↗️ Направление: *{data['wind']['deg']}°*"
            icon_id = data['weather'][0]['icon']
            icon_url = f"http://openweathermap.org/img/wn/{icon_id}@2x.png"
            await update.message.reply_photo(photo=icon_url, caption=msg, parse_mode="Markdown")
        else:
            msg = "Город не найден."
            error_picture = "./assets/img/cat-404-error.jpg"
            await update.message.reply_photo(photo=error_picture, caption=msg)
    except Exception:
        msg = "Ошибка соединения с сервером..."
        await update.message.reply_text(msg)
    await log_message(update, f"User: {update.message.text}\nBot: {msg}")

async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = "Укажите название фильма: /movie <название>"
        await update.message.reply_text(msg)
        await log_message(update, f"User: {update.message.text}\nBot: {msg}")
        return
    movie = ' '.join(context.args)
    search_url = f"https://www.kinopoisk.ru/index.php?kp_query={movie}"
    try:
        resp = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(resp.text, 'html.parser')
        film_content = soup.select_one('.search_results .element')
        if film_content:
            title = film_content.select_one('.info .name a').text.strip()
            rating = film_content.select_one('.rating')
            year = film_content.select_one('.info .name .year').text.strip()
            full_name = film_content.select_one('.info .gray').text.strip()
            rating_text = rating.text.strip() if rating else "Нет рейтинга"
            film_id = film_content.select_one('.info .name a')['href'].split('/')[2]
            poster = await get_posters(film_id)
            
            msg = f"{title} ({year})\n{full_name}.\n\n" \
                  f"*Рейтинг: {rating_text}/10*⭐️\n\n" \
                  f"Описание:\n{await get_details(film_id)}\n\n" \
                  f"[Ссылочка *Тык*](https://www.kinopoisk.ru{film_content.select_one('.info .name a')['href']})"
            if poster:
                await update.message.reply_photo(photo=poster, caption=msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            msg = "Фильм не найден."
            error_picture = "./assets/img/cat-404-error.jpg"
            await update.message.reply_photo(photo=error_picture, caption=msg)
    except Exception:
        msg = "Ошибка соединения с сервером..."
        await update.message.reply_text(msg)
    await log_message(update, f"User: {update.message.text}\nBot: {msg}")
    
async def most_wanted(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = 0
    await send_most_wanted(update, context, page, edit=False)

async def most_wanted_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        page = int(query.data.split("_")[-1])
    except Exception:
        await query.message.reply_text("Нет данных")
        return
    await send_most_wanted(update, context, page, edit=True)

async def send_most_wanted(update, context, page, edit):
    year = datetime.datetime.now().year
    month = await get_actual_month()
    url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/premieres?year={year}&month={month}"
    try:
        resp = requests.get(url, headers={
                'X-API-KEY': kinopoisk_unofficial_token,
                'Content-Type': 'application/json'
            })
        if resp.status_code == 200:
            data = resp.json()
            items = data['items']
            per_page = 10
            total_pages = (len(items) + per_page - 1) // per_page
            start = page * per_page
            end = start + per_page
            msg = f"Фильмы месяца (стр. {page+1}/{total_pages}):\n\n"
            for item in items[start:end]:
                msg += (
                    f"🎬 [{item['nameRu']}](https://www.kinopoisk.ru/film/{item['kinopoiskId']}/) "
                    f"({item['year']}) {item.get('duration', '?')} мин.\n"
                    f"📆 Дата премьеры: {item.get('premiereRu', 'неизвестно')}\n"
                    f"[Купить билет 🎟](https://www.kinopoisk.ru/film/{item['kinopoiskId']}/afisha/city/1/)\n\n"
                )
            keyboard = get_most_wanted_keyboard(page, total_pages)
            if edit:
                await update.callback_query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")
            await log_message(update, f"User: {getattr(update.message, 'text', '')}\nBot: {msg}")
        else:
            msg = "Ошибка получения данных."
            if edit:
                await update.callback_query.edit_message_text(msg)
            else:
                await update.message.reply_text(msg)
    except Exception:
        msg = "Ошибка соединения с сервером..."
        if edit:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)

def get_most_wanted_keyboard(page, total_pages):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"most_wanted_{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("Далее ➡️", callback_data=f"most_wanted_{page+1}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None

async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = "Укажите город, адрес или название заведения: /map <локация>"
        await update.message.reply_text(msg)
        await log_message(update, f"User: {update.message.text}\nBot: {msg}")
        return
    city = ' '.join(context.args)
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}"
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = resp.json()
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        msg = f"Координаты {city}: {lat}, {lon}"
        await update.message.reply_text(msg)
        await update.message.reply_location(latitude=float(lat), longitude=float(lon))
    else:
        msg = "Не нашлось :с."
        error_picture = "./assets/img/cat-404-error.jpg"
        await update.message.reply_photo(photo=error_picture, caption=msg)
    await log_message(update, f"User: {update.message.text}\nBot: {msg}")

async def translate_user_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = "Введите текст для перевода."
        await update.message.reply_text(msg)
        await log_message(update, f"User: {update.message.text}\nBot: {msg}")
        return
    text = ' '.join(context.args)
    translated_text = await translate(text)
    msg = f"Источник:\n{text}\n\n" \
          f"Перевод:\n{translated_text}"
    await update.message.reply_text(msg)
    await log_message(update, f"User: {update.message.text}\nBot: {msg}")

async def random_affirmations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://www.affirmations.dev/"
    resp = requests.get(url)
    if resp.status_code == 200:
        affirmation = resp.json().get('affirmation')
        ru_affirmation = await translate(affirmation)
        msg = f"{affirmation}\n\n-=-=-=-=-На русском-=-=-=-=-\n\n{ru_affirmation}"
    else:
        affirmation = "Мы ошибаемся - это нормально! Каждая ошибка - это ценный опыт."
        msg = f"{affirmation}"

    
    await update.message.reply_text(msg)
    await log_message(update, f"User: {update.message.text}\nBot: {msg}")
    
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Неизвестная команда. Введите /help для списка команд."
    await update.message.reply_text(msg)
    await log_message(update, f"User: {update.message.text}\nBot: {msg}")

def get_main_keyboard():
    keyboard = [
        ["/affirmation", "/most_wanted"],
        [           "/help"             ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)