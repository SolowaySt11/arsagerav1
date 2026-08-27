from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import io
import os

TOKEN = "8776459772:AAHJZrqZ_IYOGpP6OD67dkG1GOBdHaC0XLo"

# ===== ЛЕКЦИИ =====
LECTURES = [
    {
        "id": "lecture_1",
        "title": "📚 Введение в инвестиции",
        "description": "Базовые понятия: что такое инвестиции, виды активов, риск и доходность.",
        "file_id": "ВАШ_FILE_ID_1"  # Замени на реальный file_id из Telegram
    },
    # Добавляй сюда новые лекции по мере добавления
]

def get_lecture_buttons():
    """Создаёт кнопки для лекций"""
    keyboard = []
    for lecture in LECTURES:
        keyboard.append([InlineKeyboardButton(lecture["title"], callback_data=f"lecture_{lecture['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

# ===== ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ =====

def get_all_fund_data(fund_code):
    url = f"https://arsagera.ru/api/v1/funds/{fund_code}/fund-metrics/"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('data'):
                return sorted(data['data'], key=lambda x: x['date'])
        return []
    except Exception as e:
        print(f"Ошибка API для {fund_code}: {e}")
        return []

def calculate_changes(data, current_price):
    if not data:
        return {}
    target_dates = {
        '1 день': datetime.now() - timedelta(days=1),
        '1 неделя': datetime.now() - timedelta(weeks=1),
        '1 месяц': datetime.now() - relativedelta(months=1),
        '3 месяца': datetime.now() - relativedelta(months=3),
        '1 год': datetime.now() - relativedelta(years=1),
        '5 лет': datetime.now() - relativedelta(years=5)
    }
    changes = {}
    for period, target_date in target_dates.items():
        closest = None
        closest_diff = None
        for entry in data:
            entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
            if entry_date <= target_date:
                diff = (target_date - entry_date).days
                if closest_diff is None or diff < closest_diff:
                    closest_diff = diff
                    closest = entry
        if closest:
            old_price = closest['nav_per_share']
            rub_change = current_price - old_price
            percent_change = (rub_change / old_price) * 100 if old_price != 0 else 0
            changes[period] = {'rub': rub_change, 'percent': percent_change, 'old_date': closest['date']}
    return changes

def format_response(fund_code, fund_name):
    data = get_all_fund_data(fund_code)
    if not data:
        return f"❌ Не удалось получить данные для {fund_name}"
    latest = data[-1]
    current_price = latest['nav_per_share']
    current_date = latest['date']
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    price_str = f"{current_price:,.2f}".replace(",", " ")
    changes = calculate_changes(data, current_price)
    text = f"{fund_name}\n\n💰 Стоимость пая: *{price_str}* ₽\n📅 Данные на {formatted_date}\n\n📊 *Изменения:*\n"
    for period, change in changes.items():
        sign = "+" if change['rub'] >= 0 else ""
        rub_str = f"{sign}{change['rub']:,.2f}".replace(",", " ")
        percent_str = f"{sign}{change['percent']:.2f}".replace(".", ",")
        emoji = "🟢" if change['percent'] >= 0 else "🔴"
        text += f"▫️ *За {period}:* {emoji} {percent_str}% ({rub_str} ₽)\n"
    return text

async def send_chart(update, fund_code, fund_name, period_days, period_name):
    data = get_all_fund_data(fund_code)
    if not data:
        await update.callback_query.message.reply_text(f"❌ Нет данных для построения графика {fund_name}")
        return
    cutoff_date = datetime.now() - timedelta(days=period_days)
    filtered = [entry for entry in data if datetime.strptime(entry['date'], "%Y-%m-%d") >= cutoff_date]
    if not filtered:
        await update.callback_query.message.reply_text(f"❌ Недостаточно данных для периода {period_name}")
        return
    dates = [datetime.strptime(item['date'], "%Y-%m-%d") for item in filtered]
    prices = [item['nav_per_share'] for item in filtered]
    plt.figure(figsize=(10, 5))
    plt.plot(dates, prices, marker='o', linestyle='-', linewidth=2, markersize=4)
    plt.title(f"{fund_name} — динамика за {period_name}")
    plt.xlabel("Дата")
    plt.ylabel("Стоимость пая, ₽")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches="tight")
    buf.seek(0)
    plt.close()
    await update.callback_query.message.reply_photo(buf, caption=f"📈 {fund_name} — динамика за {period_name}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Фонд акций", callback_data="fa")],
        [InlineKeyboardButton("📊 Смешанный фонд", callback_data="f4si")],
        [InlineKeyboardButton("📉 Облигации KP 1.55", callback_data="fo")],
        [InlineKeyboardButton("📊 Аналитика (сравнение)", callback_data="analytics")],
        [InlineKeyboardButton("🎓 Курс лекций", callback_data="lectures")],
        [InlineKeyboardButton("📊 Новости фондов", callback_data="check_changes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔶 *Арсагера — Аналитика фондов*\n\n"
        "Выбери фонд для детальной аналитики, посмотри новости или пройди курс лекций.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def lectures_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню с лекциями"""
    query = update.callback_query
    keyboard = get_lecture_buttons()
    await query.edit_message_text(
        "🎓 *Курс лекций по инвестициям*\n\n"
        "Выбери лекцию для прослушивания:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def send_lecture(update: Update, context: ContextTypes.DEFAULT_TYPE, lecture_id: str):
    """Отправляет аудио-лекцию"""
    query = update.callback_query
    
    # Находим лекцию по ID
    lecture = next((l for l in LECTURES if l["id"] == lecture_id), None)
    if not lecture:
        await query.edit_message_text("❌ Лекция не найдена")
        return
    
    # Если есть file_id, отправляем аудио
    if lecture.get("file_id"):
        try:
            await query.edit_message_text(f"🎧 Отправляю лекцию: {lecture['title']}...")
            await update.effective_chat.send_audio(
                audio=lecture["file_id"],
                caption=f"🎓 *{lecture['title']}*\n\n{lecture['description']}",
                parse_mode="Markdown",
                title=lecture["title"]
            )
            
            # Возвращаемся в меню лекций
            await update.effective_chat.send_message(
                "📚 Выбери следующую лекцию:",
                reply_markup=get_lecture_buttons()
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка при отправке лекции: {str(e)}")
    else:
        await query.edit_message_text(
            f"❌ Аудиофайл для лекции *{lecture['title']}* не найден.\n\n"
            f"Пожалуйста, добавьте file_id в список LECTURES.",
            parse_mode="Markdown"
        )

async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1 день", callback_data="analytics_1")],
        [InlineKeyboardButton("1 неделя", callback_data="analytics_7")],
        [InlineKeyboardButton("1 месяц", callback_data="analytics_30")],
        [InlineKeyboardButton("3 месяца", callback_data="analytics_90")],
        [InlineKeyboardButton("1 год", callback_data="analytics_365")],
        [InlineKeyboardButton("5 лет", callback_data="analytics_1825")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📊 *Аналитика фондов*\n\nВыбери период для сравнения:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def analytics_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("1 день", callback_data="analytics_1")],
        [InlineKeyboardButton("1 неделя", callback_data="analytics_7")],
        [InlineKeyboardButton("1 месяц", callback_data="analytics_30")],
        [InlineKeyboardButton("3 месяца", callback_data="analytics_90")],
        [InlineKeyboardButton("1 год", callback_data="analytics_365")],
        [InlineKeyboardButton("5 лет", callback_data="analytics_1825")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📊 *Аналитика фондов*\n\nВыбери период для сравнения:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def send_analytics_chart(update, period_days, period_name):
    query = update.callback_query
    funds = {
        "fa": ("Фонд акций", "blue"),
        "f4si": ("Смешанный фонд", "green"),
        "fo": ("Облигации KP 1.55", "orange")
    }
    
    cutoff_date = datetime.now() - timedelta(days=period_days)
    
    plt.figure(figsize=(10, 5))
    
    for code, (name, color) in funds.items():
        data = get_all_fund_data(code)
        if not data:
            continue
        filtered = [entry for entry in data if datetime.strptime(entry['date'], "%Y-%m-%d") >= cutoff_date]
        if not filtered:
            continue
        dates = [datetime.strptime(item['date'], "%Y-%m-%d") for item in filtered]
        prices = [item['nav_per_share'] for item in filtered]
        plt.plot(dates, prices, label=name, color=color, linewidth=2)
    
    if not plt.gca().has_data():
        await query.edit_message_text("❌ Недостаточно данных для построения аналитики.")
        return
    
    plt.title(f"Динамика фондов Арсагеры за {period_name}")
    plt.xlabel("Дата")
    plt.ylabel("Стоимость пая, ₽")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.xticks(rotation=45)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches="tight")
    buf.seek(0)
    plt.close()
    
    await update.effective_chat.send_photo(photo=buf, caption=f"📊 Динамика фондов Арсагеры за {period_name}")

async def check_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализирует изменения фондов за последние 3 дня"""
    funds = {
        "fa": "📈 Фонд акций",
        "f4si": "📊 Смешанный фонд",
        "fo": "📉 Облигации KP 1.55"
    }
    
    result = "📊 *Новости фондов за последние 3 дня*\n\n"
    threshold = 2.0
    
    for code, name in funds.items():
        data = get_all_fund_data(code)
        if not data or len(data) < 2:
            result += f"{name}: ❌ нет данных\n"
            continue
            
        current = data[-1]['nav_per_share']
        
        target_date = datetime.now() - timedelta(days=3)
        closest = None
        closest_diff = None
        
        for entry in data:
            entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
            if entry_date <= target_date:
                diff = (target_date - entry_date).days
                if closest_diff is None or diff < closest_diff:
                    closest_diff = diff
                    closest = entry
        
        if closest:
            old_price = closest['nav_per_share']
            change_percent = ((current - old_price) / old_price) * 100
            
            if change_percent > threshold:
                status = f"📈 рост (+{round(change_percent, 2)}%)"
            elif change_percent < -threshold:
                status = f"📉 падение ({round(change_percent, 2)}%)"
            else:
                status = f"⚖️ стабильно ({round(change_percent, 2)}%)"
            
            result += f"{name}: {status}\n"
        else:
            result += f"{name}: ❌ нет данных за 3 дня\n"
    
    result += f"\n🔔 Порог срабатывания: ±{threshold}%\n"
    result += "📌 Для подробной статистики — /start"
    
    await update.message.reply_text(result, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await query.message.delete()
        keyboard = [
            [InlineKeyboardButton("📈 Фонд акций", callback_data="fa")],
            [InlineKeyboardButton("📊 Смешанный фонд", callback_data="f4si")],
            [InlineKeyboardButton("📉 Облигации KP 1.55", callback_data="fo")],
            [InlineKeyboardButton("📊 Аналитика (сравнение)", callback_data="analytics")],
            [InlineKeyboardButton("🎓 Курс лекций", callback_data="lectures")],
            [InlineKeyboardButton("📊 Новости фондов", callback_data="check_changes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_chat.send_message(
            "🔶 *Арсагера — Аналитика фондов*\n\n"
            "Выбери фонд для детальной аналитики, посмотри новости или пройди курс лекций.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    if data == "analytics":
        await analytics_menu(update, context)
        return

    if data == "lectures":
        await lectures_menu(update, context)
        return

    if data == "check_changes":
        # Создаём фейковый update для check_changes
        await check_changes(update, context)
        return

    if data.startswith("lecture_"):
        lecture_id = data[8:]  # Убираем "lecture_"
        await send_lecture(update, context, lecture_id)
        return

    if data in ["fa", "f4si", "fo"]:
        fund_names = {"fa": "📈 Фонд акций", "f4si": "📊 Смешанный фонд", "fo": "📉 Облигации KP 1.55"}
        text = format_response(data, fund_names[data])
        keyboard = [
            [InlineKeyboardButton("📈 1 день", callback_data=f"graph_{data}_1")],
            [InlineKeyboardButton("📈 1 неделя", callback_data=f"graph_{data}_7")],
            [InlineKeyboardButton("📈 1 месяц", callback_data=f"graph_{data}_30")],
            [InlineKeyboardButton("📈 3 месяца", callback_data=f"graph_{data}_90")],
            [InlineKeyboardButton("📈 1 год", callback_data=f"graph_{data}_365")],
            [InlineKeyboardButton("📈 5 лет", callback_data=f"graph_{data}_1825")],
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        return

    if data.startswith("graph_"):
        parts = data.split("_")
        fund_code = parts[1]
        days = int(parts[2])
        fund_names = {"fa": "Фонд акций", "f4si": "Смешанный фонд", "fo": "Облигации KP 1.55"}
        period_names = {1: "1 день", 7: "1 неделя", 30: "1 месяц", 90: "3 месяца", 365: "1 год", 1825: "5 лет"}
        period_name = period_names.get(days, f"{days} дней")
        await query.edit_message_text(f"📈 Строю график за {period_name}, подождите...")
        await send_chart(update, fund_code, fund_names[fund_code], days, period_name)
        return

    if data.startswith("analytics_"):
        days = int(data.split("_")[1])
        period_names = {1: "1 день", 7: "1 неделя", 30: "1 месяц", 90: "3 месяца", 365: "1 год", 1825: "5 лет"}
        period_name = period_names.get(days, f"{days} дней")
        await query.edit_message_text(f"📊 Строю аналитику за {period_name}, подождите...")
        await send_analytics_chart(update, days, period_name)
        return

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Доступные команды:*\n\n"
        "/start — Главное меню\n"
        "/analytics — Аналитика фондов\n"
        "/check — Новости фондов за 3 дня\n"
        "/help — Помощь",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("check", check_changes))
    app.add_handler(CommandHandler("analytics", analytics_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("Бот Арсагера с лекциями запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()