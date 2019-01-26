from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^qq/statues/$', views.QQAuthURLView.as_view()),
    url(r'^qq/users/$',views.QQAuthUserView.as_view()),

]