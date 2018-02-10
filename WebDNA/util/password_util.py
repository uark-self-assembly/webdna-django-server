import bcrypt


def check_password(raw_password, hashed_password):
    return bcrypt.checkpw(raw_password.encode('utf-8'), hashed_password.encode('utf-8'))


def hash_password(raw_password):
    return bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())
