import requests
import frappe

def send_telegram_message(chat_id, message):

    url = f"https://api.telegram.org/bot8771876885:AAEOMgp9qdoZlcRYgd7Z6IXwP-Cr7q5vrIo/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    
    frappe.log_error("Success")
