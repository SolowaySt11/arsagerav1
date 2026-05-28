async def send_chart(update, fund_code, fund_name, period_days):
    data = get_all_fund_data(fund_code)
    if not data:
        await update.callback_query.edit_message_text(f"❌ Нет данных для построения графика {fund_name}")
        return
    
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
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches="tight")
    buf.seek(0)
    plt.close()
    
    # Отправляем новым сообщением (не редактируем старое)
    await update.callback_query.message.reply_photo(buf, caption=f"📈 {fund_name} — динамика за {period_days} дней")