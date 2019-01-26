from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token

from . import views

router = DefaultRouter()
router.register(r'addresses', views.AddAdddress, base_name='address')

urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.RejisterUsernameCountAPIView.as_view(), name='usernamecount'),
    url(r'^phones/(?P<mobile>1[345789]\d{9})/count/$', views.RejisterPhoneCountAPIView.as_view(), name='phonecount'),
    url(r'^$', views.RejisterCreateUser.as_view(), name='rejisteruser'),
    url(r'^auths/', views.MergeLoginAPIView.as_view()),
    url(r'^infos/$', views.UserDetailView.as_view(), name='detail'),
    url(r'^emails/$',views.EmailView.as_view(),name='send_mail'),
    url(r'emails/verification/', views.VerificationEmailView.as_view()),
    # url(r'^', include(router.urls)),
    url(r'^browerhistories/$', views.UserBrowsingHistoryView.as_view(), name='history'),

    # /users/'+vm.user_id+'/password/',
    url(r'^(?P<user_pwd>\d+)/password/$',views.UserPassWordView.as_view()),

    # 忘记密码
    url(r'image_codes/(?P<image_code_id>.+)/$',views.ForgetImageAPIView.as_view(),name='imagecode'),
    url(r'accounts/(?P<username>.+)/sms/token/',views.ForgetUsernameAPIView.as_view()),
    # 短信发送
    url(r'sms_codes/',views.ForgetSMS.as_view()),
    url(r'accounts/(?P<username>.+)/password/token/',views.Forget_SMS_verification_code.as_view()),
    # 重置密码
    url(r'(?P<user_id>.+)/password/',views.Reset_password.as_view())

]
urlpatterns += router.urls


