import os
import re
import webbrowser

import geocoder
import requests
from dotenv import load_dotenv

from core_voice import speak

load_dotenv()

try:
    from twilio.rest import Client
except Exception:
    Client = None


TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
EMERGENCY_CONTACT = os.getenv("EMERGENCY_CONTACT")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ENABLE_REMOTE_SOS = os.getenv("ENABLE_REMOTE_SOS", "false").lower() in {"1", "true", "yes", "on"}

contacts = {
    "dhruvin": "9913635130",
    "": "9879674896",
    "mummy": "8488901762",
    "grandfather": "9879665906",
    "harsh": "9727009440",
}


def is_valid_config(value):
    return isinstance(value, str) and value.strip() != "" and not value.strip().startswith("#")


def get_location():
    g = geocoder.ip("me")
    if g.latlng:
        return g.latlng
    return None


def build_sos_message():
    location = get_location()
    if location:
        return f"🚨 SOS Alert! Emergency at location: {location} 🚨\nGoogle Maps: https://www.google.com/maps/search/?api=1&query={location[0]},{location[1]}"
    return "🚨 SOS Alert! Location not found. Please check manually."


def send_sos_via_telegram(sos_message):
    if not (is_valid_config(TELEGRAM_BOT_TOKEN) and is_valid_config(TELEGRAM_CHAT_ID)):
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": sos_message}
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    print("SOS alert sent via Telegram")
    return True


def send_sos_via_twilio(sos_message):
    if Client is None:
        return False
    required = [TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, EMERGENCY_CONTACT]
    if not all(is_valid_config(v) for v in required):
        return False
    msg = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = msg.messages.create(body=sos_message, from_=TWILIO_PHONE_NUMBER, to=EMERGENCY_CONTACT)
    print(f"SOS SMS sent via Twilio! Message SID: {message.sid}")
    return True


def send_sos_sms():
    sos_message = build_sos_message()
    location = get_location()
    if location:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={location[0]},{location[1]}"
        webbrowser.open(maps_url)
    speak("Emergency mode activated. I have prepared your location and opened maps.")
    print(sos_message)
    if not ENABLE_REMOTE_SOS:
        return True
    try:
        if send_sos_via_telegram(sos_message):
            speak("SOS alert sent successfully via Telegram.")
            return True
    except Exception as e:
        print(f"Telegram SOS failed: {e}")
    try:
        if send_sos_via_twilio(sos_message):
            speak("SOS alert sent successfully via Twilio.")
            return True
    except Exception as e:
        print(f"Twilio SOS failed: {e}")
    speak("Remote SOS send failed. Local emergency mode is active.")
    return True


def validate_phone_number(number):
    return re.match(r"^\d{10}$", number)


def get_phone_number(contact_name):
    contact_name = contact_name.lower()
    return contacts.get(contact_name, None)


def send_whatsapp_message(contact_name, message):
    phone_number = get_phone_number(contact_name)
    if phone_number and validate_phone_number(phone_number):
        try:
            from pywhatkit import sendwhatmsg_instantly
            sendwhatmsg_instantly(f"+91{phone_number}", message, wait_time=10)
            speak("Message sent successfully.")
        except Exception as e:
            speak(f"I couldn't send the WhatsApp message. {str(e)}")
    else:
        speak("Invalid contact name or number.")
