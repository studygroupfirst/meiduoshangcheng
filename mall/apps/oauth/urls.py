#coding:utf8
from django.conf.urls import url
from . import views

urlpatterns = [

    #/oauth/qq/statues/
    url(r'^qq/statues/$',views.OAuthQQURLAPIView.as_view()),
    #oauth/qq/users/
    url(r'^qq/users/$',views.OAuthQQUserAPIView.as_view()),
    #/oauth/weibo/authorization/?next=
    url(r'^weibo/authorization/$',views.WeiboAuthURLLView.as_view()),
    # /oauth/sina/user/
    url(r'^sina/user/$',views.WeiboOauthView.as_view()),



]