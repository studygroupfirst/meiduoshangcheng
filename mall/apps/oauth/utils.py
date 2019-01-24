from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from mall import settings


def generate_save_user_token(openid):

    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    data = {'openid': openid}
    token = serializer.dumps(data)
    return token.decode()


def check_save_user_token(access_token):
    serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
    try:
        data = serializer.loads(access_token)
    except BadData:
        return None