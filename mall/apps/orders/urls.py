from django.conf.urls import url

from orders.views import OrderAPIViewSet
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'', OrderAPIViewSet, base_name='order')



urlpatterns = [
    #/orders/places/
    url(r'^places/$',views.PlaceOrderAPIView.as_view(),name='placeorder'),

    # url(r'^$',views.OrderAPIView.as_view(),name='order'),
    # url(r'^info/$', views.InfoOrderAPIView.as_view())

    url(r'^(?P<order_id>\d+)/uncommentgoods/$', views.ScoreOrderView.as_view()),
    url(r'^(?P<order_id>\d+)/comments/$', views.CommentView.as_view()),
    url(r'^(?P<sku_id>\d+)/commentlists/$', views.CommentListView.as_view()),

]
urlpatterns += router.urls