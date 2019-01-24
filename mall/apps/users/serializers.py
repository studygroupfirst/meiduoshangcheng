import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import User, Address
from celery_tasks.email.tasks import send_verify_mail


class RegisterCreateSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(label='校验密码', allow_null=False,    allow_blank=False,  write_only=True)
    sms_code = serializers.CharField(label='短信验证码', max_length=6,min_length=6,allow_null=False, allow_blank=False,  write_only=True)
    allow = serializers.CharField(label='是否同意协议',   allow_null=False,   allow_blank=False,  write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)

    class Meta:
        model = User
        fields = ['password', 'password2', 'sms_code', 'id', 'username', 'allow', 'mobile', 'token']
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate_mobile(self, value):

        if not re.match(r'^1[345789]\d{9}', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value

    def validate_allow(self, value):

        if not value:
            raise serializers.ValidationError('您未同意协议')
        return value

    def validate(self, attrs):

        password = attrs['password']
        password2 = attrs['password2']
        if password != password2:
            raise serializers.ValidationError('密码不一致')

        redis_conn = get_redis_connection('code')
        mobile = attrs['mobile']
        code = attrs['sms_code']
        redis_code = redis_conn.get('sms_' + mobile)
        if redis_code is None:
            raise serializers.ValidationError('验证码已过期')
        if code != redis_code.decode():
            raise serializers.ValidationError('验证码不正确')

        return attrs

    def create(self, validated_data):

        # 删除多余字段
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        user = super().create(validated_data)

        # 修改密码
        user.set_password(validated_data['password'])
        user.save()

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详细信息序列化器
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        email = validated_data['email']
        instance.email = validated_data['email']
        instance.save()
        # 发送激活邮件
        # 生成激活链接
        verify_url = instance.generate_verify_email_url()
        # 发送,注意调用delay方法

        send_verify_mail.delay(email, verify_url)
        return instance


class AddAddressSerializer(serializers.ModelSerializer):

    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = Address
        exclude = ['user', 'is_deleted', 'create_time', 'update_time']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ['title']


from goods.models import SKU
from django_redis import get_redis_connection


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览记录序列化器
    """
    sku_id = serializers.IntegerField(label='商品编号',min_value=1,required=True)

    def validate_sku_id(self,value):
        """
        检查商品是否存在
        """
        try:
            SKU.objects.get(pk=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value

    def create(self, validated_data):

        #获取用户信息
        user_id = self.context['request'].user.id
        #获取商品id
        sku_id = validated_data['sku_id']
        #连接redis
        redis_conn = get_redis_connection('history')
        #移除已经存在的本记录
        redis_conn.lrem('history_%s'%user_id,0,sku_id)
        #添加新的记录
        redis_conn.lpush('history_%s'%user_id,sku_id)
        #保存最多5条记录
        redis_conn.ltrim('history_%s'%user_id,0,4)
        return validated_data


class SKUSerializer(serializers.ModelSerializer):

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')