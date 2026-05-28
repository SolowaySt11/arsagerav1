from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from datetime import datetime

TOKEN = "8776459772:AAGNtlF2uFC22z_oM4Fcha_GKk_Ho6jkWnI"

# ---------- ФУНКЦИЯ ПОЛУЧЕНИЯ ДАННЫХ ФОНДА ----------
def get_fund_metrics(fund_code):
    url = f"https://arsagera.ru/api/v1/funds/{fund_code}/fund-metrics/"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('data'):
                # Сортируем по дате в убывающем порядке (сначала новые)
                sorted_data = sorted(data['data'], key=lambda x: x['date'], reverse=True)
                latest = sorted_data[0]
                return {
                    'date': latest['date'],
                    'price': latest['nav_per_share'],
                    'assets': latest.get('total_net_assets', 0)
                }
        return None
    except Exception as e:
        print(f"Ошибка API для {fund_code}: {e}")
        return None

# ---------- ГЛАВНОЕ МЕНЮ ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📈 Фонд акций (fa)", callback_data="fa")],
        [InlineKeyboardButton("📊 Смешанный фонд (f4si)", callback_data="f4si")],
        [InlineKeyboardButton("📉 Облигации KP 1.55 (fo)", callback_data="fo")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🏦 *Арсагера — Аналитика фондов*\n\n"
        "Выбери фонд для получения текущей стоимости пая:",
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
        data = get_fund_metrics(fund_code)
        if data:
            date_obj = datetime.strptime(data['date'], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")
            price_str = f"{data['price']:,.2f}".replace(",", " ")

            # Базовый текст
            text = (
                f"{fund_names[fund_code]}\n\n"
                f"💰 Стоимость пая: *{price_str}* ₽\n"
                f"📅 Данные на {formatted_date}\n\n"
                f"📊 *Изменения:*"
            )

            # Пробуем добавить аналитику (если есть в ответе API)
            # Поля могут называться иначе — подстрой под реальный JSON
            # Сначала проверим, есть ли данные в ответе
            # Это пример, адаптируй под реальные ключи из API
            try:
                # Если API возвращает изменения за периоды
                # Например: 'nav_per_share_change_1m' — за месяц
                # 'nav_per_share_change_3m' — за 3 месяца
                # 'nav_per_share_change_6m' — за полгода
                # 'nav_per_share_change_ytd' — с начала года

                # Это ПРИМЕР — замени на реальные ключи из твоего JSON
                changes = {
                    "За 1 месяц": data.get('nav_per_share_change_1m'),
                    "За 3 месяца": data.get('nav_per_share_change_3m'),
                    "За 6 месяцев": data.get('nav_per_share_change_6m'),
                    "С начала года": data.get('nav_per_share_change_ytd')
                }

                for period, value in changes.items():
                    if value is not None:
                        sign = "+" if value > 0 else ""
                        text += f"\n• {period}: {sign}{value:.2f}%"
            except Exception as e:
                # Если с аналитикой что-то пошло не так — просто пропускаем
                print(f"Ошибка при добавлении аналитики: {e}")
                pass

            await query.edit_message_text(text, parse_mode="Markdown")
        else:
            text = f"❌ Не удалось получить данные для {fund_names[fund_code]}"
            await query.edit_message_text(text, parse_mode="Markdown")
        return

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