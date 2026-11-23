import os
import re
import requests

class SmsService:
    def __init__(self, mode="simulation", db=None):
        self.mode = mode
        self.db = db

    def valid_phone(self, phone):
        value = str(phone or "").strip()
        return bool(re.fullmatch(r"\+[1-9][0-9]{7,14}", value))

    def normalize_phone(self, phone):
        value = str(phone or "").strip().replace(" ", "").replace("-", "")
        if value.startswith("00"):
            value = "+" + value[2:]
        elif value and not value.startswith("+"):
            value = "+91" + value[-10:] if len(value[-10:]) == 10 else "+" + value
        return value

    def send(self, phone, message, incident_id=None, recipient_id=None):
        phone = self.normalize_phone(phone)
        if not self.valid_phone(phone):
            return {"status": "failed", "provider": "validation", "response": "Invalid recipient phone"}

        if self.mode == "real":
            sid, token, sender = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), os.getenv("TWILIO_FROM_NUMBER")
            if not all([sid, token, sender]):
                return {"status": "failed", "provider": "twilio", "response": "Real SMS unavailable: credentials missing"}
            try:
                data = {"To": phone, "From": sender, "Body": message}
                callback_url = os.getenv("TWILIO_STATUS_CALLBACK_URL", "")
                if callback_url:
                    data["StatusCallback"] = callback_url
                response = requests.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                    data=data, auth=(sid, token), timeout=10)
                if response.ok:
                    data = response.json()
                    return {"status": "accepted", "provider": "twilio", "response": data.get("sid", "accepted"), "delivery_confirmation": "provider_accepted_not_confirmed"}
                return {"status": "failed", "provider": "twilio", "response": response.text[:300]}
            except requests.RequestException as exc:
                return {"status": "failed", "provider": "twilio", "response": str(exc)[:300]}

        # Predictable demonstration: the configured test recipient gets a transient failure once.
        if str(recipient_id) == "5":
            return {"status": "failed", "provider": "simulation", "response": "SIMULATED_TRANSIENT_FAILURE", "mode": "simulation"}
        return {"status": "success", "provider": "simulation", "response": "SIMULATION_DELIVERED", "mode": "simulation"}
