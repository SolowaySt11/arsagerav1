from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import io

TOKEN = "8776459772:AAGNtlF2uFC22z_oM4Fcha_GKk_Ho6jkWnI"

# ---------- ФУНКЦИЯ ЗАГРУЗКИ ВСЕХ ДАННЫХ ФОНДА ----------
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

# ---------- РАСЧЁТ ИЗМЕНЕНИЙ ЗА ПЕРИОДЫ ----------
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

# ---------- ФОРМИРОВАНИЕ ТЕКСТА ОТВЕТА ----------
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

# ---------- ПОСТРОЕНИЕ ГРАФИКА ----------
async def send_chart(update, fund_code, fund_name, period_days):
    data = get_all_fund_data(fund_code)
    if not data:
        await update.callback_query.edit_message_text(f"❌ Нет данных для построения графика {fund_name}")
        return
    
    # Берём данные за последние period_days дней
    cutoff_date = datetime.now() - timedelta(days=period_days)
    filtered = []
    for entry in data:
        entry_date = datetime.strptime(entry['date'], "%Y-%m-%d")
        if entry_date >= cutoff_date:
            filtered.append(entry)
    
    if not filtered:
        await update.callback_query.edit_message_text(f"❌ Недостаточно данных для периода {period_days} дней")
        return
    
    dates = [datetime.strptime(item['date'], "%Y-%m-%d") for item in filtered]
    prices = [item['nav_per_share'] for item in filtered]
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, prices, marker='o', linestyle='-', linewidth=2, markersize=4)
    plt.title(f"{fund_name} — динамика за {period_days} дней")
    plt.xlabel("Дата")
    plt.ylabel("Стоимость пая, ₽")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    
    # Сохраняем в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches="tight")
    buf.seek(0)
    plt.close()
    
    # Отправляем
    await update.callback_query.message.reply_photo(buf, caption=f"📈 {fund_name} — динамика за {period_days} дней")

# ---------- МЕНЮ АКЦИЙ (заглушка) ----------
async def stocks_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🛢️ Газпром", callback_data="GAZP")],
        [InlineKeyboardButton("🏦 Сбербанк", callback_data="SBER")],
        [InlineKeyboardButton("⛽ Лукойл", callback_data="LKOH")],
        [InlineKeyboardButton("🌐 Яндекс", callback_data="YDEX")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📈 Выбери акцию:", reply_markup=reply_markup)

# ---------- ГЛАВНОЕ МЕНЮ ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Фонд акций", callback_data="fa")],
        [InlineKeyboardButton("📊 Смешанный фонд", callback_data="f4si")],
        [InlineKeyboardButton("📉 Облигации KP 1.55", callback_data="fo")],
        [InlineKeyboardButton("📈 Акции", callback_data="stocks")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🏦 *Арсагера — Аналитика фондов*\n\n"
        "Выбери фонд или акции.\n\n"
        "📌 *Акции* временно недоступны. Ведутся технические работы.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ---------- МЕНЮ ДРАГМЕТАЛЛОВ ----------
async def metals_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🥇 Золото", callback_data="gold")],
        [InlineKeyboardButton("🥈 Серебро", callback_data="silver")],
        [InlineKeyboardButton("💍 Платина", callback_data="PLAT")],
        [InlineKeyboardButton("🪨 Палладий", callback_data="PLD")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🪙 Выбери драгоценный металл:", reply_markup=reply_markup)

# ---------- МЕНЮ ВАЛЮТ ----------
async def currencies_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("🇺🇸 Доллар", callback_data="USD")],
        [InlineKeyboardButton("🇪🇺 Евро", callback_data="EUR")],
        [InlineKeyboardButton("🇨🇳 Юань", callback_data="CNY")],
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("💵 Выбери валюту:", reply_markup=reply_markup)

# ---------- ОБРАБОТЧИК КНОПОК ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await start(update, context)
        return

    # Меню акций (заглушка)
    if data == "stocks":
        await stocks_menu(update, context)
        return

    # Фонды
    if data in ["fa", "f4si", "fo"]:
        fund_names = {"fa": "📈 Фонд акций", "f4si": "📊 Смешанный фонд", "fo": "📉 Облигации KP 1.55"}
        text = format_response(data, fund_names[data])
        # Добавляем кнопку "📈 График"
        keyboard = [[InlineKeyboardButton("📈 График за месяц", callback_data=f"graph_{data}_30")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        return

    # Графики
    if data.startswith("graph_"):
        parts = data.split("_")
        fund_code = parts[1]
        days = int(parts[2])
        fund_names = {"fa": "Фонд акций", "f4si": "Смешанный фонд", "fo": "Облигации KP 1.55"}
        await send_chart(update, fund_code, fund_names[fund_code], days)
        return

    # Если неизвестный callback — покажем меню
    await start(update, context)

# ---------- HELP ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй /start для начала работы.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Бот Арсагера (с графиками) запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()