from alipay import AliPay
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mall import settings
from orders.models import OrderInfo
from pay.models import Payment


class PaymentView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):

        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        subject = '测试订单'

        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),  # total_amount是 decimal类型 要转换为 str
            subject=subject,
            return_url="http://www.meiduo.site:8080/pay_success.html",
            # notify_url="https://example.com/notify"  # 可选, 不填则使用默认notify url
        )
        # 5. 拼接url
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # 6. 返回url
        return Response({'alipay_url': alipay_url})


class PayStatuAPIView(APIView):

    def put(self, request):

        data = request.query_params.dict()
        signature = data.pop('sign')

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type='RSA2',
            debug=settings.ALIPAY_DEBUG
        )

        success = alipay.verify(data, signature)

        if success:
            out_trade_id = data.get('out_trade_no')
            trade_id = data.get('trade_no')

            Payment.objects.create(
                order_id=out_trade_id,
                trade_id=trade_id
            )

            OrderInfo.objects.filter(order_id=out_trade_id).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

            return Response(status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

