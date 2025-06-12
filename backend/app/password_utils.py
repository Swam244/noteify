import bcrypt

def generate_hash(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()

def verify_hash(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())