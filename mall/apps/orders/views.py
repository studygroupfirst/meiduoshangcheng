from decimal import Decimal
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU
from orders.serializers import OrderPlaceSerializer, OrderSerializer


class PlaceOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
        redis_conn = get_redis_connection('cart')

        redis_ids_count = redis_conn.hgetall('cart_%s' % user.id)
        selected_ids = redis_conn.smembers('cart_selected_%s' % user.id)

        selected_carts = {}
        for id in selected_ids:
            selected_carts[int(id)] = int(redis_ids_count[id])

        ids = selected_carts.keys()
        skus = SKU.objects.filter(pk__in=ids)
        for sku in skus:
            sku.count = selected_carts[sku.id]

        freight = Decimal('10.00')

        serializer = OrderPlaceSerializer({
            'freight': freight,
            'skus': skus
        })

        return Response(serializer.data)


class OrderAPIView(CreateAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = OrderSerializer