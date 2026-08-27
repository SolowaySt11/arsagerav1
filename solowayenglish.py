from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3
import os
import json
import matplotlib.pyplot as plt
import io
import hashlib
import re

TOKEN = "8681728801:AAFNkjp2eeIZ3KYEOnpXgIu3IowwERXSEWM"
DB_PATH = "/data/english.db"

# ===== ЗАГРУЗКА ВСЕХ JSON ФАЙЛОВ =====

def load_all_tests():
    TESTS = {}
    level_map = {
        "A1 (Beginner)": "A1",
        "A2 (Elementary)": "A2",
        "B1 (Intermediate)": "B1",
        "B2 (Upper-Intermediate)": "B2"
    }
    base_path = os.path.dirname(__file__)
    
    for level_name, level_key in level_map.items():
        TESTS[level_name] = {}
        
        grammar_file = os.path.join(base_path, f"{level_key}_grammar.json")
        if os.path.exists(grammar_file):
            try:
                with open(grammar_file, "r", encoding="utf-8") as f:
                    grammar_data = json.load(f)
                    TESTS[level_name]["Грамматика"] = grammar_data
                print(f"✅ Загружена грамматика для {level_name}")
            except Exception as e:
                print(f"❌ Ошибка загрузки {grammar_file}: {e}")
                TESTS[level_name]["Грамматика"] = {}
        else:
            print(f"⚠️ Файл не найден: {grammar_file}")
            TESTS[level_name]["Грамматика"] = {}
        
        vocabulary_file = os.path.join(base_path, f"{level_key}_vocabulary.json")
        if os.path.exists(vocabulary_file):
            try:
                with open(vocabulary_file, "r", encoding="utf-8") as f:
                    vocab_data = json.load(f)
                    TESTS[level_name]["Лексика"] = vocab_data
                print(f"✅ Загружена лексика для {level_name}")
            except Exception as e:
                print(f"❌ Ошибка загрузки {vocabulary_file}: {e}")
                TESTS[level_name]["Лексика"] = {}
        else:
            print(f"⚠️ Файл не найден: {vocabulary_file}")
            TESTS[level_name]["Лексика"] = {}
    
    return TESTS

print("📂 Загрузка JSON файлов...")
TESTS = load_all_tests()

print("\n📊 Загруженные данные:")
for level in TESTS:
    print(f"  📚 {level}:")
    for cat in TESTS[level]:
        topics = TESTS[level][cat]
        print(f"    📂 {cat}: {len(topics)} тем")

# ===== TOPICS =====
TOPICS = {
    "A1 (Beginner)": {
        "Грамматика": [
            "Глагол to be (am/is/are)",
            "Личные местоимения (I, you, he, she, it, we, they)",
            "Объектные местоимения (me, him, her, us, them)",
            "Притяжательные местоимения (my/mine, your/yours)",
            "Указательные местоимения (this, that, these, those)",
            "Неопределённые местоимения (some, any, no)",
            "Множественное число существительных",
            "Притяжательный падеж ('s)",
            "Артикли (a/an, the)",
            "Present Simple",
            "Present Continuous",
            "Present Simple vs Present Continuous",
            "Past Simple (was/were, правильные глаголы)",
            "Past Simple (неправильные глаголы, топ-20)",
            "Future Simple (will)",
            "Конструкция to be going to",
            "Предлоги места (in, on, under, next to, behind)",
            "Предлоги времени (at, on, in)",
            "Порядок слов в утверждении (SVO)",
            "Общие вопросы (Do you…? Is he…?)",
            "Специальные вопросы (What, Where, When)",
            "Вопросы к подлежащему (Who lives here?)",
            "Повелительное наклонение (Open the door!)",
            "Союзы (and, but, or, because)",
            "Конструкция like + ing",
            "Модальный глагол can/can't",
            "There is / There are",
            "Наречия частоты (always, never, sometimes, often)"
        ],
        "Лексика": [
            "Цифры, числа, даты, время",
            "Дни недели, месяцы, времена года",
            "Семья (mother, father, sister, brother)",
            "Дом и комната (furniture, rooms)",
            "Еда и напитки (food, drink)",
            "Одежда и цвета (clothes, colours)",
            "Школа и школьные предметы",
            "Хобби и свободное время",
            "Описание людей (tall, short, kind, funny)",
            "Город и транспорт (places, prepositions)",
            "Погода (sunny, rainy, hot, cold)",
            "Повседневные действия (get up, have breakfast, go to school)"
        ]
    },
    "A2 (Elementary)": {
        "Грамматика": [
            "Past Continuous (I was doing)",
            "Present Perfect (I have done) — опыт, результат",
            "Present Perfect vs Past Simple",
            "Present Perfect Continuous (I have been doing)",
            "Future forms: will / going to / Present Continuous",
            "Конструкция used to",
            "Степени сравнения прилагательных",
            "Сравнительные конструкции (as…as, not as…as, than)",
            "Порядок прилагательных",
            "Наречия образа действия (quickly, well, fast)",
            "Модальные глаголы (must, have to, should, may, might, could)",
            "Предлоги времени (for, since, during, by, until)",
            "Предлоги места (in, on, at, behind, between)",
            "Предлоги движения (to, into, out of, through, along)",
            "Количественные слова (some, any, much, many, a lot of)",
            "Неопределённые местоимения (somebody, anybody, nobody)",
            "Возвратные местоимения (myself, yourself, himself)",
            "Союзы (because, so, although, however)",
            "Косвенная речь (база: He said that…)",
            "Условные предложения 0 и 1 типа",
            "Пассивный залог (база: is done, was done)",
            "Вопросы разделительные (You like coffee, don't you?)",
            "Вопросы косвенные (Can you tell me where…)"
        ],
        "Лексика": [
            "Путешествия и транспорт",
            "Еда и заказ в кафе",
            "Внешность и характер",
            "Семья и отношения",
            "Образование и экзамены",
            "Работа и профессии",
            "Город и ориентация",
            "Погода и времена года",
            "Покупки и одежда",
            "Здоровье и тело"
        ]
    },
    "B1 (Intermediate)": {
        "Грамматика": [
            "Past Perfect (I had done)",
            "Past Perfect vs Past Simple",
            "Present Perfect Continuous (углублённо)",
            "Future Continuous (I will be doing)",
            "Future Perfect (I will have done)",
            "Условные предложения 2 и 3 типа",
            "Сослагательное наклонение (I wish… / If only…)",
            "Конструкция be/get used to + ing",
            "Герундий и инфинитив (remember to do vs remember doing)",
            "Модальные глаголы в прошлом (must have, might have)",
            "Пассивный залог (все времена)",
            "Косвенная речь (вопросы, просьбы, приказы)",
            "Определительные придаточные (who, which, that, whose)",
            "Артикли (углублённо, включая нулевой артикль)",
            "Предлоги (углублённо: despite, in spite of, due to)",
            "Фразовые глаголы (get up, turn on, look for, give up)",
            "Инверсия (Never have I seen…)"
        ],
        "Лексика": [
            "Путешествия и культура",
            "Технологии и интернет",
            "Экология и окружающая среда",
            "Работа и карьера",
            "Образование",
            "Здоровье и медицина",
            "Медиа и новости",
            "Отношения и общение",
            "Искусство и литература",
            "Финансы и деньги"
        ]
    },
    "B2 (Upper-Intermediate)": {
        "Грамматика": [
            "Все времена (активный и пассивный залог)",
            "Все условные предложения (смешанные типы)",
            "Сослагательное наклонение после suggest, recommend, insist",
            "Модальные глаголы для выражения предположений",
            "Инверсия в условных предложениях (Had I known…)",
            "Эмфатические конструкции (It is … that… / What … is…)",
            "Сложные союзы (nonetheless, whereas, thereby, hence)",
            "Фразовые глаголы (углублённо, с несколькими значениями)",
            "Сложные герундиальные и инфинитивные обороты",
            "Пунктуация и стилистика"
        ],
        "Лексика": [
            "Бизнес и экономика",
            "Наука и технологии",
            "Политика и общество",
            "Юриспруденция и право",
            "Психология и саморазвитие",
            "Глобальные проблемы",
            "Культура и традиции (глубоко)",
            "Маркетинг и реклама",
            "Переговоры и убеждение",
            "Реферирование и пересказ"
        ]
    }
}

# ===== БАЗА ДАННЫХ =====

def init_db():
    try:
        os.makedirs("/data", exist_ok=True)
    except:
        pass
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        level TEXT,
        category TEXT,
        topic TEXT,
        done INTEGER DEFAULT 0,
        UNIQUE(user_id, level, topic)
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        level TEXT,
        category TEXT,
        topic TEXT,
        score INTEGER,
        total INTEGER,
        date TEXT
    )""")
    
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
                  ("admin", admin_password, 1))
        print("✅ Создан аккаунт администратора (логин: admin, пароль: admin123)")
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, password, is_admin FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        hashed = hash_password(password)
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 0)", 
                  (username, hashed))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None

def get_progress(user_id, level):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT topic, done FROM progress WHERE user_id = ? AND level = ?", (user_id, level))
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def toggle_topic(user_id, level, category, topic):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT done FROM progress WHERE user_id = ? AND level = ? AND topic = ?", 
              (user_id, level, topic))
    row = c.fetchone()
    if row:
        new_status = 0 if row[0] else 1
        c.execute("UPDATE progress SET done = ? WHERE user_id = ? AND level = ? AND topic = ?", 
                  (new_status, user_id, level, topic))
    else:
        new_status = 1
        c.execute("INSERT INTO progress (user_id, level, category, topic, done) VALUES (?, ?, ?, ?, ?)", 
                  (user_id, level, category, topic, 1))
    conn.commit()
    conn.close()
    return new_status

def save_test_result(user_id, level, category, topic, score, total):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO test_results (user_id, level, category, topic, score, total, date) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))", 
              (user_id, level, category, topic, score, total))
    conn.commit()
    conn.close()

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def has_test(level, topic):
    try:
        if level not in TESTS:
            return False
        for cat in TESTS[level]:
            if topic in TESTS[level][cat]:
                if "questions" in TESTS[level][cat][topic]:
                    return True
    except:
        pass
    return False

def find_topic_index(level, category, topic_name):
    if level in TOPICS and category in TOPICS[level]:
        topics = TOPICS[level][category]
        for idx, topic in enumerate(topics):
            if topic == topic_name:
                return idx
    return 0

def generate_table_image(headers, rows, topic):
    fig, ax = plt.subplots(figsize=(10, len(rows) * 0.5 + 1))
    ax.axis('off')
    table = ax.table(cellText=rows, colLabels=headers, cellLoc='left', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    for (i, j), cell in table.get_celld().items():
        cell.set_edgecolor('#2c3e50')
        if i == 0:
            cell.set_facecolor('#3498db')
            cell.set_text_props(color='white', weight='bold')
        elif i % 2 == 0:
            cell.set_facecolor('#ecf0f1')
        else:
            cell.set_facecolor('white')
    plt.title(topic, fontsize=14, weight='bold', pad=20)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

# ===== ОСНОВНЫЕ ОБРАБОТЧИКИ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔑 Войти", callback_data="login")],
        [InlineKeyboardButton("📝 Зарегистрироваться", callback_data="register")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 *Добро пожаловать в Soloway English Tracker!*\n\n"
        "У тебя уже есть аккаунт? Войди или зарегистрируйся!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔑 *Вход*\n\nВведи логин и пароль двумя сообщениями.",
        parse_mode="Markdown"
    )
    context.user_data["awaiting_login"] = True

async def show_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 *Регистрация*\n\nЛогин: 3+ букв/цифр. Пароль: 4+ символов.\n\nВведи логин, потом пароль.",
        parse_mode="Markdown"
    )
    context.user_data["awaiting_register"] = True

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if context.user_data.get("awaiting_login"):
        if not context.user_data.get("login_username"):
            context.user_data["login_username"] = text
            await update.message.reply_text("✅ Теперь введи пароль:")
        else:
            username = context.user_data.get("login_username")
            password = text
            user = get_user(username)
            if user and user[2] == hash_password(password):
                context.user_data["authenticated"] = True
                context.user_data["user_id"] = user[0]
                context.user_data["username"] = user[1]
                context.user_data["is_admin"] = user[3]
                context.user_data.pop("awaiting_login", None)
                context.user_data.pop("login_username", None)
                await update.message.reply_text(f"✅ Добро пожаловать, {username}!")
                await show_levels(update, context)
            else:
                context.user_data.pop("awaiting_login", None)
                context.user_data.pop("login_username", None)
                await update.message.reply_text("❌ Неверный логин или пароль.")
    
    elif context.user_data.get("awaiting_register"):
        if not context.user_data.get("reg_username"):
            if re.match(r'^[a-zA-Z0-9_]{3,}$', text):
                context.user_data["reg_username"] = text
                await update.message.reply_text("✅ Теперь введи пароль (мин. 4 символа):")
            else:
                await update.message.reply_text("❌ Логин должен содержать минимум 3 буквы или цифры.")
        else:
            username = context.user_data.get("reg_username")
            password = text
            if len(password) < 4:
                await update.message.reply_text("❌ Пароль должен быть минимум 4 символа.")
                return
            new_user_id = create_user(username, password)
            if new_user_id:
                context.user_data["authenticated"] = True
                context.user_data["user_id"] = new_user_id
                context.user_data["username"] = username
                context.user_data["is_admin"] = 0
                context.user_data.pop("awaiting_register", None)
                context.user_data.pop("reg_username", None)
                await update.message.reply_text(f"✅ Аккаунт создан! Добро пожаловать, {username}!")
                await show_levels(update, context)
            else:
                context.user_data.pop("awaiting_register", None)
                context.user_data.pop("reg_username", None)
                await update.message.reply_text("❌ Пользователь с таким логином уже существует.")
    
    elif context.user_data.get("awaiting_oge_word"):
        await handle_oge_word_input(update, context)
        return
    elif context.user_data.get("awaiting_fill_answer"):
        await handle_fill_answer(update, context)
        return
    elif context.user_data.get("awaiting_word_formation"):
        await handle_word_formation_answer(update, context)
        return
    elif context.user_data.get("awaiting_lexical_word"):
        await handle_lexical_word(update, context)
        return

async def show_levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if not user_id:
        await start(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("🎯 Тест на уровень (30 вопросов)", callback_data="diagnostic")],
        [InlineKeyboardButton("📚 A1 (Beginner)", callback_data="level_A1 (Beginner)")],
        [InlineKeyboardButton("📚 A2 (Elementary)", callback_data="level_A2 (Elementary)")],
        [InlineKeyboardButton("📚 B1 (Intermediate)", callback_data="level_B1 (Intermediate)")],
        [InlineKeyboardButton("📚 B2 (Upper-Intermediate)", callback_data="level_B2 (Upper-Intermediate)")],
        [InlineKeyboardButton("🎯 ОГЭ", callback_data="oge_menu")],
        [InlineKeyboardButton("📊 Общий прогресс", callback_data="total_progress")],
        [InlineKeyboardButton("🚪 Выйти", callback_data="logout")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"🎓 *Soloway English Tracker*\n\n👤 {context.user_data.get('username')}\n\nВыбери уровень:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.callback_query.answer("🚪 Выход...")
    keyboard = [
        [InlineKeyboardButton("🔑 Войти", callback_data="login")],
        [InlineKeyboardButton("📝 Зарегистрироваться", callback_data="register")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "👋 Ты вышел из аккаунта.",
        reply_markup=reply_markup
    )

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE, level):
    user_id = context.user_data.get("user_id")
    if not user_id:
        await start(update, context)
        return
    
    categories = list(TOPICS[level].keys())
    keyboard = []
    for cat in categories:
        progress = get_progress(user_id, level)
        total = len(TOPICS[level][cat])
        done = sum(1 for topic in TOPICS[level][cat] if progress.get(topic, 0))
        keyboard.append([InlineKeyboardButton(f"{cat} ({done}/{total})", callback_data=f"cat_{level}|{cat}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_levels")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(f"📚 {level}\n\nВыбери категорию:", reply_markup=reply_markup)

async def show_topics(update: Update, context: ContextTypes.DEFAULT_TYPE, level, category, page=0):
    user_id = context.user_data.get("user_id")
    if not user_id:
        await start(update, context)
        return
    
    topics = TOPICS[level][category]
    progress = get_progress(user_id, level)
    per_page = 8
    total_pages = (len(topics) + per_page - 1) // per_page
    if page < 0: page = 0
    if page >= total_pages: page = total_pages - 1
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(topics))
    keyboard = []
    for idx in range(start_idx, end_idx):
        topic = topics[idx]
        done = progress.get(topic, 0)
        emoji = "✅" if done else "⬜"
        keyboard.append([InlineKeyboardButton(f"{emoji} {topic}", callback_data=f"topic_{level}|{category}|{idx}")])
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"page_{level}|{category}|{page-1}"))
    nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"page_{level}|{category}|{page+1}"))
    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"level_{level}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    total = len(topics)
    done = sum(1 for t in topics if progress.get(t, 0))
    percent = int(done / total * 100) if total > 0 else 0
    bar = "🟩" * (percent // 10) + "⬜" * (10 - percent // 10)
    await update.callback_query.edit_message_text(
        f"📚 {level} → {category}\n\n{bar} {done}/{total} ({percent}%)\n\nСтр. {page+1}/{total_pages}:",
        reply_markup=reply_markup
    )

async def show_topic_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, level, category, idx):
    user_id = context.user_data.get("user_id")
    if not user_id:
        await start(update, context)
        return
    
    topics = TOPICS[level][category]
    topic = topics[int(idx)]
    progress = get_progress(user_id, level)
    done = progress.get(topic, 0)
    status = "✅ Пройдена" if done else "⬜ Не пройдена"
    
    has_expl = False
    try:
        if level in TESTS:
            for cat in TESTS[level]:
                if topic in TESTS[level][cat]:
                    expl = TESTS[level][cat][topic].get("explanation")
                    if expl and isinstance(expl, dict):
                        has_expl = True
                        break
    except:
        pass
    
    has_vocab = False
    try:
        if level in TESTS:
            for cat in TESTS[level]:
                if topic in TESTS[level][cat]:
                    vocab = TESTS[level][cat][topic].get("vocabulary")
                    if vocab:
                        has_vocab = True
                        break
    except:
        pass
    
    keyboard = [
        [InlineKeyboardButton("✅ Отметить" if not done else "❌ Снять отметку", callback_data=f"tog_{level}|{category}|{idx}")],
    ]
    if has_expl:
        keyboard.append([InlineKeyboardButton("📖 Теория", callback_data=f"expl_{level}|{category}|{idx}")])
    if has_vocab:
        keyboard.append([InlineKeyboardButton("📚 Словарь", callback_data=f"vocab_{level}|{category}|{idx}")])
    if has_test(level, topic):
        keyboard.append([InlineKeyboardButton("📝 Пройти тест (8 вопросов)", callback_data=f"test_{level}|{category}|{idx}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"cat_{level}|{category}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"📚 {topic}\n\n{status}\n\nВыбери действие:",
        reply_markup=reply_markup
    )

async def show_explanation(update: Update, context: ContextTypes.DEFAULT_TYPE, level, category, idx):
    topics = TOPICS[level][category]
    topic = topics[int(idx)]
    expl_data = None
    try:
        if level in TESTS:
            for cat in TESTS[level]:
                if topic in TESTS[level][cat]:
                    expl = TESTS[level][cat][topic].get("explanation")
                    if expl and isinstance(expl, dict):
                        expl_data = expl
                        break
    except:
        pass
    
    if not expl_data:
        await update.callback_query.answer("❌ Теория пока не добавлена", show_alert=True)
        return
    
    buf = generate_table_image(expl_data["headers"], expl_data["rows"], topic)
    keyboard = [[InlineKeyboardButton("🔙 К теме", callback_data=f"topic_{level}|{category}|{idx}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.callback_query.message.delete()
    except:
        pass
    await update.effective_chat.send_photo(photo=buf, caption=f"📖 {topic}", reply_markup=reply_markup)

async def show_vocabulary(update: Update, context: ContextTypes.DEFAULT_TYPE, level, category, idx):
    topics = TOPICS[level][category]
    topic = topics[int(idx)]
    vocab_data = None
    try:
        if level in TESTS:
            for cat in TESTS[level]:
                if topic in TESTS[level][cat]:
                    vocab = TESTS[level][cat][topic].get("vocabulary")
                    if vocab:
                        vocab_data = vocab
                        break
    except:
        pass
    
    if not vocab_data:
        await update.callback_query.answer("❌ Словарь пока не добавлен", show_alert=True)
        return
    
    if isinstance(vocab_data, list):
        for i, table in enumerate(vocab_data):
            buf = generate_table_image(table["headers"], table["rows"], f"{topic} (часть {i+1})")
            try:
                if i == 0:
                    await update.callback_query.message.delete()
            except:
                pass
            await update.effective_chat.send_photo(
                photo=buf,
                caption=f"📚 {topic} - Словарь" if i == 0 else "",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К теме", callback_data=f"topic_{level}|{category}|{idx}")]]) if i == len(vocab_data) - 1 else None
            )
    else:
        buf = generate_table_image(vocab_data["headers"], vocab_data["rows"], f"📚 {topic}")
        try:
            await update.callback_query.message.delete()
        except:
            pass
        await update.effective_chat.send_photo(
            photo=buf,
            caption=f"📚 {topic} - Словарь",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К теме", callback_data=f"topic_{level}|{category}|{idx}")]])
        )

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE, level, category, idx):
    user_id = context.user_data.get("user_id")
    if not user_id:
        await start(update, context)
        return
    
    topics = TOPICS[level][category]
    topic = topics[int(idx)]
    test_data = None
    try:
        if level in TESTS:
            for cat in TESTS[level]:
                if topic in TESTS[level][cat]:
                    if "questions" in TESTS[level][cat][topic]:
                        test_data = TESTS[level][cat][topic]
                        break
    except:
        pass
    
    if not test_data or "questions" not in test_data:
        await update.callback_query.answer("❌ Тест не найден", show_alert=True)
        return
    
    questions = test_data["questions"]
    context.user_data["test"] = {
        "level": level,
        "category": category,
        "topic": topic,
        "questions": questions,
        "current": 0,
        "score": 0,
        "user_answers": [],
        "user_id": user_id
    }
    await show_question(update, context)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test = context.user_data.get("test")
    if not test: return
    q_num = test["current"]
    if q_num >= len(test["questions"]):
        await finish_test(update, context)
        return
    question = test["questions"][q_num]
    options = question["options"]
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{chr(97+i)}) {opt}", callback_data=f"ans_{i}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"📝 *Тест: {test['topic']}*\n\nВопрос {q_num + 1}/{len(test['questions'])}:\n\n*{question['q']}*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_idx):
    test = context.user_data.get("test")
    if not test:
        await update.callback_query.answer("Тест не найден.")
        return
    question = test["questions"][test["current"]]
    correct = question["answer"]
    correct_ans = question["options"][correct]
    user_answer = question["options"][answer_idx]
    is_correct = (answer_idx == correct)
    test["user_answers"].append({
        "question": question["q"],
        "user_answer": user_answer,
        "correct_answer": correct_ans,
        "is_correct": is_correct
    })
    if is_correct:
        test["score"] += 1
        await update.callback_query.answer(f"✅ Правильно! ({correct_ans})")
    else:
        await update.callback_query.answer(
            f"❌ Твой ответ: {user_answer}. Правильно: {correct_ans}",
            show_alert=True
        )
    test["current"] += 1
    if test["current"] >= len(test["questions"]):
        await finish_test(update, context)
    else:
        await show_question(update, context)

async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test = context.user_data.get("test")
    if not test: return
    score = test["score"]
    total = len(test["questions"])
    percent = int(score / total * 100)
    user_id = test["user_id"]
    save_test_result(user_id, test["level"], test["category"], test["topic"], score, total)
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально!"
    elif percent >= 75:
        emoji, comment = "🎉", "Хороший результат!"
    elif percent >= 50:
        emoji, comment = "📚", "Неплохо! Но стоит повторить."
    else:
        emoji, comment = "💪", "Нужно подучить."
    
    wrong_answers = [ans for ans in test["user_answers"] if not ans["is_correct"]]
    idx = find_topic_index(test["level"], test["category"], test["topic"])
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти ещё раз", callback_data=f"test_{test['level']}|{test['category']}|{idx}")],
        [InlineKeyboardButton("🔙 К теме", callback_data=f"topic_{test['level']}|{test['category']}|{idx}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    result_text = f"{emoji} *Тест завершён!*\n\n📝 {test['topic']}\n📊 Результат: {score}/{total} ({percent}%)\n\n{comment}"
    if wrong_answers:
        result_text += f"\n\n❌ *Ошибки: {len(wrong_answers)} из {total}*"
    
    await update.callback_query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    if wrong_answers:
        for i in range(0, len(wrong_answers), 2):
            chunk = wrong_answers[i:i+2]
            error_text = "*❌ Ошибки:*\n\n"
            for j, wrong in enumerate(chunk, i+1):
                error_text += f"{j}. *{wrong['question']}*\n   ❌ Ваш ответ: {wrong['user_answer']}\n   ✅ Правильно: {wrong['correct_answer']}\n\n"
            await update.effective_chat.send_message(error_text, parse_mode="Markdown")
    
    del context.user_data["test"]

async def toggle_topic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, level, category, idx):
    user_id = context.user_data.get("user_id")
    if not user_id:
        await start(update, context)
        return
    
    topics = TOPICS[level][category]
    topic = topics[int(idx)]
    new_status = toggle_topic(user_id, level, category, topic)
    await update.callback_query.answer(f"{'✅ Отмечено!' if new_status else '❌ Снято!'}")
    await show_topic_menu(update, context, level, category, idx)

async def oge_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎧 1. Аудирование (выбор ответа)", callback_data="start_audio_choice")],
        [InlineKeyboardButton("🎧 2. Аудирование (сопоставление)", callback_data="start_audio_matching")],
        [InlineKeyboardButton("📝 3. Аудирование (заполнение пропусков)", callback_data="start_audio_fill")],
        [InlineKeyboardButton("📖 4. Работа с текстом", callback_data="oge_reading")],
        [InlineKeyboardButton("📝 5. Словообразование", callback_data="start_word_formation")],
        [InlineKeyboardButton("📝 6. Лексико-грамматика", callback_data="start_lexical_grammar")],
        [InlineKeyboardButton("✉️ 7. Письмо (скоро)", callback_data="oge_letter")],
        [InlineKeyboardButton("📖 8. Чтение текста (скоро)", callback_data="oge_text_reading")],
        [InlineKeyboardButton("🎤 9. Монолог (скоро)", callback_data="oge_monologue")],
        [InlineKeyboardButton("📱 10. Electronic Assistant (скоро)", callback_data="oge_assistant")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_levels")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🎯 *ОГЭ — подготовка к экзамену*\n\n"
        "Выбери раздел для тренировки:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ===== ОГЭ: РАБОТА С ТЕКСТОМ (МЕНЮ) =====

async def oge_reading_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📌 Сопоставление (матчинг)", callback_data="oge_matching")],
        [InlineKeyboardButton("✅ True / False / Not Stated", callback_data="oge_tfns")],
        [InlineKeyboardButton("🔙 Назад", callback_data="oge_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "📖 *Работа с текстом*\n\n"
        "Выбери тип задания:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ===== ОГЭ: МАТЧИНГ (СОПОСТАВЛЕНИЕ) =====

def load_oge_matching():
    try:
        with open("oge_matching.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

async def start_oge_matching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_oge_matching()
    if not data:
        await update.callback_query.answer("❌ Файл с заданиями не найден!", show_alert=True)
        return
    
    texts = data["texts"]
    keyboard = []
    for text in texts:
        display_name = f"{text['id'].replace('oge_text_', '')}. {text['title']}"
        keyboard.append([InlineKeyboardButton(f"📄 {display_name}", callback_data=f"oge_match_show_{text['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="oge_reading")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "📌 *Сопоставление (матчинг)*\n\n"
        "Выбери текст:\n"
        "Вопросы 1–7, абзацы A–F. Один вопрос без ответа.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_oge_matching_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text_id):
    data = load_oge_matching()
    if not data:
        await update.callback_query.answer("❌ Ошибка загрузки", show_alert=True)
        return
    
    selected_text = None
    for text in data["texts"]:
        if text["id"] == text_id:
            selected_text = text
            break
    
    if not selected_text:
        await update.callback_query.answer("❌ Текст не найден", show_alert=True)
        return
    
    context.user_data["oge_matching_session"] = {
        "text_data": selected_text,
        "current_question": 0,
        "score": 0,
        "user_answers": [],
        "questions": selected_text["questions"]
    }
    
    text_message = f"📖 *{selected_text['title']}*\n\n{selected_text['text']}"
    await update.callback_query.edit_message_text(
        text_message,
        parse_mode="Markdown"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Начать отвечать", callback_data=f"oge_match_start_{text_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_chat.send_message(
        "Готов(а)? Нажимай! 🚀",
        reply_markup=reply_markup
    )

async def start_oge_matching_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_oge_matching_question(update, context)

async def show_oge_matching_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.user_data.get("oge_matching_session")
    if not session:
        await update.callback_query.answer("❌ Сессия не найдена", show_alert=True)
        return
    
    current = session["current_question"]
    questions = session["questions"]
    
    if current >= len(questions):
        await finish_oge_matching(update, context)
        return
    
    question_data = questions[current]
    q_text = question_data["q"]
    
    if question_data["answer"] == "":
        session["current_question"] += 1
        await show_oge_matching_question(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"oge_match_ans_A_{current}"),
         InlineKeyboardButton("B", callback_data=f"oge_match_ans_B_{current}"),
         InlineKeyboardButton("C", callback_data=f"oge_match_ans_C_{current}")],
        [InlineKeyboardButton("D", callback_data=f"oge_match_ans_D_{current}"),
         InlineKeyboardButton("E", callback_data=f"oge_match_ans_E_{current}"),
         InlineKeyboardButton("F", callback_data=f"oge_match_ans_F_{current}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"❓ *Вопрос {current+1} из {len(questions)}*\n\n{q_text}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_oge_matching_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_letter, q_index):
    session = context.user_data.get("oge_matching_session")
    if not session:
        await update.callback_query.answer("❌ Сессия устарела", show_alert=True)
        return
    
    if q_index != session["current_question"]:
        await update.callback_query.answer("⏳ Уже отвечено!", show_alert=True)
        return
    
    question_data = session["questions"][q_index]
    correct_answer = question_data["answer"]
    is_correct = (answer_letter == correct_answer)
    
    if is_correct:
        session["score"] += 1
        await update.callback_query.answer(f"✅ Правильно! {correct_answer}")
    else:
        await update.callback_query.answer(f"❌ Правильно: {correct_answer}", show_alert=True)
    
    session["user_answers"].append({
        "question": question_data["q"],
        "user_answer": answer_letter,
        "correct_answer": correct_answer,
        "is_correct": is_correct
    })
    
    session["current_question"] += 1
    await show_oge_matching_question(update, context)

async def finish_oge_matching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.user_data.get("oge_matching_session")
    if not session:
        return
    
    valid_questions = [q for q in session["questions"] if q["answer"] != ""]
    total_valid = len(valid_questions)
    score = session["score"]
    percent = int(score / total_valid * 100) if total_valid > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально!"
    elif percent >= 75:
        emoji, comment = "🎉", "Отлично!"
    elif percent >= 50:
        emoji, comment = "📚", "Неплохо!"
    else:
        emoji, comment = "💪", "Попробуй ещё!"
    
    details = ""
    for i, ans in enumerate(session["user_answers"]):
        icon = "✅" if ans["is_correct"] else "❌"
        details += f"{i+1}. {ans['question']}\n"
        details += f"   {icon} Ты: {ans['user_answer']} | Правильно: {ans['correct_answer']}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Другой текст", callback_data="oge_matching")],
        [InlineKeyboardButton("🔙 Назад", callback_data="oge_reading")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"{emoji} *Результат!*\n\n"
        f"📊 {score}/{total_valid} ({percent}%)\n\n"
        f"{comment}\n\n"
        f"📋 *Детали:*\n{details}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    del context.user_data["oge_matching_session"]

# ===== ОГЭ: СЛОВООБРАЗОВАНИЕ =====

def load_oge_word_formation():
    try:
        with open("oge_word_formation.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

async def start_oge_word_formation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_oge_word_formation()
    if not data:
        await update.callback_query.answer("❌ Задания пока не загружены", show_alert=True)
        return
    
    tasks = data["tasks"]
    context.user_data["oge_word"] = {
        "tasks": tasks,
        "current": 0,
        "score": 0,
        "total": len(tasks),
        "answers": []
    }
    await show_oge_word_task(update, context)

async def show_oge_word_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.get("oge_word")
    if not data:
        return
    
    idx = data["current"]
    if idx >= data["total"]:
        await finish_oge_word_formation(update, context)
        return
    
    task = data["tasks"][idx]
    
    keyboard = [
        [InlineKeyboardButton("📝 Существительное (noun)", callback_data=f"oge_word_pos_noun_{idx}")],
        [InlineKeyboardButton("📝 Глагол (verb)", callback_data=f"oge_word_pos_verb_{idx}")],
        [InlineKeyboardButton("📝 Прилагательное (adjective)", callback_data=f"oge_word_pos_adjective_{idx}")],
        [InlineKeyboardButton("📝 Наречие (adverb)", callback_data=f"oge_word_pos_adverb_{idx}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"📝 *Словообразование*\n\n"
        f"Задание {idx+1}/{data['total']}:\n\n"
        f"{task['sentence']}\n\n"
        f"⬇️ *Сначала выбери часть речи:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_oge_word_pos(update: Update, context: ContextTypes.DEFAULT_TYPE, pos, idx):
    data = context.user_data.get("oge_word")
    if not data:
        return
    
    if idx != data["current"]:
        await update.callback_query.answer("⏳ Это задание уже выполнено!", show_alert=True)
        return
    
    task = data["tasks"][idx]
    is_correct = (pos == task["part_of_speech"])
    
    data["answers"].append({
        "sentence": task["sentence"],
        "selected_pos": pos,
        "correct_pos": task["part_of_speech"],
        "is_correct_pos": is_correct,
        "correct_answer": task["correct_answer"]
    })
    
    if is_correct:
        data["score"] += 1
        await update.callback_query.answer(f"✅ Часть речи верная! Теперь напиши слово.")
    else:
        await update.callback_query.answer(f"❌ Неправильно! Правильно: {task['part_of_speech']}", show_alert=True)
    
    context.user_data["awaiting_oge_word"] = True
    await update.callback_query.edit_message_text(
        f"📝 *Введи слово*\n\n"
        f"Задание {idx+1}/{data['total']}:\n\n"
        f"{task['sentence']}\n\n"
        f"✏️ *Напиши правильную форму слова в чат:*"
    )

async def handle_oge_word_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = update.message.text.strip().lower()
    data = context.user_data.get("oge_word")
    if not data:
        return
    
    idx = data["current"]
    task = data["tasks"][idx]
    is_correct = (word == task["correct_answer"].lower())
    
    data["answers"][-1]["user_word"] = word
    data["answers"][-1]["is_correct_word"] = is_correct
    
    if is_correct:
        data["score"] += 1
        await update.message.reply_text(f"✅ Правильно! '{task['correct_answer']}' — верно!")
    else:
        await update.message.reply_text(f"❌ Неправильно. Правильный ответ: {task['correct_answer']}")
    
    data["current"] += 1
    context.user_data["awaiting_oge_word"] = False
    
    if data["current"] >= data["total"]:
        await finish_oge_word_formation_from_message(update, context)
    else:
        await show_oge_word_task_from_message(update, context)

async def show_oge_word_task_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.get("oge_word")
    if not data:
        return
    
    idx = data["current"]
    if idx >= data["total"]:
        await finish_oge_word_formation_from_message(update, context)
        return
    
    task = data["tasks"][idx]
    
    keyboard = [
        [InlineKeyboardButton("📝 Существительное (noun)", callback_data=f"oge_word_pos_noun_{idx}")],
        [InlineKeyboardButton("📝 Глагол (verb)", callback_data=f"oge_word_pos_verb_{idx}")],
        [InlineKeyboardButton("📝 Прилагательное (adjective)", callback_data=f"oge_word_pos_adjective_{idx}")],
        [InlineKeyboardButton("📝 Наречие (adverb)", callback_data=f"oge_word_pos_adverb_{idx}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📝 *Словообразование*\n\n"
        f"Задание {idx+1}/{data['total']}:\n\n"
        f"{task['sentence']}\n\n"
        f"⬇️ *Выбери часть речи:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def finish_oge_word_formation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await finish_oge_word_formation_internal(update, context)

async def finish_oge_word_formation_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await finish_oge_word_formation_internal(update, context)

async def finish_oge_word_formation_internal(update, context):
    data = context.user_data.get("oge_word")
    if not data:
        return
    
    score = data["score"]
    total = data["total"]
    percent = int(score / total * 100) if total > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально! Ты мастер словообразования!"
    elif percent >= 75:
        emoji, comment = "🎉", "Отличный результат!"
    elif percent >= 50:
        emoji, comment = "📚", "Неплохо! Но стоит повторить."
    else:
        emoji, comment = "💪", "Нужно больше практики!"
    
    details = ""
    for i, ans in enumerate(data["answers"]):
        pos_icon = "✅" if ans["is_correct_pos"] else "❌"
        word_icon = "✅" if ans.get("is_correct_word", False) else "❌"
        details += f"{i+1}. {ans['sentence']}\n"
        details += f"   Часть речи: {pos_icon} {ans['selected_pos']} (правильно: {ans['correct_pos']})\n"
        details += f"   Слово: {word_icon} {ans.get('user_word', '—')} (правильно: {ans['correct_answer']})\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="oge_word_formation")],
        [InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(
            f"{emoji} *Результат!*\n\n"
            f"📊 {score}/{total} ({percent}%)\n\n{comment}\n\n📋 *Детали:*\n{details}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"{emoji} *Результат!*\n\n"
            f"📊 {score}/{total} ({percent}%)\n\n{comment}\n\n📋 *Детали:*\n{details}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    del context.user_data["oge_word"]
    context.user_data["awaiting_oge_word"] = False

# ===== ДИАГНОСТИКА =====

def load_diagnostic():
    try:
        with open("diagnostic.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

async def start_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diagnostic_data = load_diagnostic()
    if not diagnostic_data:
        await update.callback_query.answer("❌ Тест пока не доступен", show_alert=True)
        return
    
    questions = diagnostic_data["questions"]
    context.user_data["diagnostic"] = {
        "questions": questions,
        "current": 0,
        "score": 0,
        "answers": []
    }
    await show_diagnostic_question(update, context)

async def show_diagnostic_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diag = context.user_data.get("diagnostic")
    if not diag:
        return
    
    q_num = diag["current"]
    if q_num >= len(diag["questions"]):
        await finish_diagnostic(update, context)
        return
    
    question = diag["questions"][q_num]
    options = question["options"]
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{chr(97+i)}) {opt}", callback_data=f"diag_ans_{i}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"🎯 *Тест на твой уровень*\n\nВопрос {q_num + 1}/{len(diag['questions'])}:\n\n*{question['q']}*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_diagnostic_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_idx):
    diag = context.user_data.get("diagnostic")
    if not diag:
        return
    
    question = diag["questions"][diag["current"]]
    correct = question["answer"]
    is_correct = (answer_idx == correct)
    
    if is_correct:
        diag["score"] += 1
    
    diag["answers"].append({
        "question": question["q"],
        "correct": is_correct,
        "level": question["level"]
    })
    
    diag["current"] += 1
    
    if diag["current"] >= len(diag["questions"]):
        await finish_diagnostic(update, context)
    else:
        await show_diagnostic_question(update, context)

async def finish_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diag = context.user_data.get("diagnostic")
    if not diag:
        return
    
    score = diag["score"]
    total = len(diag["questions"])
    
    level_counts = {"A1": 0, "A2": 0, "B1": 0, "B2": 0}
    for ans in diag["answers"]:
        if ans["correct"]:
            level_counts[ans["level"]] += 1
    
    diagnostic_data = load_diagnostic()
    levels = diagnostic_data["levels"]
    
    main_level = "A1"
    if score >= 25:
        main_level = "B2"
    elif score >= 19:
        main_level = "B1"
    elif score >= 11:
        main_level = "A2"
    
    level_info = levels[main_level]
    
    result_text = (
        f"📊 *Результат теста*\n\n"
        f"✅ Правильных ответов: {score}/{total}\n"
        f"🎯 *Твой уровень: {level_info['label']}*\n\n"
        f"📌 *Рекомендация:*\n{level_info['recommend']}\n\n"
        f"📈 *Детали:*\n"
        f"  A1: {level_counts['A1']} правильных\n"
        f"  A2: {level_counts['A2']} правильных\n"
        f"  B1: {level_counts['B1']} правильных\n"
        f"  B2: {level_counts['B2']} правильных"
    )
    
    keyboard = [
        [InlineKeyboardButton("📚 Перейти к обучению", callback_data="back_to_levels")],
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="diag_restart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    del context.user_data["diagnostic"]

# ===== ОБЩИЙ ПРОГРЕСС =====

async def show_total_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if not user_id:
        await start(update, context)
        return
    
    text = "📊 *Общий прогресс*\n\n"
    total_all = done_all = 0
    for level in TOPICS:
        level_total = sum(len(topics) for topics in TOPICS[level].values())
        progress = get_progress(user_id, level)
        level_done = 0
        for cat in TOPICS[level]:
            for topic in TOPICS[level][cat]:
                if progress.get(topic, 0):
                    level_done += 1
        total_all += level_total
        done_all += level_done
        percent = int(level_done / level_total * 100) if level_total > 0 else 0
        bar = "🟩" * (percent // 10) + "⬜" * (10 - percent // 10)
        text += f"{bar} {level}: {level_done}/{level_total} ({percent}%)\n"
    total_percent = int(done_all / total_all * 100) if total_all > 0 else 0
    text += f"\n🎯 *Всего: {done_all}/{total_all} ({total_percent}%)*"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_levels")]]
    if context.user_data.get("is_admin"):
        keyboard.append([InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ===== АДМИН =====

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("is_admin"):
        await update.callback_query.answer("❌ Нет доступа", show_alert=True)
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, is_admin FROM users ORDER BY id")
    users = c.fetchall()
    conn.close()
    
    text = "👥 *Список пользователей*\n\n"
    for user in users:
        role = "👑 Админ" if user[2] else "👤 Пользователь"
        text += f"ID: {user[0]} | {user[1]} — {role}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_levels")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ===== ОГЭ: TRUE / FALSE / NOT STATED =====

def load_oge_tfns():
    """Загружает задания для раздела True/False/Not Stated"""
    try:
        with open("oge_tfns.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

async def start_oge_tfns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список текстов для T/F/NS"""
    data = load_oge_tfns()
    if not data:
        await update.callback_query.answer("❌ Файл с заданиями не найден!", show_alert=True)
        return
    
    texts = data["texts"]
    keyboard = []
    for text in texts:
        display_name = f"{text['id'].replace('tfns_', '')}. {text['title']}"
        keyboard.append([InlineKeyboardButton(f"📄 {display_name}", callback_data=f"oge_tfns_show_{text['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="oge_reading")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "✅ *True / False / Not Stated*\n\n"
        "Выбери текст для выполнения заданий.\n"
        "Тебе нужно будет определить, верны ли утверждения (True/False) "
        "или информация не упоминается в тексте (Not Stated).",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_oge_tfns_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text_id):
    """Показывает текст и запускает опрос"""
    data = load_oge_tfns()
    if not data:
        await update.callback_query.answer("❌ Ошибка загрузки", show_alert=True)
        return
    
    selected_text = None
    for text in data["texts"]:
        if text["id"] == text_id:
            selected_text = text
            break
    
    if not selected_text:
        await update.callback_query.answer("❌ Текст не найден", show_alert=True)
        return
    
    context.user_data["oge_tfns_session"] = {
        "text_data": selected_text,
        "current_question": 0,
        "score": 0,
        "user_answers": [],
        "statements": selected_text["statements"]
    }
    
    text_message = f"📖 *{selected_text['title']}*\n\n{selected_text['text']}"
    await update.callback_query.edit_message_text(
        text_message,
        parse_mode="Markdown"
    )
    
    keyboard = [[InlineKeyboardButton("▶️ Начать отвечать", callback_data=f"oge_tfns_start_{text_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_chat.send_message(
        "Готов(а)? Нажимай! 🚀",
        reply_markup=reply_markup
    )

async def start_oge_tfns_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает процесс ответа на вопросы"""
    await show_oge_tfns_question(update, context)

async def show_oge_tfns_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущее утверждение"""
    session = context.user_data.get("oge_tfns_session")
    if not session:
        await update.callback_query.answer("❌ Сессия не найдена", show_alert=True)
        return
    
    current = session["current_question"]
    statements = session["statements"]
    
    if current >= len(statements):
        await finish_oge_tfns(update, context)
        return
    
    statement_data = statements[current]
    statement_text = statement_data["statement"]
    
    keyboard = [
        [InlineKeyboardButton("✅ True", callback_data=f"oge_tfns_ans_True_{current}")],
        [InlineKeyboardButton("❌ False", callback_data=f"oge_tfns_ans_False_{current}")],
        [InlineKeyboardButton("❓ Not Stated", callback_data=f"oge_tfns_ans_Not Stated_{current}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"❓ *Утверждение {current+1} из {len(statements)}*\n\n{statement_text}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_oge_tfns_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer, q_index):
    """Обрабатывает ответ на утверждение"""
    session = context.user_data.get("oge_tfns_session")
    if not session:
        await update.callback_query.answer("❌ Сессия устарела", show_alert=True)
        return
    
    if q_index != session["current_question"]:
        await update.callback_query.answer("⏳ Уже отвечено!", show_alert=True)
        return
    
    statement_data = session["statements"][q_index]
    correct_answer = statement_data["answer"]
    is_correct = (answer == correct_answer)
    
    if is_correct:
        session["score"] += 1
        await update.callback_query.answer(f"✅ Правильно! {correct_answer}")
    else:
        await update.callback_query.answer(f"❌ Правильно: {correct_answer}", show_alert=True)
    
    session["user_answers"].append({
        "statement": statement_data["statement"],
        "user_answer": answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct
    })
    
    session["current_question"] += 1
    await show_oge_tfns_question(update, context)

async def finish_oge_tfns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает раздел True/False/Not Stated"""
    session = context.user_data.get("oge_tfns_session")
    if not session:
        return
    
    total = len(session["statements"])
    score = session["score"]
    percent = int(score / total * 100) if total > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально! Ты отлично понял(а) текст!"
    elif percent >= 75:
        emoji, comment = "🎉", "Хороший результат! Так держать!"
    elif percent >= 50:
        emoji, comment = "📚", "Неплохо! Но стоит перечитать текст внимательнее."
    else:
        emoji, comment = "💪", "Нужно больше практики! Попробуй ещё раз."
    
    details = ""
    for i, ans in enumerate(session["user_answers"]):
        icon = "✅" if ans["is_correct"] else "❌"
        details += f"{i+1}. {ans['statement']}\n"
        details += f"   {icon} Ты: {ans['user_answer']} | Правильно: {ans['correct_answer']}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Другой текст", callback_data="oge_tfns")],
        [InlineKeyboardButton("🔙 Назад", callback_data="oge_reading")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"{emoji} *Результат!*\n\n"
        f"📊 {score}/{total} ({percent}%)\n\n"
        f"{comment}\n\n"
        f"📋 *Детали:*\n{details}",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    del context.user_data["oge_tfns_session"]


# ===== ОГЭ: АУДИРОВАНИЕ (ЗАДАНИЕ 1 — ВЫБОР ОТВЕТА) =====

def find_audio_file(filename):
    """Ищет аудиофайл в разных возможных местах"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(base_dir, "audio", "choice", filename),
        os.path.join(base_dir, "choice", filename),
        os.path.join(base_dir, filename),
        os.path.join("/app", "audio", "choice", filename),
        os.path.join("/app", "choice", filename),
        os.path.join("/data", "audio", "choice", filename),
        os.path.join(os.getcwd(), "audio", "choice", filename),
        os.path.join(os.getcwd(), "choice", filename),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Найден аудиофайл: {path}")
            return path
    
    print(f"❌ Аудиофайл {filename} не найден. Проверены пути:")
    for path in possible_paths:
        print(f"  - {path} (exists: {os.path.exists(path)})")
    
    return None

def load_audio_choice():
    """Загружает задания для аудирования"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_paths = [
            os.path.join(base_dir, "oge_audio_choice.json"),
            os.path.join("/app", "oge_audio_choice.json"),
            os.path.join(os.getcwd(), "oge_audio_choice.json")
        ]
        
        for path in json_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        print(f"❌ oge_audio_choice.json не найден. Проверены пути: {json_paths}")
        return None
    except Exception as e:
        print(f"❌ Ошибка загрузки oge_audio_choice.json: {e}")
        return None

async def start_audio_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает задание 1 по аудированию (выбор ответа)"""
    data = load_audio_choice()
    if not data:
        await update.callback_query.answer("❌ Задания не загружены", show_alert=True)
        return
    
    audio_path = find_audio_file(data["audio_file"])
    
    if audio_path:
        try:
            with open(audio_path, "rb") as f:
                await update.effective_chat.send_voice(
                    voice=f,
                    caption="🎧 *Задание 1. Выбор ответа*\n\n"
                           "Прослушайте аудио (4 коротких текста A, B, C, D) и ответьте на 4 вопроса.\n"
                           "Вы услышите запись дважды.",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при отправке аудио: {str(e)}\n\n"
                f"Путь: `{audio_path}`",
                parse_mode="Markdown"
            )
            return
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        await update.callback_query.edit_message_text(
            f"❌ Аудиофайл `{data['audio_file']}` не найден!\n\n"
            f"Проверь, что файл находится в одной из папок:\n"
            f"• `{base_dir}/audio/choice/`\n"
            f"• `/app/audio/choice/`\n"
            f"• `/app/`\n"
            f"• `{os.getcwd()}/audio/choice/`\n\n"
            f"Текущая директория: `{base_dir}`",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем все вопросы в сессию
    context.user_data["audio_choice"] = {
        "tasks": data["tasks"],
        "current": 0,
        "score": 0,
        "user_answers": [],
        "total": len(data["tasks"])
    }
    
    # Показываем все вопросы сразу
    await show_all_audio_questions(update, context)

async def show_all_audio_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает все 4 вопроса сразу с кнопками для ответа"""
    session = context.user_data.get("audio_choice")
    if not session:
        return
    
    tasks = session["tasks"]
    current = session["current"]
    
    # Формируем текст со всеми вопросами
    text = "🎧 *Задание 1. Выбор ответа*\n\n"
    text += "Ответь на все 4 вопроса. На каждый вопрос выбери один вариант:\n\n"
    
    for i, task in enumerate(tasks):
        status = "✅" if i < current else "⬜"
        text += f"{status} *Вопрос {i+1}:* {task['question']}\n"
        for j, opt in enumerate(task["options"]):
            text += f"   {chr(97+j)}) {opt}\n"
        text += "\n"
    
    # Создаём кнопки для каждого вопроса
    keyboard = []
    for i in range(len(tasks)):
        if i < current:
            # Вопрос уже отвечен - показываем зелёную галочку
            keyboard.append([InlineKeyboardButton(f"✅ Вопрос {i+1} (отвечен)", callback_data=f"audio_choice_noop")])
        else:
            # Вопрос ещё не отвечен - показываем кнопку с вариантами
            row = []
            for j in range(3):
                row.append(InlineKeyboardButton(
                    f"{chr(97+j)}", 
                    callback_data=f"audio_choice_ans_{j}_{i}"
                ))
            keyboard.append([InlineKeyboardButton(f"❓ Вопрос {i+1}:", callback_data=f"audio_choice_noop")] + row)
    
    # Кнопка для перезапуска
    keyboard.append([InlineKeyboardButton("🔄 Пройти заново", callback_data="audio_choice_restart")])
    keyboard.append([InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_audio_choice_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, answer_idx, q_index):
    """Обрабатывает ответ на вопрос и показывает обновлённый список"""
    session = context.user_data.get("audio_choice")
    if not session:
        await update.callback_query.answer("❌ Сессия устарела", show_alert=True)
        return
    
    # Проверяем, что вопрос ещё не отвечен
    if q_index < session["current"]:
        await update.callback_query.answer("⏳ Этот вопрос уже отвечен!", show_alert=True)
        return
    
    # Проверяем, что это правильный вопрос по порядку
    if q_index != session["current"]:
        await update.callback_query.answer(f"❌ Отвечай на вопросы по порядку! Сейчас вопрос {session['current'] + 1}", show_alert=True)
        return
    
    task = session["tasks"][q_index]
    is_correct = (answer_idx == task["answer"])
    
    if is_correct:
        session["score"] += 1
        await update.callback_query.answer("✅ Правильно!")
    else:
        correct_text = task["options"][task["answer"]]
        await update.callback_query.answer(f"❌ Правильно: {correct_text}", show_alert=True)
    
    session["user_answers"].append({
        "question": task["question"],
        "user_answer": task["options"][answer_idx],
        "correct_answer": task["options"][task["answer"]],
        "is_correct": is_correct
    })
    
    session["current"] += 1
    
    # Проверяем, все ли вопросы отвечены
    if session["current"] >= session["total"]:
        await finish_audio_choice(update, context)
    else:
        # Обновляем список вопросов
        await show_all_audio_questions(update, context)

async def finish_audio_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает задание 1 по аудированию"""
    session = context.user_data.get("audio_choice")
    if not session:
        return
    
    total = session["total"]
    score = session["score"]
    percent = int(score / total * 100) if total > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально! Ты отлично справился(ась)!"
    elif percent >= 75:
        emoji, comment = "🎉", "Хороший результат!"
    elif percent >= 50:
        emoji, comment = "📚", "Неплохо, но стоит переслушать аудио."
    else:
        emoji, comment = "💪", "Нужно больше практики!"
    
    details = ""
    for i, ans in enumerate(session["user_answers"]):
        icon = "✅" if ans["is_correct"] else "❌"
        details += f"{i+1}. {ans['question']}\n"
        details += f"   {icon} Ты: {ans['user_answer']} | Правильно: {ans['correct_answer']}\n"
    
    # Создаём красивую таблицу результатов
    result_text = f"{emoji} *Результат!*\n\n"
    result_text += f"📊 {score}/{total} ({percent}%)\n\n"
    result_text += f"{comment}\n\n"
    
    # Добавляем прогресс-бар
    bar_length = 10
    filled = int(percent / 100 * bar_length)
    bar = "🟩" * filled + "⬜" * (bar_length - filled)
    result_text += f"{bar} {percent}%\n\n"
    
    result_text += f"📋 *Детали:*\n{details}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="audio_choice_restart")],
        [InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    del context.user_data["audio_choice"]

async def debug_paths(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отладочная функция для проверки путей"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    
    paths = [
        ("__file__", base_dir),
        ("os.getcwd()", cwd),
        ("audio/choice/8171.mp3", os.path.join(base_dir, "audio", "choice", "8171.mp3")),
        ("/app/audio/choice/8171.mp3", "/app/audio/choice/8171.mp3"),
    ]
    
    message = "📁 *Отладка путей:*\n\n"
    for name, path in paths:
        exists = "✅" if os.path.exists(path) else "❌"
        message += f"{exists} {name}: `{path}`\n"
    
    try:
        files = os.listdir(base_dir)
        message += f"\n📂 Файлы в `{base_dir}`:\n"
        for f in files:
            message += f"• {f}\n"
    except:
        message += "\n❌ Не удалось прочитать директорию"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# ===== ОГЭ: АУДИРОВАНИЕ (ЗАДАНИЕ 2 — СОПОСТАВЛЕНИЕ) =====

def load_audio_matching():
    """Загружает задания для сопоставления"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_paths = [
            os.path.join(base_dir, "oge_audio_matching.json"),
            os.path.join("/app", "oge_audio_matching.json"),
            os.path.join(os.getcwd(), "oge_audio_matching.json")
        ]
        
        for path in json_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        print(f"❌ oge_audio_matching.json не найден. Проверены пути: {json_paths}")
        return None
    except Exception as e:
        print(f"❌ Ошибка загрузки oge_audio_matching.json: {e}")
        return None

def find_audio_file_matching(filename):
    """Ищет аудиофайл для задания 2"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(base_dir, "audio", "matching", filename),
        os.path.join(base_dir, "matching", filename),
        os.path.join(base_dir, filename),
        os.path.join("/app", "audio", "matching", filename),
        os.path.join("/app", "matching", filename),
        os.path.join("/data", "audio", "matching", filename),
        os.path.join(os.getcwd(), "audio", "matching", filename),
        os.path.join(os.getcwd(), "matching", filename),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Найден аудиофайл: {path}")
            return path
    
    print(f"❌ Аудиофайл {filename} не найден. Проверены пути:")
    for path in possible_paths:
        print(f"  - {path} (exists: {os.path.exists(path)})")
    
    return None

async def start_audio_matching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает задание 2 — сопоставление"""
    data = load_audio_matching()
    if not data:
        await update.callback_query.answer("❌ Задания не загружены", show_alert=True)
        return
    
    # Отправляем аудио
    audio_path = find_audio_file_matching(data["audio_file"])
    
    if audio_path:
        try:
            with open(audio_path, "rb") as f:
                await update.effective_chat.send_voice(
                    voice=f,
                    caption="🎧 *Задание 2. Сопоставление*\n\n"
                           "Прослушайте высказывания пяти людей (A, B, C, D, E) и подберите к каждому "
                           "соответствующую рубрику из списка 1–6. Одна рубрика лишняя.\n"
                           "Вы услышите запись дважды.",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при отправке аудио: {str(e)}\n\n"
                f"Путь: `{audio_path}`",
                parse_mode="Markdown"
            )
            return
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        await update.callback_query.edit_message_text(
            f"❌ Аудиофайл `{data['audio_file']}` не найден!\n\n"
            f"Проверь, что файл находится в папке `audio/matching/`\n\n"
            f"Текущая директория: `{base_dir}`",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем данные в сессию
    context.user_data["audio_matching"] = {
        "speakers": data["speakers"],
        "rubrics": data["rubrics"],
        "current": 0,
        "score": 0,
        "user_answers": [],
        "total": len(data["speakers"])
    }
    
    # Показываем рубрики и начинаем опрос
    await show_matching_question(update, context)

async def show_matching_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущего говорящего для сопоставления"""
    session = context.user_data.get("audio_matching")
    if not session:
        return
    
    current = session["current"]
    speakers = session["speakers"]
    rubrics = session["rubrics"]
    
    if current >= session["total"]:
        await finish_matching(update, context)
        return
    
    speaker = speakers[current]
    
    # Формируем текст с рубриками
    text = f"🎯 *Сопоставление*\n\n"
    text += f"Говорящий *{speaker['id']}*\n\n"
    text += "📋 *Рубрики:*\n"
    for i, rubric in enumerate(rubrics):
        text += f"{i+1}. {rubric}\n"
    text += f"\n⬇️ *Выбери номер рубрики для говорящего {speaker['id']}:*"
    
    # Создаём кнопки с номерами рубрик
    keyboard = []
    row = []
    for i in range(len(rubrics)):
        row.append(InlineKeyboardButton(str(i+1), callback_data=f"matching_ans_{i}_{current}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_matching_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, rubric_idx, speaker_idx):
    """Обрабатывает ответ на сопоставление"""
    session = context.user_data.get("audio_matching")
    if not session:
        await update.callback_query.answer("❌ Сессия устарела", show_alert=True)
        return
    
    if speaker_idx != session["current"]:
        await update.callback_query.answer("⏳ Это задание уже выполнено!", show_alert=True)
        return
    
    speaker = session["speakers"][speaker_idx]
    is_correct = (rubric_idx == speaker["correct_rubric"])
    
    if is_correct:
        session["score"] += 1
        await update.callback_query.answer(f"✅ Правильно! Рубрика {rubric_idx + 1}")
    else:
        correct_rubric_text = session["rubrics"][speaker["correct_rubric"]]
        await update.callback_query.answer(f"❌ Правильно: {speaker['correct_rubric'] + 1} — {correct_rubric_text}", show_alert=True)
    
    session["user_answers"].append({
        "speaker": speaker["id"],
        "user_answer": rubric_idx + 1,
        "correct_answer": speaker["correct_rubric"] + 1,
        "is_correct": is_correct
    })
    
    session["current"] += 1
    
    if session["current"] >= session["total"]:
        await finish_matching(update, context)
    else:
        await show_matching_question(update, context)

async def finish_matching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает задание 2 — сопоставление"""
    session = context.user_data.get("audio_matching")
    if not session:
        return
    
    total = session["total"]
    score = session["score"]
    percent = int(score / total * 100) if total > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально! Ты отлично справился(ась)!"
    elif percent >= 80:
        emoji, comment = "🎉", "Отличный результат!"
    elif percent >= 60:
        emoji, comment = "📚", "Неплохо! Но стоит переслушать аудио."
    else:
        emoji, comment = "💪", "Нужно больше практики!"
    
    details = ""
    for i, ans in enumerate(session["user_answers"]):
        icon = "✅" if ans["is_correct"] else "❌"
        details += f"{i+1}. Говорящий {ans['speaker']} → "
        details += f"{icon} Ты выбрал: {ans['user_answer']} | "
        details += f"Правильно: {ans['correct_answer']}\n"
    
    # Результат с прогресс-баром
    result_text = f"{emoji} *Результат!*\n\n"
    result_text += f"📊 {score}/{total} ({percent}%)\n\n"
    result_text += f"{comment}\n\n"
    
    bar_length = 10
    filled = int(percent / 100 * bar_length)
    bar = "🟩" * filled + "⬜" * (bar_length - filled)
    result_text += f"{bar} {percent}%\n\n"
    
    result_text += f"📋 *Детали:*\n{details}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_audio_matching")],
        [InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    del context.user_data["audio_matching"]

# ===== ОГЭ: АУДИРОВАНИЕ (ЗАДАНИЕ 3 — ЗАПОЛНЕНИЕ ПРОПУСКОВ) =====

def load_audio_fill():
    """Загружает задания для заполнения пропусков"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_paths = [
            os.path.join(base_dir, "oge_audio_fill.json"),
            os.path.join("/app", "oge_audio_fill.json"),
            os.path.join(os.getcwd(), "oge_audio_fill.json")
        ]
        
        for path in json_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        print(f"❌ oge_audio_fill.json не найден. Проверены пути: {json_paths}")
        return None
    except Exception as e:
        print(f"❌ Ошибка загрузки oge_audio_fill.json: {e}")
        return None

def find_audio_file_fill(filename):
    """Ищет аудиофайл для задания 3"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(base_dir, "audio", "fill", filename),
        os.path.join(base_dir, "fill", filename),
        os.path.join(base_dir, filename),
        os.path.join("/app", "audio", "fill", filename),
        os.path.join("/app", "fill", filename),
        os.path.join("/data", "audio", "fill", filename),
        os.path.join(os.getcwd(), "audio", "fill", filename),
        os.path.join(os.getcwd(), "fill", filename),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Найден аудиофайл: {path}")
            return path
    
    print(f"❌ Аудиофайл {filename} не найден. Проверены пути:")
    for path in possible_paths:
        print(f"  - {path} (exists: {os.path.exists(path)})")
    
    return None

async def start_audio_fill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает задание 3 — заполнение пропусков"""
    data = load_audio_fill()
    if not data:
        await update.callback_query.answer("❌ Задания не загружены", show_alert=True)
        return
    
    # Отправляем аудио
    audio_path = find_audio_file_fill(data["audio_file"])
    
    if audio_path:
        try:
            with open(audio_path, "rb") as f:
                await update.effective_chat.send_voice(
                    voice=f,
                    caption="🎧 *Задание 3. Заполнение пропусков*\n\n"
                           "Прослушайте интервью и заполните пропуски в предложениях.\n"
                           "Впишите не более одного слова (без артиклей).\n"
                           "Числа записывайте буквами.\n"
                           "Вы услышите запись дважды.",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await update.callback_query.edit_message_text(
                f"❌ Ошибка при отправке аудио: {str(e)}\n\n"
                f"Путь: `{audio_path}`",
                parse_mode="Markdown"
            )
            return
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        await update.callback_query.edit_message_text(
            f"❌ Аудиофайл `{data['audio_file']}` не найден!\n\n"
            f"Проверь, что файл находится в папке `audio/fill/`\n\n"
            f"Текущая директория: `{base_dir}`",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем данные в сессию
    context.user_data["audio_fill"] = {
        "tasks": data["tasks"],
        "current": 0,
        "score": 0,
        "user_answers": [],
        "total": len(data["tasks"])
    }
    
    # Показываем первый вопрос
    await show_fill_question(update, context)

async def show_fill_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущий вопрос для заполнения"""
    session = context.user_data.get("audio_fill")
    if not session:
        return
    
    current = session["current"]
    tasks = session["tasks"]
    
    if current >= session["total"]:
        await finish_fill(update, context)
        return
    
    task = tasks[current]
    
    # Показываем вопрос с пропуском
    text = f"📝 *Заполнение пропусков*\n\n"
    text += f"Вопрос {current + 1} из {session['total']}:\n\n"
    text += f"*{task['question']}*\n\n"
    text += "✏️ *Напиши слово в чат:*"
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode="Markdown"
    )
    
    # Устанавливаем флаг ожидания ответа
    context.user_data["awaiting_fill_answer"] = True

async def handle_fill_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на заполнение пропуска"""
    session = context.user_data.get("audio_fill")
    if not session:
        await update.message.reply_text("❌ Сессия устарела. Начни заново.")
        return
    
    current = session["current"]
    if current >= session["total"]:
        return
    
    user_word = update.message.text.strip()
    task = session["tasks"][current]
    
    # Сравниваем ответ (регистронезависимо)
    is_correct = user_word.lower() == task["answer"].lower()
    
    if is_correct:
        session["score"] += 1
        await update.message.reply_text(f"✅ Правильно! Ответ: {task['answer']}")
    else:
        await update.message.reply_text(f"❌ Неправильно. Правильный ответ: {task['answer']}")
    
    session["user_answers"].append({
        "question": task["question"],
        "user_answer": user_word,
        "correct_answer": task["answer"],
        "is_correct": is_correct
    })
    
    session["current"] += 1
    context.user_data["awaiting_fill_answer"] = False
    
    if session["current"] >= session["total"]:
        await finish_fill_from_message(update, context)
    else:
        await show_fill_question_from_message(update, context)

async def show_fill_question_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает следующий вопрос после ответа"""
    session = context.user_data.get("audio_fill")
    if not session:
        return
    
    current = session["current"]
    tasks = session["tasks"]
    
    if current >= session["total"]:
        await finish_fill_from_message(update, context)
        return
    
    task = tasks[current]
    
    text = f"📝 *Заполнение пропусков*\n\n"
    text += f"Вопрос {current + 1} из {session['total']}:\n\n"
    text += f"*{task['question']}*\n\n"
    text += "✏️ *Напиши слово в чат:*"
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )
    
    context.user_data["awaiting_fill_answer"] = True

async def finish_fill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает задание 3 (из callback)"""
    await finish_fill_internal(update, context)

async def finish_fill_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает задание 3 (из сообщения)"""
    await finish_fill_internal(update, context)

async def finish_fill_internal(update, context):
    """Внутренняя функция завершения задания 3"""
    session = context.user_data.get("audio_fill")
    if not session:
        return
    
    total = session["total"]
    score = session["score"]
    percent = int(score / total * 100) if total > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально! Ты отлично справился(ась)!"
    elif percent >= 75:
        emoji, comment = "🎉", "Хороший результат!"
    elif percent >= 50:
        emoji, comment = "📚", "Неплохо! Но стоит переслушать аудио."
    else:
        emoji, comment = "💪", "Нужно больше практики!"
    
    details = ""
    for i, ans in enumerate(session["user_answers"]):
        icon = "✅" if ans["is_correct"] else "❌"
        details += f"{i+1}. {ans['question']}\n"
        details += f"   {icon} Ты: {ans['user_answer']} | Правильно: {ans['correct_answer']}\n"
    
    result_text = f"{emoji} *Результат!*\n\n"
    result_text += f"📊 {score}/{total} ({percent}%)\n\n"
    result_text += f"{comment}\n\n"
    
    bar_length = 10
    filled = int(percent / 100 * bar_length)
    bar = "🟩" * filled + "⬜" * (bar_length - filled)
    result_text += f"{bar} {percent}%\n\n"
    
    result_text += f"📋 *Детали:*\n{details}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_audio_fill")],
        [InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Определяем, откуда пришёл вызов
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    del context.user_data["audio_fill"]
    context.user_data["awaiting_fill_answer"] = False

# ===== ОГЭ: СЛОВООБРАЗОВАНИЕ (ЛЕКСИКО-ГРАММАТИЧЕСКИЕ ТРАНСФОРМАЦИИ) =====

def load_oge_word_formation_new():
    """Загружает задания по словообразованию"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_paths = [
            os.path.join(base_dir, "oge_word_formation.json"),
            os.path.join("/app", "oge_word_formation.json"),
            os.path.join(os.getcwd(), "oge_word_formation.json")
        ]
        
        for path in json_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        print(f"❌ oge_word_formation.json не найден. Проверены пути: {json_paths}")
        return None
    except Exception as e:
        print(f"❌ Ошибка загрузки oge_word_formation.json: {e}")
        return None

async def start_word_formation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает задание 4 — словообразование"""
    data = load_oge_word_formation_new()
    if not data:
        await update.callback_query.answer("❌ Задания не загружены", show_alert=True)
        return
    
    # Отправляем текст с легендой
    if "text" in data:
        await update.callback_query.edit_message_text(
            f"📖 *Прочитайте текст и преобразуйте слова в скобках:*\n\n{data['text']}",
            parse_mode="Markdown"
        )
        # Отправляем отдельное сообщение с инструкцией
        await update.effective_chat.send_message(
            "✏️ *Сейчас будут показаны задания по одному.*\n"
            "Вам нужно преобразовать слово в скобках так, чтобы оно грамматически соответствовало тексту.\n\n"
            "Напишите ответ в чат.",
            parse_mode="Markdown"
        )
    
    # Сохраняем данные в сессию
    context.user_data["word_formation"] = {
        "tasks": data["tasks"],
        "current": 0,
        "score": 0,
        "user_answers": [],
        "total": len(data["tasks"])
    }
    
    # Показываем первый вопрос
    await show_word_formation_question(update, context)
    
    # Сохраняем данные в сессию
    context.user_data["word_formation"] = {
        "tasks": data["tasks"],
        "current": 0,
        "score": 0,
        "user_answers": [],
        "total": len(data["tasks"])
    }
    
    # Показываем первый вопрос
    await show_word_formation_question(update, context)

async def show_word_formation_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущее задание по словообразованию"""
    session = context.user_data.get("word_formation")
    if not session:
        return
    
    current = session["current"]
    tasks = session["tasks"]
    
    if current >= session["total"]:
        await finish_word_formation(update, context)
        return
    
    task = tasks[current]
    
    text = f"📝 *Словообразование*\n\n"
    text += f"Задание {current + 1} из {session['total']}:\n\n"
    text += f"{task['question']}\n\n"
    text += "✏️ *Напиши преобразованное слово в чат:*"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)
    
    context.user_data["awaiting_word_formation"] = True

async def handle_word_formation_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на словообразование"""
    session = context.user_data.get("word_formation")
    if not session:
        await update.message.reply_text("❌ Сессия устарела. Начни заново.")
        return
    
    current = session["current"]
    if current >= session["total"]:
        return
    
    user_answer = update.message.text.strip()
    task = session["tasks"][current]
    
    # Сравниваем ответ (регистронезависимо, убираем пробелы)
    is_correct = user_answer.lower() == task["answer"].lower()
    
    if is_correct:
        session["score"] += 1
        await update.message.reply_text(f"✅ Правильно! Ответ: {task['answer']}")
    else:
        await update.message.reply_text(f"❌ Неправильно. Правильный ответ: {task['answer']}")
    
    session["user_answers"].append({
        "question": task["question"],
        "user_answer": user_answer,
        "correct_answer": task["answer"],
        "is_correct": is_correct
    })
    
    session["current"] += 1
    context.user_data["awaiting_word_formation"] = False
    
    if session["current"] >= session["total"]:
        await finish_word_formation_from_message(update, context)
    else:
        await show_word_formation_question_from_message(update, context)

async def show_word_formation_question_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает следующий вопрос после ответа"""
    session = context.user_data.get("word_formation")
    if not session:
        return
    
    current = session["current"]
    tasks = session["tasks"]
    
    if current >= session["total"]:
        await finish_word_formation_from_message(update, context)
        return
    
    task = tasks[current]
    
    text = f"📝 *Словообразование*\n\n"
    text += f"Задание {current + 1} из {session['total']}:\n\n"
    text += f"{task['question']}\n\n"
    text += "✏️ *Напиши преобразованное слово в чат:*"
    
    await update.message.reply_text(text)
    
    context.user_data["awaiting_word_formation"] = True

async def finish_word_formation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает задание 4 (из callback)"""
    await finish_word_formation_internal(update, context)

async def finish_word_formation_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершает задание 4 (из сообщения)"""
    await finish_word_formation_internal(update, context)

async def finish_word_formation_internal(update, context):
    """Внутренняя функция завершения задания 4"""
    session = context.user_data.get("word_formation")
    if not session:
        return
    
    total = session["total"]
    score = session["score"]
    percent = int(score / total * 100) if total > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально! Ты мастер словообразования!"
    elif percent >= 80:
        emoji, comment = "🎉", "Отличный результат!"
    elif percent >= 60:
        emoji, comment = "📚", "Неплохо! Но стоит повторить правила."
    else:
        emoji, comment = "💪", "Нужно больше практики!"
    
    details = ""
    for i, ans in enumerate(session["user_answers"]):
        icon = "✅" if ans["is_correct"] else "❌"
        details += f"{i+1}. {ans['question']}\n"
        details += f"   {icon} Ты: {ans['user_answer']} | Правильно: {ans['correct_answer']}\n"
    
    result_text = f"{emoji} *Результат!*\n\n"
    result_text += f"📊 {score}/{total} ({percent}%)\n\n"
    result_text += f"{comment}\n\n"
    
    bar_length = 10
    filled = int(percent / 100 * bar_length)
    bar = "🟩" * filled + "⬜" * (bar_length - filled)
    result_text += f"{bar} {percent}%\n\n"
    
    result_text += f"📋 *Детали:*\n{details}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_word_formation")],
        [InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Определяем, откуда пришёл вызов
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    del context.user_data["word_formation"]
    context.user_data["awaiting_word_formation"] = False

# ===== ОГЭ: ЛЕКСИКО-ГРАММАТИЧЕСКИЕ ТРАНСФОРМАЦИИ =====

def load_lexical_grammar():
    """Загружает задания по лексико-грамматическим трансформациям"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_paths = [
            os.path.join(base_dir, "oge_lexical_grammar.json"),
            os.path.join("/app", "oge_lexical_grammar.json"),
            os.path.join(os.getcwd(), "oge_lexical_grammar.json")
        ]
        
        for path in json_paths:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        print(f"❌ oge_lexical_grammar.json не найден. Проверены пути: {json_paths}")
        return None
    except Exception as e:
        print(f"❌ Ошибка загрузки oge_lexical_grammar.json: {e}")
        return None

async def start_lexical_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает задание — лексико-грамматические трансформации"""
    data = load_lexical_grammar()
    if not data:
        await update.callback_query.answer("❌ Задания не загружены", show_alert=True)
        return
    
    context.user_data["lexical_grammar"] = {
        "tasks": data["tasks"],
        "current": 0,
        "score": 0,
        "user_answers": [],
        "total": len(data["tasks"])
    }
    
    await show_lexical_question(update, context)

async def show_lexical_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущее задание с выбором части речи"""
    session = context.user_data.get("lexical_grammar")
    if not session:
        return
    
    current = session["current"]
    tasks = session["tasks"]
    
    if current >= session["total"]:
        await finish_lexical_grammar(update, context)
        return
    
    task = tasks[current]
    
    text = f"📝 *Лексико-грамматическая трансформация*\n\n"
    text += f"Задание {current + 1} из {session['total']}:\n\n"
    text += f"{task['question']}\n\n"
    text += "⬇️ *Сначала выбери часть речи:*"
    
    keyboard = [
        [InlineKeyboardButton("📝 Существительное (noun)", callback_data=f"lg_pos_noun_{current}")],
        [InlineKeyboardButton("📝 Глагол (verb)", callback_data=f"lg_pos_verb_{current}")],
        [InlineKeyboardButton("📝 Прилагательное (adjective)", callback_data=f"lg_pos_adjective_{current}")],
        [InlineKeyboardButton("📝 Наречие (adverb)", callback_data=f"lg_pos_adverb_{current}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_lexical_pos(update: Update, context: ContextTypes.DEFAULT_TYPE, pos: str, task_idx: int):
    """Обрабатывает выбор части речи"""
    query = update.callback_query
    session = context.user_data.get("lexical_grammar")
    if not session:
        await query.answer("❌ Сессия устарела", show_alert=True)
        return
    
    if task_idx != session["current"]:
        await query.answer("⏳ Это задание уже выполнено!", show_alert=True)
        return
    
    task = session["tasks"][task_idx]
    is_pos_correct = (pos == task["part_of_speech"])
    
    # Сохраняем ответ по части речи
    session["user_answers"].append({
        "question": task["question"],
        "selected_pos": pos,
        "correct_pos": task["part_of_speech"],
        "is_pos_correct": is_pos_correct,
        "correct_answer": task["answer"]
    })
    
    if is_pos_correct:
        await query.answer("✅ Часть речи верная! Теперь напиши слово.")
    else:
        await query.answer(f"❌ Неправильно! Правильно: {task['part_of_speech']}", show_alert=True)
    
    # Переход к вводу слова
    context.user_data["awaiting_lexical_word"] = True
    
    await query.edit_message_text(
        f"📝 *Введи слово*\n\n"
        f"Задание {task_idx + 1} из {session['total']}:\n\n"
        f"{task['question']}\n\n"
        f"✏️ *Напиши преобразованное слово в чат:*"
    )

async def handle_lexical_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод слова"""
    word = update.message.text.strip().lower()
    session = context.user_data.get("lexical_grammar")
    if not session:
        await update.message.reply_text("❌ Сессия устарела. Начни заново.")
        return
    
    current = session["current"]
    if current >= session["total"]:
        return
    
    task = session["tasks"][current]
    is_word_correct = (word == task["answer"].lower())
    
    # Обновляем ответ
    session["user_answers"][-1]["user_word"] = word
    session["user_answers"][-1]["is_word_correct"] = is_word_correct
    
    if is_word_correct:
        session["score"] += 1
        await update.message.reply_text(f"✅ Правильно! '{task['answer']}' — верно!")
    else:
        await update.message.reply_text(f"❌ Неправильно. Правильный ответ: {task['answer']}")
    
    session["current"] += 1
    context.user_data["awaiting_lexical_word"] = False
    
    if session["current"] >= session["total"]:
        await finish_lexical_grammar_from_message(update, context)
    else:
        await show_lexical_question_from_message(update, context)

async def show_lexical_question_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает следующий вопрос (из сообщения)"""
    session = context.user_data.get("lexical_grammar")
    if not session:
        return
    
    current = session["current"]
    tasks = session["tasks"]
    
    if current >= session["total"]:
        await finish_lexical_grammar_from_message(update, context)
        return
    
    task = tasks[current]
    
    text = f"📝 *Лексико-грамматическая трансформация*\n\n"
    text += f"Задание {current + 1} из {session['total']}:\n\n"
    text += f"{task['question']}\n\n"
    text += "⬇️ *Сначала выбери часть речи:*"
    
    keyboard = [
        [InlineKeyboardButton("📝 Существительное (noun)", callback_data=f"lg_pos_noun_{current}")],
        [InlineKeyboardButton("📝 Глагол (verb)", callback_data=f"lg_pos_verb_{current}")],
        [InlineKeyboardButton("📝 Прилагательное (adjective)", callback_data=f"lg_pos_adjective_{current}")],
        [InlineKeyboardButton("📝 Наречие (adverb)", callback_data=f"lg_pos_adverb_{current}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def finish_lexical_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await finish_lexical_grammar_internal(update, context)

async def finish_lexical_grammar_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await finish_lexical_grammar_internal(update, context)

async def finish_lexical_grammar_internal(update, context):
    """Завершает задание"""
    session = context.user_data.get("lexical_grammar")
    if not session:
        return
    
    total = session["total"]
    score = session["score"]
    percent = int(score / total * 100) if total > 0 else 0
    
    if percent == 100:
        emoji, comment = "🏆", "Идеально! Ты мастер словообразования!"
    elif percent >= 80:
        emoji, comment = "🎉", "Отличный результат!"
    elif percent >= 60:
        emoji, comment = "📚", "Неплохо! Но стоит повторить."
    else:
        emoji, comment = "💪", "Нужно больше практики!"
    
    details = ""
    for i, ans in enumerate(session["user_answers"]):
        pos_icon = "✅" if ans.get("is_pos_correct", False) else "❌"
        word_icon = "✅" if ans.get("is_word_correct", False) else "❌"
        details += f"{i+1}. {ans['question'][:60]}...\n"
        details += f"   Часть речи: {pos_icon} {ans['selected_pos']} (правильно: {ans['correct_pos']})\n"
        details += f"   Слово: {word_icon} {ans.get('user_word', '—')} (правильно: {ans['correct_answer']})\n\n"
    
    result_text = f"{emoji} *Результат!*\n\n"
    result_text += f"📊 {score}/{total} ({percent}%)\n\n"
    result_text += f"{comment}\n\n"
    
    bar_length = 10
    filled = int(percent / 100 * bar_length)
    bar = "🟩" * filled + "⬜" * (bar_length - filled)
    result_text += f"{bar} {percent}%\n\n"
    result_text += f"📋 *Детали:*\n{details}"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти заново", callback_data="start_lexical_grammar")],
        [InlineKeyboardButton("🔙 Назад в ОГЭ", callback_data="oge_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(result_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    del context.user_data["lexical_grammar"]
    context.user_data["awaiting_lexical_word"] = False
# ===== BUTTON CALLBACK =====

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "back_to_levels":
        await show_levels(update, context)
    elif data == "total_progress":
        await show_total_progress(update, context)
    elif data == "logout":
        await logout(update, context)
    elif data == "login":
        await show_login(update, context)
    elif data == "register":
        await show_register(update, context)
    elif data == "admin_users":
        await admin_users(update, context)
    elif data == "noop":
        pass
    elif data.startswith("level_"):
        await show_categories(update, context, data[6:])
    elif data.startswith("cat_"):
        parts = data[4:].split("|")
        await show_topics(update, context, parts[0], parts[1], 0)
    elif data.startswith("topic_"):
        parts = data[6:].split("|")
        await show_topic_menu(update, context, parts[0], parts[1], parts[2])
    elif data.startswith("page_"):
        parts = data[5:].split("|")
        await show_topics(update, context, parts[0], parts[1], int(parts[2]))
    elif data.startswith("expl_"):
        parts = data[5:].split("|")
        await show_explanation(update, context, parts[0], parts[1], parts[2])
    elif data.startswith("vocab_"):
        parts = data[6:].split("|")
        await show_vocabulary(update, context, parts[0], parts[1], parts[2])
    elif data.startswith("tog_"):
        parts = data[4:].split("|")
        await toggle_topic_handler(update, context, parts[0], parts[1], parts[2])
    elif data.startswith("test_"):
        parts = data[5:].split("|")
        await start_test(update, context, parts[0], parts[1], parts[2])
    elif data.startswith("ans_"):
        await handle_answer(update, context, int(data[4:]))
    elif data == "diagnostic":
        await start_diagnostic(update, context)
    elif data == "diag_restart":
        await start_diagnostic(update, context)
    elif data.startswith("diag_ans_"):
        await handle_diagnostic_answer(update, context, int(data[9:]))
    elif data == "oge_menu":
        await oge_menu(update, context)
    elif data == "oge_reading":
        await oge_reading_menu(update, context)
    elif data == "oge_matching":
        await start_oge_matching(update, context)
    elif data == "oge_tfns":
        await start_oge_tfns(update, context)
    elif data.startswith("oge_match_show_"):
        text_id = data[15:]
        await show_oge_matching_text(update, context, text_id)
    elif data.startswith("oge_match_start_"):
        await start_oge_matching_questions(update, context)
    elif data.startswith("oge_match_ans_"):
        parts = data[14:].split("_")
        answer_letter = parts[0]
        q_index = int(parts[1])
        await handle_oge_matching_answer(update, context, answer_letter, q_index)
    elif data == "oge_word_formation":
        await start_oge_word_formation(update, context)
    elif data.startswith("oge_word_pos_"):
        parts = data[13:].split("_")
        pos = parts[0]
        idx = int(parts[1])
        await handle_oge_word_pos(update, context, pos, idx)
    elif data.startswith("oge_tfns_show_"):
        text_id = data[14:]
        await show_oge_tfns_text(update, context, text_id)
    elif data.startswith("oge_tfns_start_"):
        await start_oge_tfns_questions(update, context)
    elif data.startswith("oge_tfns_ans_"):
        parts = data[13:].split("_")
        answer = parts[0]
        q_index = int(parts[1])
        await handle_oge_tfns_answer(update, context, answer, q_index)
    elif data == "oge_audio":
        await update.callback_query.answer("🎧 Аудирование пока в разработке!", show_alert=True)
    elif data == "oge_letter":
        await update.callback_query.answer("✉️ Письмо пока в разработке!", show_alert=True)
    elif data == "oge_text_reading":
        await update.callback_query.answer("📖 Чтение текста пока в разработке!", show_alert=True)
    elif data == "oge_monologue":
        await update.callback_query.answer("🎤 Монолог пока в разработке!", show_alert=True)
    elif data == "oge_assistant":
        await update.callback_query.answer("📱 Electronic Assistant пока в разработке!", show_alert=True)
    elif data == "start_audio_choice":
        await start_audio_choice(update, context)
    elif data == "audio_choice_restart":
        await start_audio_choice(update, context)
    elif data == "audio_choice_noop":
        await query.answer()
    elif data.startswith("audio_choice_ans_"):
        parts = data[17:].split("_")
        answer_idx = int(parts[0])
        q_index = int(parts[1])
        await handle_audio_choice_answer(update, context, answer_idx, q_index)
    elif data == "start_audio_matching":
        await start_audio_matching(update, context)
    elif data == "start_audio_fill":
        await start_audio_fill(update, context)
    elif data.startswith("matching_ans_"):
        parts = data[13:].split("_")
        rubric_idx = int(parts[0])
        speaker_idx = int(parts[1])
        await handle_matching_answer(update, context, rubric_idx, speaker_idx)
    elif data == "start_word_formation":
        await start_word_formation(update, context)
    elif data == "start_lexical_grammar":
        await start_lexical_grammar(update, context)
    elif data.startswith("lg_pos_"):
        parts = data[7:].split("_")
        pos = parts[0]
        task_idx = int(parts[1])
        await handle_lexical_pos(update, context, pos, task_idx)
    

# ===== MAIN =====

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CommandHandler("debug", debug_paths))
    print("🎓 Soloway English Tracker запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()