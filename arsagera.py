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
        "file_id": "СЮДА ВСТАВИШЬ FILE_ID ПОСЛЕ ОТПРАВКИ"  # ⬅️ ⬅️ ⬅️
    },
]