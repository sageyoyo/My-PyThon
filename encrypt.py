from cryptography.fernet import Fernet

PASSWORD = "0717Pmacnhl"

key = Fernet.generate_key()
with open(r"C:\jobcan_profile\key.bin", "wb") as f:
    f.write(key)

f = Fernet(key)
encrypted = f.encrypt(PASSWORD.encode())
with open(r"C:\jobcan_profile\pwd.bin", "wb") as f2:
    f2.write(encrypted)

print("密码已加密保存完成")