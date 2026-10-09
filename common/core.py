import os, json, logging, socket, hashlib, secrets
from datetime import datetime, timedelta, timezone
from fastapi import Header, HTTPException
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-change-me")
ALGORITHM = "HS256"
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "college-project-key")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": os.getenv("SERVICE_NAME", "service"),
            "message": record.getMessage(),
        })

class LogstashHandler(logging.Handler):
    def emit(self, record):
        host=os.getenv("ELK_HOST")
        if not host: return
        try:
            payload=self.format(record)+"\n"
            with socket.create_connection((host, int(os.getenv("ELK_PORT","5000"))), timeout=0.4) as s:
                s.sendall(payload.encode())
        except Exception:
            pass

def setup_logging():
    logger=logging.getLogger("app")
    logger.setLevel(logging.INFO)
    if logger.handlers: return logger
    sh=logging.StreamHandler(); sh.setFormatter(JsonFormatter()); logger.addHandler(sh)
    if os.getenv("ELK_HOST"):
        lh=LogstashHandler(); lh.setFormatter(JsonFormatter()); logger.addHandler(lh)
    return logger

def hash_password(password):
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120000)
    return salt.hex()+":"+digest.hex()

def verify_password(password, stored):
    try:
        salt_hex,digest_hex=stored.split(":")
        digest=hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120000)
        return secrets.compare_digest(digest.hex(), digest_hex)
    except Exception: return False

def create_token(user_id, role, email):
    payload={"sub":str(user_id),"role":role,"email":email,"exp":datetime.now(timezone.utc)+timedelta(hours=8)}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token):
    try: return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except Exception: raise HTTPException(status_code=401, detail="Invalid or expired token")

def auth_user(authorization: str|None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    return decode_token(authorization.split(" ",1)[1])

def internal_key(x_internal_key: str|None = Header(default=None)):
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Internal access only")
