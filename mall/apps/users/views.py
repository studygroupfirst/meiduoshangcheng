from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework_jwt.views import ObtainJSONWebToken

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from users.models import User, Address
from users.serializers import RegisterCreateSerializer, EmailSerializer, AddAddressSerializer, AddressTitleSerializer, \
    SKUSerializer
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import UserDetailSerializer
# Create your views here.
import requests

class RejisterUsernameCountAPIView(APIView):

    def get(self, request, username):

        count = User.objects.filter(username=username).count()

        context = {
            "count": count,
            "username": username
        }

        return Response(context)


class RejisterPhoneCountAPIView(APIView):

    def get(self, request, mobile):

        count = User.objects.filter(mobile=mobile).count()

        context = {
            "count": count,
            "phone": mobile
        }

        return Response(context)


class RejisterCreateUser(CreateAPIView):

    serializer_class = RegisterCreateSerializer


class UserDetailView(RetrieveAPIView):
    """
    获取登录用户的信息
    GET /users/
    既然是登录用户,我们就要用到权限管理
    在类视图对象中也保存了请求对象request
    request对象的user属性是通过认证检验之后的请求用户对象
    """
    permission_classes = [IsAuthenticated]

    serializer_class = UserDetailSerializer

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    """
    保存邮箱
    PUT /users/emails/
    """

    permission_classes = [IsAuthenticated]

    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


class VerificationEmailView(APIView):
    """
    验证激活邮箱
    GET /users/emails/verification/?token=xxxx

    思路:
    获取token,并判断
    获取 token中的idf
    查询用户,并判断是否存在
    修改状态
    返回响应
    """

    def get(self,request):
        # 获取token, 并判断
        token = request.query_params.get('token')
        if not token:
            return Response({'message':'缺少token'},status=status.HTTP_400_BAD_REQUEST)
        # 获取token中的id,email
        # 查询用户, 并判断是否存在
        user = User.check_verify_email_token(token)
        if user is None:
            return Response({'message':'链接无效'},status=status.HTTP_400_BAD_REQUEST)
        else:
            # 修改状态
            user.email_active = True
            user.save()
            # 返回响应
            return Response({'message': 'ok'})


class AddAdddress(mixins.ListModelMixin,mixins.CreateModelMixin,mixins.UpdateModelMixin,GenericViewSet):

    serializer_class = AddAddressSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        """
        保存用户地址数据
        """
        count = request.user.addresses.count()
        if count >= 20:
            return Response({'message': '保存地址数量已经达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        获取用户地址列表
        """
        # 获取所有地址
        queryset = self.get_queryset()
        # 创建序列化器
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        # 响应
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None, address_id=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None, address_id=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from .serializers import  AddUserBrowsingHistorySerializer
from rest_framework.permissions import IsAuthenticated


class UserBrowsingHistoryView(mixins.CreateModelMixin, GenericAPIView):
    """
    用户浏览历史记录
    POST /users/browerhistories/
    GET  /users/browerhistories/
    数据只需要保存到redis中
    """
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """保存"""
        return self.create(request)

    def get(self,request):
        """获取"""
        #获取用户信息
        user_id = request.user.id
        #连接redis
        redis_conn =  get_redis_connection('history')
        #获取数据
        history_sku_ids = redis_conn.lrange('history_%s'%user_id,0,5)
        skus = []
        for sku_id in history_sku_ids:
            sku = SKU.objects.get(pk=sku_id)
            skus.append(sku)
        #序列化
        serializer = SKUSerializer(skus,many=True)
        return Response(serializer.data)


class MergeLoginAPIView(ObtainJSONWebToken):

    def post(self, request, *args, **kwargs):
        # 调用jwt扩展的方法，对用户登录的数据进行验证
        response = super().post(request)

        # 如果用户登录成功，进行购物车数据合并
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 表示用户登录成功
            user = serializer.validated_data.get("user")
            # 合并购物车
            #merge_cart_cookie_to_redis(request, user, response)
            responses = merge_cart_cookie_to_redis(request, user, response)

        return responses


# 修改密码
class UserPassWordView(APIView):
        def put(self,request, user_pwd):

            data = request.data
            user = User.objects.get(id=user_pwd)
            # 查看旧密码正确性
            if not user.check_password(data['old_password']):
                raise Exception('原密码错误')
            # 判断新密码是否一致
            new_pwd = data['password']
            new_cpwd = data['password2']
            if new_pwd != new_cpwd:
                raise Response('{"status":"fail", "msg":"密码不一致"}', content_type="application/json")
                # 密码加密保存
            user.set_password(new_pwd)
            user.save()
            return Response({'message':'保存成功'})





from libs.captcha.captcha import captcha
import re,random
import json
from libs.yuntongxun.sms import CCP
from django.http import HttpResponse
from users.utils import forget_verify_url,forget_token



# ---------------------------------忘记密码--------------------------------
class ForgetImageAPIView(APIView):

    def get(self,request,image_code_id):
        # 1.接收image_code_id
        # 2.生成图片和验证码
        text,image = captcha.generate_captcha()

        # 3.把验证码保存到redis中
        #3.1连接redis
        redis_conn = get_redis_connection('code')
        #3.2设置图片
        redis_conn.setex('forget_img_'+image_code_id,600,text)
        # 4.返回图片相应

        return HttpResponse(image,content_type='image/jpeg')





class ForgetUsernameAPIView(APIView):

    def get(self,request,username):
        # 判断用户是否注册
        # 查询用户名的数量
        # itcast 0   没有注册
        # itcast 1   有注册
        try:
            if re.match(r'1[3-9]\d{9}',username):
                # 手机号
                user = User.objects.get(mobile=username)

            else:
                # 用户名
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
            return Response(status=status.HTTP_404_NOT_FOUND)

        # user = User.objects.filter(username=username).count()
        mobile = user.mobile
        # 判断用户名是否存在
        if user == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 判断验证码是否正确
        # 获取到用户输入的验证码
        code_text = request.query_params['text']
        # 获取到image_code_id
        image_code_id = request.query_params['image_code_id']

        redis_conn = get_redis_connection('code')
        # 3.2设置图片
        get_redis_code = redis_conn.get('forget_img_' + image_code_id)

        if code_text.lower() != get_redis_code.decode().lower():
            return Response(status=status.HTTP_400_BAD_REQUEST)


        # 加密token
        token = forget_verify_url(mobile)

        start = mobile[:3]
        end = mobile[-4:]
        mobile = ''.join([start,'*****',end])

        json_data = json.dumps({
            "mobile":mobile,
            "access_token":token
            })
        # 返回数据
        return Response(json_data)


# 忘记密码实现短信发送
class ForgetSMS(APIView):
    def get(self,request):
        # 获取token值
        # 1. 接收token信息
        token = request.query_params.get('access_token')
        if token is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 2. 对token进行解析
        mobile = forget_token(token)

        if mobile is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 3. 解析获取user_id之后,进行查询
        user = User.objects.get(mobile=mobile)
        user_id = user.id

        user_token = forget_verify_url(user_id)

        # # 4. 修改状态
        # user.save()
        # 5. 返回相应
        json_data = json.dumps({
            "user_id": user_id,
            "access_token": user_token
        })

        # 3.生成短信
        sms_code = '%06d' % random.randint(0,999999)
        # 4.将短信保存在redis中
        redis_conn = get_redis_connection('code')

        redis_conn.setex('forget_sms_' + mobile,5 * 60,sms_code)
        # 5.使用云通讯发送短信
        CCP().send_template_sms(mobile,[sms_code,5],1)


        # 返回数据
        return Response(json_data)


# 短信验证码校验与手机号
class Forget_SMS_verification_code(APIView):
    '''
    判断短信验证码是否一致

    '''

    def get(self,request,username):

        try:
            if re.match(r'1[3-9]\d{9}',username):
                # 手机号
                user = User.objects.get(mobile=username)

            else:
                # 用户名
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 数据库中获取号码
        mobile = user.mobile
        user_id = user.id

        # 从数据库中获取到加密后的密码
        password = user.password



        # 获取到前端发送过来的短信验证码
        sms_code = request.query_params['sms_code']

        # 获取到redis数据库中的短信验证码
        redis_conn = get_redis_connection('code')
        get_redis_code = redis_conn.get('forget_sms_' + mobile)

        # 对短信验证码进行校验
        if sms_code != get_redis_code.decode():
            return Response(status=status.HTTP_400_BAD_REQUEST)


        # 4.将user_id保存在redis中
        redis_conn.setex('forget_id_' + str(user_id),1 * 60,user_id)

        # 向前端返回旧密码
        # 5. 返回相应
        json_data = json.dumps({
            "access_token": password,
            "user_id":user_id,
        })

        return Response(json_data)


# -------------------------重置密码-------------------------
class Reset_password(APIView):
    def post(self,request,user_id):

        # 从redis中取出user_id
        redis_conn = get_redis_connection('code')
        redis_user_id = redis_conn.get('forget_id_'+ str(user_id))

        # 如果redis_user_id 值为空
        if redis_user_id == None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if redis_user_id.decode() != user_id:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 1两次密码需要一致
        password = request.data['password']
        password2 = request.data['password2']
        token = request.data['access_token']

        if password != password2:
            raise Response({"message":"密码不一致"})

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 2. 验证码用户密码
        if user is not None and user.check_password(token):
            return Response(status=status.HTTP_404_NOT_FOUND)



        # 修改密码，调用django自带的加密算法，对密码进行加密存储
        user.set_password(password)
        user.save()
        # 用户入库之后,我们生成token
        from rest_framework_jwt.settings import api_settings

        # 4.1 需要使用 jwt的2个方法
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        # 4.2 让payload(载荷 )盛放一些用户信息
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token = token

        return Response(status=status.HTTP_200_OK)

