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
            # username = request.POST['username']

            data = request.data
            user = User.objects.get(id=user_pwd)
            # 查看就密码正确性
            if not user.check_password(data['old_password']):
                raise Exception('原密码错误')
            # 判断新密码是否一致
            if data['password'] != data['password2']:
                raise Response('{"status":"fail", "msg":"密码不一致"}', content_type="application/json")
                # 密码加密保存
            user.set_password(data['password'])
            user.save()
            return Response({'message':'保存成功'})



