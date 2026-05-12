import os
from loguru import logger

class TwilioClient:
    def __init__(self):
        self.sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

    def is_configured(self):
        return bool(self.sid and self.token and self.from_number)

    def send_sms(self, to, body):
        if not self.is_configured():
            return "Twilio not configured. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to .env."

        try:
            from twilio.rest import Client
            client = Client(self.sid, self.token)
            message = client.messages.create(
                body=body,
                from_=self.from_number,
                to=to
            )
            return {"sid": message.sid, "status": message.status, "to": to}
        except Exception as e:
            logger.error(f"Twilio Error: {e}")
            return f"Failed to send SMS: {str(e)}"
