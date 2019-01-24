from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ReadOnlyModelViewSet

from areas.models import Area
from areas.serializers import AreaSerializer, SubsAreaSerialzier

from rest_framework_extensions.cache.mixins import ListCacheResponseMixin
from rest_framework_extensions.cache.mixins import RetrieveCacheResponseMixin
from rest_framework_extensions.cache.mixins import CacheResponseMixin


class AreaModelViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    pagination_class = None
    # queryset = Area.objects.all()   #所有信息
    # queryset = Area.objects.filter(parent=None)   #省的信息

    def get_queryset(self):

        # 我们可以根据 不同的业务逻辑返回不同的数据源
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    # serializer_class = AreaSerializer

    def get_serializer_class(self):

        # 我们可以根据 不同的业务逻辑返回不同的 序列化器
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubsAreaSerialzier