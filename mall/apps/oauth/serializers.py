
from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.utils import generic_access_token, weibo_access_token
from users.models import User
from .models import OAuthQQUser, OAuthWeiboUser

# serializers.Serializer
# serializers.ModelSerializer

"""
手机号,密码,短信验证码和加密的openid 这些数据进行校验

校验没有问题 保存数据的时候 是保存的 user 和openid

"""
class OAuthQQUserSerializer(serializers.Serializer):
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    # def validate(self, data):
    def validate(self, attrs):
        # 1. 需要对加密的openid进行处理
        access_token = attrs.get('access_token')
        # 1.1 利用封装对openid进行解密
        openid = generic_access_token(access_token)

        if openid is None:
            raise serializers.ValidationError('openid错误')

        # 我们通过attrs来传递数据
        attrs['openid'] = openid

        # 2. 需要对短信进行验证
        # 2.1 获取用户提交的
        mobile = attrs.get('mobile')
        sms_code = attrs['sms_code']
        # 2.2 获取 redis
        redis_conn = get_redis_connection('code')

        redis_code = redis_conn.get('sms_' + mobile)

        if redis_code is None:
            raise serializers.ValidationError('短信验证码已过期')

        # 最好删除短信
        redis_conn.delete('sms_' + mobile)
        # 2.3 比对
        if redis_code.decode() != sms_code:
            raise serializers.ValidationError('验证码不一致')

        # 3. 需要对手机号进行判断
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 说明没有注册过
            # 创建用户
            # User.objects.create()
            user = None
        else:
            # 说明注册过,
            # 注册过需要验证密码
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError('密码不正确')

            attrs['user'] = user

        return attrs

 # request.data --> 序列化器(data=xxx)
    # data --> attrs -->validated_data
    def create(self, validated_data):

        user = validated_data.get('user')

        if user is None:
            #创建user
            user = User.objects.create(
                mobile=validated_data.get('mobile'),
                username=validated_data.get('mobile'),
                password=validated_data.get('password')
            )

            #对password进行加密
            user.set_password(validated_data['password'])
            user.save()

        qquser = OAuthQQUser.objects.create(
            user=user,
            openid=validated_data.get('openid')
        )


        return qquser


from rest_framework_jwt.settings import api_settings
import re
class WeiboOauthSerializers(serializers.Serializer):
    """微博验证序列化器"""
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, attrs):
        """
        验证access_token
        :param attrs:
        :return:
        """
        # 1. 需要对加密的access_token进行处理
        access_token = attrs.get('access_token')
        access_token = weibo_access_token(access_token)

        if access_token is None:
            raise serializers.ValidationError('access_token错误')
        # 通过attrs来传递数据
        attrs['access_token'] = access_token

        # 2. 需要对短信进行验证
        # 2.1 获取用户提交的
        mobile = attrs.get('mobile')
        sms_code = attrs['sms_code']
        # 2.2 获取 redis
        redis_conn = get_redis_connection('code')

        redis_code = redis_conn.get('sms_' + mobile)

        if redis_code is None:
            raise serializers.ValidationError('短信验证码已过期')

        # 最好删除短信
        redis_conn.delete('sms_' + mobile)
        # 2.3 比对
        if redis_code.decode() != sms_code:
            raise serializers.ValidationError('验证码不一致')

        # 3. 需要对手机号进行判断
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 说明没有注册过
            # 创建用户
            # User.objects.create()
            user = None
        else:
            # 说明注册过,
            # 注册过需要验证密码
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError('密码不正确')

            attrs['user'] = user

        return attrs

    def create(self, validated_data):
        """
        保存用户
        :param self:
        :param validated_data:
        :return:
        """
        # 判断用户
        user = validated_data.get('user')
        if user is None:
            # 创建用户
            user = User.objects.create_user(username=validated_data['mobile'],
                                        password=validated_data['password'],
                                        mobile=validated_data['mobile'])

            # 对password进行加密
            user.set_password(validated_data['password'])
            user.save()

        weibo_user = OAuthWeiboUser.objects.create(
            user=user,
            access_token=validated_data.get('access_token')
        )

        return weibo_user
