import base64
import pickle

from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer
from goods.models import SKU


class CartAPIView(APIView):

    def perform_authentication(self, request):

        pass

    def post(self, request):

        data = request.data
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except Exception as e:
            user = None

        if user is not None and user.is_authenticated:

            redis_conn = get_redis_connection('cart')

            pl = redis_conn.pipeline()
            pl.hincrby('cart_%s' % user.id, sku_id,count)

            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            pl.execute()

            return Response(serializer.data)

        else:

            cookie_str = request.COOKIES.get('cart')
            if cookie_str is not None:
                decode = base64.b64decode(cookie_str)
                cookie_str = pickle.loads(decode)
            else:
                cookie_str = {}

            if sku_id in cookie_str.keys():

                origin_count = cookie_str[sku_id]['count']
                count += origin_count
            cookie_str[sku_id] = {
                'count': count,
                'selected': selected
            }

            dumps = pickle.dumps(cookie_str)
            encode = base64.b64encode(dumps)
            value = encode.decode()

            response = Response(serializer.data)
            response.set_cookie('cart', value)

            return response

    def get(self, request):

        try:
            user = request.user
        except Exception as e:
            user = None

        if user is not None and user.is_authenticated:

            redis_conn = get_redis_connection('cart')

            redis_ids_count = redis_conn.hgetall('cart_%s' % user.id)
            redis_selected_ids = redis_conn.smembers('cart_selected_%s' % user.id)

            cookie_cart = {}
            for sku_id, count in redis_ids_count.items():
                cookie_cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected_ids
                }

        else:
            cookie_str = request.COOKIES.get('cart')
            if cookie_str is not None:
                decode = base64.b64decode(cookie_str)
                cookie_cart = pickle.loads(decode)
            else:
                cookie_cart = {}

        ids = cookie_cart.keys()
        skus = SKU.objects.filter(pk__in=ids)
        for sku in skus:
            sku.count = cookie_cart[sku.id]['count']
            sku.selected = cookie_cart[sku.id]['selected']

        serializer = CartSKUSerializer(skus, many=True)

        return Response(serializer.data)

    def put(self, request):

        data = request.data
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except Exception as e:
            user = None

        if user is not None and user.is_authenticated:

            redis_conn = get_redis_connection('cart')
            redis_conn.hset('cart_%s' % user.id, sku_id, count)

            if selected:
                redis_conn.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                redis_conn.srem('cart_selected_%s' % user.id, sku_id)

            return Response(serializer.data)

        else:
            cookie_str = request.COOKIES.get('cart')

            if cookie_str is not None:
                decode = base64.b64decode(cookie_str)
                cookie_cart = pickle.loads(decode)
            else:
                cookie_cart = {}

            for sku_id in cookie_cart:
                cookie_cart[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            value = base64.b64encode(pickle.dumps(cookie_cart)).decode()

            response = Response(serializer.data)
            response.set_cookie('cart', value)

            return response

    def delete(self, request):

        data = request.data
        serializer = CartDeleteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')

        try:
            user = request.user
        except Exception as e:
            user = None

        if user is not None and user.is_authenticated:

            redis_conn = get_redis_connection('cart')
            redis_conn.hdel('cart_%s' % user.id, sku_id)
            redis_conn.srem('cart_selected_%s' % user.id, sku_id)

            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            cookie_str = request.COOKIES.get('cart')

            if cookie_str is not None:
                cookie_cart = pickle.loads(base64.b64decode(cookie_str))
            else:
                cookie_cart = {}

            if sku_id in cookie_cart:
                del cookie_cart[sku_id]

            value = base64.b64encode(pickle.dumps(cookie_cart)).decode()

            response = Response(status=status.HTTP_204_NO_CONTENT)
            response.set_cookie('cart', value)

            return response





