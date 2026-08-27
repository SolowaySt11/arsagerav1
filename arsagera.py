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
        "title": "📚 Лекция 1. Инвестиции: трудности выбора",
        "description": "Базовые понятия: что такое инвестиции, виды активов, риск и доходность.",
        "file_id": "CQACAgIAAxkBAAIBsmqQpNoNR85Hd-d7k6H6X9bAZt7zAAKxoQACjCeBSBw3muirYi02PQQ"
    },
]