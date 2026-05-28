from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

TOKEN = "8776459772:AAGNtlF2uFC22z_oM4Fcha_GKk_Ho6jkWnI"

# ---------- ФУНКЦИЯ ЗАГРУЗКИ ВСЕХ ДАННЫХ ФОНДА ----------
def get_all_fund_data(fund_code):
    url = f"https://arsagera.ru/api/v1/funds/{fund_code}/fund-metrics/"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('data'):
                # Сортируем по дате (старые → новые)
                return sorted(data['data'], key=lambda x: x['date'])
        return []
    except Exception as e:
        print(f"Ошибка API для {fund_code}: {e}")
        return []

# ---------- РАСЧЁТ ИЗМЕНЕНИЙ ЗА ПЕРИОДЫ ----------
def calculate_changes(data, current_price):
    if not data:
        return {}
    
    # Словарь с целевыми датами для каждого периода
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
        # Ищем ближайшую запись к целевой дате
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
    
    latest = data[-1]  # последняя запись (самая свежая)
    current_price = latest['nav_per_share']
    current_date = latest['date']
    
    # Форматируем дату
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    # Цена с пробелами как разделителями тысяч
    price_str = f"{current_price:,.2f}".replace(",", " ")
    
    # Рассчитываем изменения
    changes = calculate_changes(data, current_price)
    
    # Собираем текст
    text = f"{fund_name}\n\n💰 Стоимость пая: *{price_str}* ₽\n📅 Данные на {formatted_date}\n\n📊 *Изменения:*\n"
    
    for period, change in changes.items():
        sign = "+" if change['rub'] >= 0 else ""
        rub_str = f"{sign}{change['rub']:,.2f}".replace(",", " ")
        percent_str = f"{sign}{change['percent']:.2f}".replace(".", ",")
        if change['percent'] >= 0:
            emoji = "🟢"
        else:
            emoji = "🔴"
        text += f"▫️ *За {period}:* {emoji} {percent_str}% ({rub_str} ₽)\n"
    
    return text

# ---------- ГЛАВНОЕ МЕНЮ ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Фонд акций", callback_data="fa")],
        [InlineKeyboardButton("📊 Смешанный фонд", callback_data="f4si")],
        [InlineKeyboardButton("📉 Облигации KP 1.55", callback_data="fo")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔶 *Арсагера — Аналитика фондов*\n\n"
        "Выбери фонд для получения текущей стоимости пая и динамики изменения:\n"
        "Данные рассчитаны по динамике цен на ближайшие к календарным даты, могут отличаться от официальных отчётов УК на ±1–2%»",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ---------- ОБРАБОТЧИК КНОПОК ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    fund_code = query.data
    
    fund_names = {
        "fa": "📈 Фонд акций",
        "f4si": "📊 Смешанный фонд",
        "fo": "📉 Облигации KP 1.55"
    }
    
    if fund_code in fund_names:
        text = format_response(fund_code, fund_names[fund_code])
        await query.edit_message_text(text, parse_mode="Markdown")
        return
    
    # Если неизвестный callback — просто покажем меню
    await start(update, context)

# ---------- HELP ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй /start для начала работы.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Бот Арсагера запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()