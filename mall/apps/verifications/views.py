from random import randint

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from libs.yuntongxun.sms import CCP
from verifications.serializers import RegisterSMSCodeSerializer
from . import constants
# Create your views here.
from django_redis import get_redis_connection
from rest_framework.views import APIView

from libs.captcha.captcha import captcha


class RegisterImageCodeView(APIView):

    def get(self, request, image_code_id):

        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection('code')

        redis_conn.setex('image_' + image_code_id, constants.IMAGE_CODE_EXPIRE_TIME, text)

        return HttpResponse(image, content_type='image/jpeg')


class RegisterSMSCodeView(GenericAPIView):

    serializer_class = RegisterSMSCodeSerializer

    def get(self, request, mobile):

        serializer = self.get_serializer(data=request.query_params)

        serializer.is_valid(raise_exception=True)

        redis_conn = get_redis_connection('code')

        if redis_conn.get('sms_flag_' + mobile):
            return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)

        sms_code = '%06d' % randint(0, 999999)

        redis_conn.setex('sms_' + mobile, constants.SMS_CODE_EXPIRE_TIME, sms_code)

        redis_conn.setex('sms_flag_' + mobile, constants.SMS_CODE_EXPIRE_TIME, 1)

        from celery_tasks.sms.tasks import send_sms_code

        send_sms_code.delay(mobile, sms_code)

        return Response({'message': 'ok'})