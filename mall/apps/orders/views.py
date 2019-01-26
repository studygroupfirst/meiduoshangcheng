from decimal import Decimal


# Create your views here.
from django_redis import get_redis_connection
from rest_framework import mixins
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from goods.models import SKU
from orders.models import OrderInfo
from orders.serializers import OrderPlaceSerializer, OrderSerializer, UserInfoOrderSerializer
from orders.models import OrderGoods
from orders.serializers import ScoreOrderSerializer, CommentSerializer


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


class OrderAPIViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, GenericViewSet):

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):

        if self.action == 'create':

            return OrderSerializer

        if self.action == 'list':

            return UserInfoOrderSerializer

    def get_queryset(self):

        if self.action == 'list':

            return OrderInfo.objects.filter(user=self.request.user).all().order_by('-create_time')


# class InfoOrderAPIView(ListAPIView):
#
#     serializer_class =

    # def get(self, request):
    #
    #     user = request.user
    #
    #     try:
    #         orders = OrderInfo.objects.filter(user=user).all().order_by('-create_time')
    #         count = OrderInfo.objects.filter(user=user).count()
    #     except OrderInfo.DoesNotExist:
    #         return Response(status=status.HTTP_204_NO_CONTENT)
    #
    #     paginator = Paginator(orders, 5)
    #     page = request.GET.get('page')
    #     try:
    #         orders = paginator.page(page)
    #     except PageNotAnInteger:
    #         # 如果page不是整数，则展示第1页
    #         orders = paginator.page(1)
    #     except EmptyPage:
    #         # 如果page超过范围，则展示最后一页
    #         orders = paginator.page(paginator.num_pages)
    #
    #     serializer = UserInfoOrderSerializer(orders, many=True)
    #
    #     data = {
    #         'count': count,
    #         'results': serializer.data
    #     }
    #
    #     return Response(data)


"""
data{
    count, resutls,
}
"""


class ScoreOrderView(APIView):
    def get(self,request,order_id):
        skus =OrderGoods.objects.filter(order_id__exact=order_id)
        serializers =  ScoreOrderSerializer(skus,many=True)
        return Response(serializers.data)

class CommentView(APIView):
    def post(self,request,order_id):
        data = request.data
        del data['order']
        data1 = data
        skus = OrderGoods.objects.filter(order_id__exact=order_id,sku_id__exact=data['sku'])
        for sku in skus:
            serilaizers = CommentSerializer(sku,data1)
            serilaizers.is_valid()
            serilaizers.save()
            return Response(serilaizers.data)
