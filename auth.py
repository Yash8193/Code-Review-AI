from passlib.context import CryptContext
import random

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ================= HASH PASSWORD =================

def hash_password(password: str) -> str:

    return pwd_context.hash(password)

# ================= VERIFY PASSWORD =================

def verify_password(
    plain: str,
    hashed: str
) -> bool:

    return pwd_context.verify(plain, hashed)

# ================= OTP STORAGE =================

otp_storage = {}

# ================= GENERATE OTP =================

def generate_otp():

    return str(random.randint(100000, 999999))