from pydantic import BaseModel

# ================= SIGNUP =================

class UserCreate(BaseModel):

    username: str

    email: str

    password: str


# ================= LOGIN =================

class UserLogin(BaseModel):

    username: str

    password: str


# ================= FORGOT PASSWORD =================

class ForgotPasswordRequest(BaseModel):

    username: str


# ================= RESET PASSWORD =================

class ResetPasswordRequest(BaseModel):

    username: str

    otp: str

    new_password: str