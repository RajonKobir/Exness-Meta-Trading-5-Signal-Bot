import requests


class TelegramService:

    def __init__(self, token, chat_id):

        self.token = token
        self.chat_id = chat_id

    def send_message(self, message):

        try:

            url = f"https://api.telegram.org/bot{self.token}/sendMessage"

            data = {
                "chat_id": self.chat_id,
                "text": message
            }

            resp = requests.post(url, data=data, timeout=10)

            try:
                payload = resp.json()
            except Exception:
                payload = None

            success = (resp.status_code == 200 and payload and payload.get("ok", False))

            details = {
                "status_code": resp.status_code,
                "payload": payload,
                "text": resp.text
            }

            return success, details

        except Exception as e:

            return False, {"error": str(e)}