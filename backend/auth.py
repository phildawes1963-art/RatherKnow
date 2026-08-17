"""Email + password auth. Results are retrieved by logging in; no email is sent."""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal

import hashlib
import secrets

import bcrypt
import jwt
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field

from database import db
from email_service import send_email, password_reset_html

router = APIRouter(prefix="/api/auth", tags=["Auth"])

JWT_ALGORITHM = "HS256"
ACCESS_TTL = timedelta(days=30)
SITUATIONS = ("single_dating", "in_relationship", "post_breakup")
SITUATION_LABELS = {
    "single_dating": "Single & dating",
    "in_relationship": "In a relationship",
    "post_breakup": "Post-breakup",
}
MAX_FAILED = 5
LOCKOUT = timedelta(minutes=15)
RESET_TTL = timedelta(minutes=60)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def assert_session_owner(session: dict, user: dict):
    """A session may only be written or read by the account that started it."""
    owner = session.get("user_id")
    if owner and owner != str(user["_id"]):
        raise HTTPException(status_code=403, detail="That session belongs to another account.")


def _secret() -> str:
    return os.environ["JWT_SECRET"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + ACCESS_TTL,
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    situation: Literal["single_dating", "in_relationship", "post_breakup"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ClaimRequest(BaseModel):
    session_ids: List[str] = Field(default_factory=list)


class ForgotRequest(BaseModel):
    email: EmailStr


class ResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=8, max_length=128)


def _public(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "situation": user["situation"],
        "situation_label": SITUATION_LABELS.get(user["situation"], user["situation"]),
        "created_at": user.get("created_at"),
    }


def _decode(token: str) -> dict:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload


def _bearer(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return request.cookies.get("access_token")


async def get_current_user(request: Request) -> dict:
    token = _bearer(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = _decode(token)
    user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_optional_user(request: Request) -> Optional[dict]:
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def _lockout_guard(identifier: str):
    doc = await db.login_attempts.find_one({"identifier": identifier})
    if not doc:
        return
    if doc.get("count", 0) >= MAX_FAILED:
        locked_until = doc.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Too many attempts. Try again in a few minutes.")
        await db.login_attempts.delete_one({"identifier": identifier})


async def _record_failure(identifier: str):
    doc = await db.login_attempts.find_one({"identifier": identifier})
    count = (doc.get("count", 0) if doc else 0) + 1
    update = {"identifier": identifier, "count": count}
    if count >= MAX_FAILED:
        update["locked_until"] = (datetime.now(timezone.utc) + LOCKOUT).isoformat()
    await db.login_attempts.update_one({"identifier": identifier}, {"$set": update}, upsert=True)


async def _claim(user_id: str, session_ids: List[str]) -> int:
    if not session_ids:
        return 0
    res = await db.mirror_v2_sessions.update_many(
        {"id": {"$in": session_ids}, "user_id": {"$in": [None, user_id]}},
        {"$set": {"user_id": user_id}},
    )
    await db.results.update_many(
        {"session_id": {"$in": session_ids}, "user_id": {"$in": [None, user_id]}},
        {"$set": {"user_id": user_id}},
    )
    return res.modified_count


@router.post("/register")
async def register(data: RegisterRequest):
    email = data.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account already exists for that email — log in instead.")
    doc = {
        "name": data.name.strip(),
        "email": email,
        "password_hash": hash_password(data.password),
        "situation": data.situation,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    res = await db.users.insert_one(doc)
    doc["_id"] = res.inserted_id
    return {"user": _public(doc), "access_token": create_access_token(str(res.inserted_id), email)}


@router.post("/login")
async def login(data: LoginRequest, request: Request):
    email = data.email.lower().strip()
    identifier = email
    await _lockout_guard(identifier)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        await _record_failure(identifier)
        raise HTTPException(status_code=401, detail="That email and password don’t match.")
    await db.login_attempts.delete_one({"identifier": identifier})
    return {"user": _public(user), "access_token": create_access_token(str(user["_id"]), email)}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": _public(user)}


@router.post("/forgot-password")
async def forgot_password(data: ForgotRequest):
    """Always answers the same way — an attacker learns nothing about who has an account."""
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_resets.delete_many({"user_id": str(user["_id"])})
        await db.password_resets.insert_one({
            "user_id": str(user["_id"]),
            "token_hash": _hash_token(token),
            "expires_at": (datetime.now(timezone.utc) + RESET_TTL).isoformat(),
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        reset_url = f"{os.environ['APP_BASE_URL']}/reset-password?token={token}"
        await send_email(
            to=user["email"],
            subject="Set a new password for Rather Know",
            html=password_reset_html(name=user["name"], reset_url=reset_url),
        )
    return {"sent": True}


@router.post("/reset-password")
async def reset_password(data: ResetRequest):
    record = await db.password_resets.find_one({"token_hash": _hash_token(data.token), "used": False})
    if not record or datetime.fromisoformat(record["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="That reset link has expired or already been used.")
    user = await db.users.find_one({"_id": ObjectId(record["user_id"])})
    if not user:
        raise HTTPException(status_code=400, detail="That reset link is no longer valid.")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": hash_password(data.password)}})
    await db.password_resets.update_one({"_id": record["_id"]}, {"$set": {"used": True}})
    await db.login_attempts.delete_one({"identifier": user["email"]})
    return {"user": _public(user), "access_token": create_access_token(str(user["_id"]), user["email"])}


@router.patch("/me/situation")
async def update_situation(data: dict, user: dict = Depends(get_current_user)):
    situation = data.get("situation")
    if situation not in SITUATIONS:
        raise HTTPException(status_code=400, detail="Unknown situation")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"situation": situation}})
    user["situation"] = situation
    return {"user": _public(user)}


@router.post("/claim")
async def claim_sessions(data: ClaimRequest, user: dict = Depends(get_current_user)):
    claimed = await _claim(str(user["_id"]), data.session_ids)
    return {"claimed": claimed}


@router.get("/me/sessions")
async def my_sessions(user: dict = Depends(get_current_user)):
    cursor = db.mirror_v2_sessions.find({"user_id": str(user["_id"])}, {"_id": 0, "responses": 0})
    sessions = await cursor.to_list(200)
    out = [
        {
            "session_id": s["id"],
            "instrument": s["instrument"],
            "status": s["status"],
            "started_at": s.get("started_at"),
            "completed_at": s.get("completed_at"),
        }
        for s in sessions
    ]
    out.sort(key=lambda s: s["started_at"] or "", reverse=True)
    return {"sessions": out}


async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.mirror_v2_sessions.create_index("user_id")
    await db.password_resets.create_index("token_hash")
    await db.password_resets.create_index("user_id")
