import jwt

JWT_SECRET = "dJaNg0w3bdnasecretkey!#@!_dontshare..."


def encode(user_object):
    return jwt.encode(user_object, JWT_SECRET, algorithm='HS256')


def decode_user(token):
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
