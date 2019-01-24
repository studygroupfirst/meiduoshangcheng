import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):

    cookie_str = request.COOKIES.get('cart')
    if cookie_str is not None:

        redis_conn = get_redis_connection('cart')
        redis_id_count = redis_conn.hgetall('cart_%s' % user.id)

        merge_cart = {}
        for sku_id, count in redis_id_count.items():
            merge_cart[int(sku_id)] = int(count)

        selected_ids = []
        decode = base64.b64decode(cookie_str)
        cookie_cart = pickle.loads(decode)

        for sku_id, count_selected_dict in cookie_cart.items():
            merge_cart[sku_id] = count_selected_dict['count']

            if count_selected_dict['selected']:
                selected_ids.append(sku_id)

        redis_conn.hmset('cart_%s' % user.id, merge_cart)
        if len(selected_ids) > 0:
            redis_conn.sadd('cart_selected_%s' % user.id, *selected_ids)

        response.delete_cookie('cart')

        return response

    return response