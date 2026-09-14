import secrets

def create_secret_key():
    with open("key.txt", "w") as file:
        file.write(secrets.token_hex(128)
    )
create_secret_key()