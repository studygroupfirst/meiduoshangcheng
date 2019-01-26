from django.shortcuts import render

# Create your views here.

from rest_framework.response import Response
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ
from mall import settings
from rest_framework import status

from oauth.models import OAuthQQUser, OAuthWeiboUser
from oauth.serializers import OAuthQQUserSerializer, WeiboOauthSerializers
from oauth.utils import check_save_user_token, generic_access_token

"""
当用户点击qq按钮的时候,会发送一个请求,
我们后端返回给它一个 url (URL是根据文档来拼接出来的)
GET     /oauth/qq/statues/

"""

class OAuthQQURLAPIView(APIView):

    def get(self,request):
        # auth_url = 'https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101474184&redirect_uri=http://www.meiduo.site:8080/oauth_callback.html&state=test'
        # 成功之后 回调到哪里去
        # next表示从哪个页面进入到的登录页面，将来登录成功后，就自动回到那个页面
        state = request.query_params.get('state')
        if not state:
            state = '/'

        # 1.创建oauthqq的实例对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=state)

        # 2. 获取跳转的url
        auth_url = oauth.get_qq_url()

        return Response({'auth_url': auth_url})

"""
1. 用户同意授权登陆,这个时候 会返回一个 code
2. 我们用code 换取 token
3. 有了token,我们再获取 openid
"""

"""
1.分析需求 (到底要干什么)
2.把需要做的事情写下来(把思路梳理清楚)
3.路由和请求方式
4.确定视图
5.按照步骤实现功能


前端会接收到 用户同意之后的, code 前端应该将这个code 发送给后端

1. 接收这个数据
2. 用code换token
3. 用token换openid

GET     /oauth/qq/users/?code=xxxxxx
"""

class OAuthQQUserAPIView(APIView):

    def get(self, request):
        # 1. 接收这个数据
        params = request.query_params
        code = params.get('code')
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 2. 用code换token
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        token = oauth.get_access_token(code)
        # 3. 用token换openid
        openid = oauth.get_open_id(token)

        # openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份
        # 获取的openid有两种情况:
        # 1. 用户之前绑定过
        # 2. 用户之前没有绑定过

        # 根据openid查询数据
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 不存在

            # openid 很重要 ,所以我们需要对openid进行一个处理
            # 绑定也应该有一个时效

            # s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
            #
            # # 2. 组织数据
            # data = {
            #     'openid': openid
            # }
            #
            # # 3. 让序列化器对数据进行处理
            # token = s.dumps(data)

            token = check_save_user_token(openid)

            return Response({'access_token': token})

        else:
            # 存在,应该让用户登陆

            from rest_framework_jwt.settings import api_settings

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(qquser.user)
            token = jwt_encode_handler(payload)

            return Response({
                'token': token,
                'username': qquser.user.username,
                'user_id': qquser.user.id
            })

            # finally:
            #     pass


    """
    当用户点击绑定的时候 ,我们需要将 手机号,密码,短信验证码和加密的openid 传递过来

    1. 接收数据
    2. 对数据进行校验
    3. 保存数据
    4. 返回相应


    POST    /oauth/qq/users/

    """
    def post(self,request):
        # 1. 接收数据
        data = request.data
        # 2. 对数据进行校验
        serializer = OAuthQQUserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3. 保存数据
        qquser = serializer.save()
        # 4. 返回相应, 应该有token数据

        from rest_framework_jwt.settings import api_settings

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(qquser.user)
        token = jwt_encode_handler(payload)

        return Response({
            'token': token,
            'username': qquser.user.username,
            'user_id': qquser.user.id
        })



#使用itsdangerous对openid进行加密处理
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mall import settings
from itsdangerous import BadSignature,SignatureExpired

#1. 创建一个序列化器
#  secret_key,   秘钥
# expires_in=None  过期时间 单位是:秒
s = Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)

#2. 组织数据
data = {
    'openid':'1234567890'
}

#3. 让序列化器对数据进行处理
token = s.dumps(data)

#eyJpYXQiOjE1NDcwODkwODAsImV4cCI6MTU0NzA5MjY4MCwiYWxnIjoiSFMyNTYifQ.
# eyJvcGVuaWQiOiIxMjM0NTY3ODkwIn0.
# OGyy5mJ5s4fNvH9gmREyJoC8raeEQPU40LpThD-lIl8


# 4. 获取数据对数据进行 解密
s.loads(token)





s = Serializer(secret_key=settings.SECRET_KEY,expires_in=1)

#2. 组织数据
data = {
    'openid':'1234567890'
}

#3. 让序列化器对数据进行处理
token = s.dumps(data)



# 1. 通过查询字符串
# 2. 获取微博登录网页
from .WeiboTool import OAuthWeibo
class WeiboAuthURLLView(APIView):
    """定义微博第三方登录的视图类"""

    def get(self, request):
        """
        获取微博登录的链接
        oauth/weibo/authorization/?next=/
        :param request:
        :return:
        """
        # 1.通过查询字符串
        state = request.query_params.get('state')
        if not state:
            state = '/'

        # 获取微博登录网页
        oauth = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                           client_secret=settings.WEIBO_CLIENT_SECRET,
                           redirect_uri=settings.WEIBO_REDIRECT_URI,
                           state=state)
        login_url = oauth.get_weibo_url()
        return Response({"login_url": login_url})
        # return Response({'login_url':'http://www.baidu.com'})



from rest_framework_jwt.settings import api_settings
from oauth.serializers import  WeiboOauthSerializers

class WeiboOauthView(APIView):
    """验证微博登录"""

    def get(self, request):
        """
        第三方登录检查
        oauth/sina/user/
        ?code=0e67548e9e075577630cc983ff79fa6a
        :param request:
        :return:
        pass
        """
        # 1.获取code值
        code = request.query_params.get("code")

        # 2.检查参数
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 3.获取token值
        # next = "/"
        weiboauth = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                               client_secret=settings.WEIBO_CLIENT_SECRET,
                               redirect_uri=settings.WEIBO_REDIRECT_URI,
                               state=next)
        access_token = weiboauth.get_access_token(code=code)
        # 5.判断是否绑定过美多账号
        try:
            weibo_user = OAuthWeiboUser.objects.get(access_token=access_token)
        except:
            # 6.未绑定,进入绑定页面,完成绑定
            token = generic_access_token(access_token)

            return Response({'access_token': token})
        else:
            # 7.绑定过,则登录成功
            # 生成jwt-token值
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(weibo_user.user)  # 生成载荷部分
            token = jwt_encode_handler(payload)  # 生成token

            return Response({
                    'token': token,
                    'username': weibo_user.user.username,
                    'user_id': weibo_user.user.id
                })


    def post(self, request):
        """
        微博用户未绑定,绑定微博用户
        :return:
        """
        # 1. 接收数据
        data = request.data
        # 2. 对数据进行校验
        serializer = WeiboOauthSerializers(data=data)
        serializer.is_valid(raise_exception=True)
        # 保存序列化器
        weibo_user = serializer.save()

        from rest_framework_jwt.settings import api_settings

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(weibo_user.user)
        token = jwt_encode_handler(payload)

        data = {
            'token': token,
            'username': weibo_user.user.username,
            'user_id': weibo_user.user.id
        }
        return Response(data)

