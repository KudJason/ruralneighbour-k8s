# 示例：不使用 passlib 的实现（仅供参考，不推荐）

from datetime import datetime, timedelta
from typing import Any, Optional, Union

import bcrypt
from jose import jwt

from .config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        # 需要手动处理编码
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")  # 或 bytes
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """哈希密码"""
    # 需要手动设置 rounds
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    # 需要手动解码
    return hashed.decode("utf-8")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": "user",
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 如果将来要切换到 Argon2，需要：
# 1. 重写 verify_password()
# 2. 重写 get_password_hash()
# 3. 需要检测哈希类型（bcrypt 还是 argon2）
# 4. 手动实现迁移逻辑
# 5. 更新所有测试
# ... 工作量巨大！😱
