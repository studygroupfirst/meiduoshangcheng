from django.conf.urls import url

from orders.views import OrderAPIViewSet
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'', OrderAPIViewSet, base_name='order')



urlpatterns = [
    #/orders/places/
    url(r'^places/$',views.PlaceOrderAPIView.as_view(),name='placeorder'),
<<<<<<< HEAD
    # url(r'^$',views.OrderAPIView.as_view(),name='order'),
    # url(r'^info/$', views.InfoOrderAPIView.as_view())
]
=======
    url(r'^(?P<order_id>\d+)/uncommentgoods/$', views.ScoreOrderView.as_view()),
    url(r'^(?P<order_id>\d+)/comments/$', views.CommentView.as_view()),
>>>>>>> 621091304585efefc60e9bd0f5bb3f33045bb9c8

urlpatterns += router.urls