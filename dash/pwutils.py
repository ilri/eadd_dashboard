from passlib.hash import pbkdf2_sha256


def hash_password(password):
    return pbkdf2_sha256.encrypt(password, rounds=25600)


def verify_password(password, hash):
    return pbkdf2_sha256.verify(password, hash)
