from django.conf.urls import url
from . import views

urlpatterns = [
    #/orders/places/
    url(r'^places/$',views.PlaceOrderAPIView.as_view(),name='placeorder'),
    url(r'^$',views.OrderAPIView.as_view(),name='order'),
    url(r'^(?P<order_id>\d+)/uncommentgoods/$', views.ScoreOrderView.as_view()),
    url(r'^(?P<order_id>\d+)/comments/$', views.CommentView.as_view()),

]