import bcrypt


def register_user(mongo, username, email, password):
    user = {
        'name': username,
        'email': email,
        'password': password,
        'account_type': 'FREE',
        "client_sites": []
    }
    print(user)

    mongo.db.users.insert_one(user)


def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode('utf-8')


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def found_user(mongo, email):
    find_user = mongo.db.users.find_one({'email': email})
    if find_user:
        return find_user

    return None


def get_password(mongo, email):
    find_user = mongo.db.users.find_one({'email': email})
    if find_user:
        return find_user['password']

    return None


def email_already_registered(mongo, email):
    find_user = mongo.db.users.find_one({'email': email})
    if find_user:
        return True

    return False
