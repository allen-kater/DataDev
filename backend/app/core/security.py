"""密码字段加密（rules/10：入库前 AES 加密，禁明文落库/落日志）。

密钥来源：
1. 环境变量 `DATAFLOW_SECRET_KEY`（base64 编码的 32 字节，生产推荐）；
2. 未设置时生成随机密钥持久化到 `data/.secret_key`（该目录已 gitignore）。

加密格式：`gcm$<base64(nonce)>$<base64(ciphertext)>`，AES-256-GCM 带认证。
"""

import base64
import os
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import DATA_DIR

_PREFIX = "gcm$"
_KEY_FILE = DATA_DIR / ".secret_key"


@lru_cache
def _get_key() -> bytes:
    """获取 32 字节 AES 密钥（环境变量优先，其次持久化文件）。"""
    env = os.getenv("DATAFLOW_SECRET_KEY")
    if env:
        return base64.b64decode(env.encode("utf-8"))
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()
    key = AESGCM.generate_key(bit_length=256)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_bytes(key)
    return key


def encrypt_plaintext(plaintext: str) -> str:
    """明文 → 密文字符串（无明文时原样返回空串）。"""
    if not plaintext:
        return ""
    nonce = os.urandom(12)
    ct = AESGCM(_get_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    nonce_b64 = base64.b64encode(nonce).decode()
    ct_b64 = base64.b64encode(ct).decode()
    return f"{_PREFIX}{nonce_b64}${ct_b64}"


def decrypt_ciphertext(ciphertext: str) -> str:
    """密文字符串 → 明文；空串或格式异常返回空串（不抛错，避免影响读取）。"""
    if not ciphertext or not ciphertext.startswith(_PREFIX):
        return ""
    try:
        _, nonce_b64, ct_b64 = ciphertext.split("$", 2)
        nonce = base64.b64decode(nonce_b64)
        ct = base64.b64decode(ct_b64)
        return AESGCM(_get_key()).decrypt(nonce, ct, None).decode("utf-8")
    except Exception:
        return ""
