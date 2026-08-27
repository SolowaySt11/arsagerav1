import requests

TOKEN = "8776459772:AAHJZrqZ_IYOGpP6OD67dkG1GOBdHaC0XLo"

response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?limit=100")
data = response.json()

for update in data.get("result", []):
    if "message" in update and "audio" in update["message"]:
        audio = update["message"]["audio"]
        print(f"Файл: {audio.get('file_name')}")
        print(f"file_id: {audio['file_id']}")
        print("-" * 50)