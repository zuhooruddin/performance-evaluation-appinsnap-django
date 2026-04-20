import json
import os

BASE_PATH = "data"
AUTH_FILE = f"{BASE_PATH}/auth_users.json"
OTP_FILE = f"{BASE_PATH}/otp_store.json"


def ensure_files():
    os.makedirs(BASE_PATH, exist_ok=True)

    if not os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "w") as f:
            json.dump({}, f)

    if not os.path.exists(OTP_FILE):
        with open(OTP_FILE, "w") as f:
            json.dump({}, f)


def load_users():
    ensure_files()
    with open(AUTH_FILE, "r") as f:
        return json.load(f)


def save_users(data):
    with open(AUTH_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_otps():
    ensure_files()
    with open(OTP_FILE, "r") as f:
        return json.load(f)


def save_otps(data):
    with open(OTP_FILE, "w") as f:
        json.dump(data, f, indent=4)