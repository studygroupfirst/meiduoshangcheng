# 由微博官方给出的文档,自定义微博登录SDK:
from django.conf import settings
from urllib.parse import urlencode
import requests
import json
class OAuthWeibo(object):
    """ 微博认证辅助工具类 """
    def __init__(self,client_id = None, client_secret = None, redirect_uri = None, state=None):
        self.client_id = client_id or settings.WEIBO_CLIENT_ID
        self.redirect_uri = redirect_uri or settings.WEIBO_REDIRECT_URI
        self.client_secret=client_secret or settings.WEIBO_CLIENT_SECRET
        self.state = state

    def get_weibo_url(self):
        """
        获取微博的验证页面链接
        :return:
        """
        data_dict = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state
        }
        # 构造微博登录链接
        # weibo_url =  'https://api.weibo.com/oauth2/authorize?response_type=code&client_id=%s&redirect_uri=%s' % (self.client_id,self.redirect_uri)
        weibo_url = 'https://api.weibo.com/oauth2/authorize?' + urlencode(data_dict)
        return weibo_url


    def get_access_token(self, code):
        """
        获取微博的accesstoken值
        https://api.weibo.com/oauth2/access_token
        ?client_id=YOUR_CLIENT_ID
        &client_secret=YOUR_CLIENT_SECRET
        &grant_type=authorization_code
        &redirect_uri=YOUR_REGISTERED_REDIRECT_URI
        &code=CODE

        :param code:
        :return:
        """
        # 构造参数
        data_dict = {
            "client_id":self.client_id,
            "client_secret":self.client_secret,
            "grant_type":"authorization_code",
            "redirect_uri":self.redirect_uri,
            "code":code
        }
        # 发送请求
        url = "https://api.weibo.com/oauth2/access_token?" + urlencode(data_dict)
        try:
            # url-字符串|data	-form提交的数据|json-json格式的数据
            response = requests.post(url)
            data = response.text
            data_dict = json.loads(data)
        except:
            raise Exception('微博请求失败')
            # 提取access_token
        access_token = data_dict.get('access_token', None)
        if not access_token:
            raise Exception('access_token获取失败')
        return access_token[0]