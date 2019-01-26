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

#序列化access_token的工具方法
def generic_access_token(access_token):

    # return openid

    #1.创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY,expires_in=60*60)
    #2. 对数据进行处理
    token = s.dumps({
        'access_token':access_token
    })
    #3.返回
    return token.decode()


#对加密的access_token进行处理
def weibo_access_token(access_token):

    #1. 创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=60 * 60)
    #2. 对数据进行 loads操作
    try:
        data = s.loads(access_token)
    except BadData:
        return None
    #3.返回 openid
    return data['access_token']