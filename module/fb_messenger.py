
import requests


class MessengerBot:
    def __init__(self, page_token):
        self.page_token = page_token
        self.api_url = f"https://graph.facebook.com/v18.0/me/messages?access_token={self.page_token}"

    def send_text(self, recipient_id, message):
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message}
        }
        return self._send(payload)

    def send_quick_replies(self, recipient_id, text, replies):
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "text": text,
                "quick_replies": replies
            }
        }
        return self._send(payload)

    def send_buttons(self, recipient_id, text, buttons):
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text,
                        "buttons": buttons
                    }
                }
            }
        }
        return self._send(payload)

    def send_generic_template(self, recipient_id, elements):
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": elements
                    }
                }
            }
        }
        return self._send(payload)

    def _send(self, payload):
        try:
            res = requests.post(self.api_url, json=payload, timeout=5)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            print("Erreur d'envoi à Messenger:", e)
            return {"error": str(e)}

