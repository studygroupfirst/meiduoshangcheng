from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadSignature
from mall import settings

# 忘记密码

def forget_verify_url(user_id):


    # 1. 创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)
    #3. 对数据加密
    token = s.dumps(user_id).decode()
    #4. 返回token
    return token

def forget_token(token):

    #1. 创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    #2. 解析数据
    try:
        result = s.loads(token)
    except BadSignature:
        return None

    #3.返回user_id
    return result

