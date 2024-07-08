import jwt
import datetime
import secrets
import json


json_file = './secret_key.json'


def create_key():
    secret_key = secrets.token_hex(32)
    print("Secret key has been generated: ", secret_key)
    config = {
        "SECRET_KEY": secret_key
    }

    with open(json_file, 'w') as file:
        json.dump(config, file)


def generate_jwt(user_id):
    with open(json_file, 'r') as file:
        check_config = json.load(file)

    if "SECRET_KEY" in check_config:
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=48)
        }

        token = jwt.encode(payload, check_config.get("SECRET_KEY"), algorithm='HS256')
        return token
    else:
        create_key()
        return generate_jwt(user_id)


def key_validation(jwt_key1, jwt_key2):

    with open(json_file, 'r') as file:
        check_config = json.load(file)
        key = check_config.get("SECRET_KEY")

    try:
        decode_1 = jwt.decode(jwt_key1, key, algorithms=["HS256"])
        decode_2 = jwt.decode(jwt_key2, key, algorithms=["HS256"])

        if decode_1 == decode_2:
            return 1
        
        return 0
    
    except jwt.ExpiredSignatureError:
        
        expired_decode_1 = jwt.decode(jwt_key1, key, algorithms=["HS256"])
        expired_decode_2 = jwt.decode(jwt_key2, key, algorithms=["HS256"])

        if expired_decode_1 == expired_decode_2:
            return 2
        else:
            return 3
    
# 0 - rejecter, 1 - passed, 2 - expired


