import random
import time


class OTPManager:

    OTP_EXPIRY = 300

    @staticmethod
    def generate():

        otp = str(random.randint(100000, 999999))
        expiry = time.time() + OTPManager.OTP_EXPIRY

        return otp, expiry

    @staticmethod
    def is_valid(stored_otp, stored_expiry, user_otp):

        if time.time() > stored_expiry:
            return False, "OTP expired"

        if stored_otp != user_otp:
            return False, "Invalid OTP"

        return True, "OTP verified"