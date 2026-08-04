from app.modules.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)

password = "Admin@123"

hashed = hash_password(password)
print("Hash:", hashed)

print("Verify:", verify_password(password, hashed))

token = create_access_token(subject="1")
print("Token:", token)

decoded = decode_token(token)
print("Decoded:", decoded)