import os

import requests

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram_message(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return

    url = TELEGRAM_API_URL.format(token=token)
    requests.post(url, data={"chat_id": chat_id, "text": text})
