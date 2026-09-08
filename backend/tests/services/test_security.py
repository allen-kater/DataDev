"""AES 加密单元测试（rules/10：密码入库前加密，禁明文）。"""

from app.core.security import decrypt_ciphertext, encrypt_plaintext


def test_encrypt_decrypt_roundtrip():
    plain = "jc2011280574"
    ct = encrypt_plaintext(plain)
    assert ct != plain
    assert "jc2011280574" not in ct
    assert decrypt_ciphertext(ct) == plain


def test_empty_plaintext_roundtrip():
    assert encrypt_plaintext("") == ""
    assert decrypt_ciphertext("") == ""


def test_decrypt_bad_ciphertext_returns_empty():
    assert decrypt_ciphertext("not-a-cipher") == ""
    assert decrypt_ciphertext("gcm$bad$bad") == ""


def test_encrypt_produces_different_ciphertexts():
    """同一明文两次加密密文不同（随机 nonce）。"""
    plain = "hive-pass"
    assert encrypt_plaintext(plain) != encrypt_plaintext(plain)
