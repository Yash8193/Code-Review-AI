from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from dotenv import load_dotenv

from groq import Groq

import os

# ================= LOAD ENV =================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

# ================= IMPORTS =================

from database import (
    Base,
    engine,
    get_db
)

from models import User

from schemas import (
    UserCreate,
    UserLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest
)

from auth import (
    hash_password,
    verify_password,
    otp_storage,
    generate_otp
)

# ================= APP =================

app = FastAPI(
    title="CodeReviewAI"
)

# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DATABASE =================

Base.metadata.create_all(bind=engine)

# ================= GROQ =================

api_key = os.getenv("GROQ_API_KEY")

if not api_key:

    print("⚠️ GROQ_API_KEY missing")

    client = None

else:

    client = Groq(
        api_key=api_key
    )

    print("✅ GROQ Connected")

# ================= ROOT =================

@app.get("/")
def root():

    return {
        "message": "Backend running 🚀"
    }

# ================= SIGNUP =================

@app.post("/signup")
def signup(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(
            user.password
        )
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return {
        "message": "Signup successful"
    }

# ================= LOGIN =================

@app.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    db_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if not db_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username"
        )

    if not verify_password(
        user.password,
        db_user.password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    return {
        "username": db_user.username,
        "message": "Login successful"
    }

# ================= FORGOT PASSWORD =================

@app.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.username == data.username
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    otp = generate_otp()

    otp_storage[data.username] = otp

    print(f"\n✅ OTP for {data.username}: {otp}\n")

    return {
        "message": "OTP sent successfully"
    }

# ================= RESET PASSWORD =================

@app.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    saved_otp = otp_storage.get(
        data.username
    )

    if not saved_otp:

        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )

    if saved_otp != data.otp:

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )

    user = db.query(User).filter(
        User.username == data.username
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user.password = hash_password(
        data.new_password
    )

    db.commit()

    del otp_storage[data.username]

    return {
        "message": "Password reset successful"
    }

# ================= REVIEW =================

@app.post("/review")
def review_code(payload: dict):

    if not payload.get("code"):

        raise HTTPException(
            status_code=400,
            detail="Code required"
        )

    if not client:

        raise HTTPException(
            status_code=500,
            detail="Groq API missing"
        )

    prompt = f"""
You are a senior software engineer.

Analyze the following {payload.get("language")} code.

VERY IMPORTANT:
For every issue return EXACTLY in this format:

CRITICAL: line_number | problematic_code
HIGH: line_number | problematic_code
MEDIUM: line_number | problematic_code
LOW: line_number | problematic_code

Only return real issues.

Code:
{payload.get("code")}
"""

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.3,

            max_tokens=1200,
        )

        return {
            "review":
            response.choices[0].message.content
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ================= REWRITE =================

@app.post("/rewrite")
def rewrite_code(payload: dict):

    if not payload.get("code"):

        raise HTTPException(
            status_code=400,
            detail="Code required"
        )

    if not client:

        raise HTTPException(
            status_code=500,
            detail="Groq API missing"
        )

    prompt = f"""
Rewrite this {payload.get("language")} code
using:

- Best practices
- Optimization
- Better readability
- Security improvements

Return only improved code.

Code:
{payload.get("code")}
"""

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.3,

            max_tokens=1200,
        )

        return {
            "rewritten_code":
            response.choices[0].message.content
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )