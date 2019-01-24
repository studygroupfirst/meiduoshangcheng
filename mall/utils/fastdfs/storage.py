from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from fdfs_client.client import Fdfs_client

from mall import settings


@deconstructible
class MyStorage(Storage):

    # def __init__(self, conf_path=None, ip=None):
    #     if not conf_path:
    #         self.conf = settings.FDFS_CLIENT_CONF
    #     if not ip:
    #         self.ip = settings.FDFS_URL
    #
    # def _open(self, name, mode='rb'):
    #     pass
    #
    # def _save(self, name, content, max_length=None):
    #
    #     fdfs_client = Fdfs_client(self.conf)
    #     file_data = content.read()
    #
    #     result = fdfs_client.upload_by_buffer(file_data)
    #
    #     if result.get('Status') == 'Upload successed':
    #         file_id = result.get('Remote file_id')
    #     else:
    #         raise Exception('上传失败')
    #     return file_id
    #     # 创建client对象
    #     # 获取文件
    #     # 上传
    #     # 判断上传结果
    #         # 返回上传的字符串
    #
    # def exists(self, name):
    #     # 判断文件是否存在，FastDFS可以自行解决文件的重名问题
    #     # 所以此处返回False，告诉Django上传的都是新文件
    #     return False
    #
    # def url(self, name):
    #     # 返回文件的完整URL路径
    #     return self.ip + name

    def __init__(self, config_path=None, config_url=None):
        if not config_path:
            fdfs_config = settings.FDFS_CLIENT_CONF
            self.fdfs_config = fdfs_config
        if not config_url:
            fdfs_url = settings.FDFS_URL
            self.fdfs_url = fdfs_url

    # 3.您的存储类必须实现_open()和_save() 方法
    # 以及适用于您的存储类的任何其他方法

    # open 打开
    # 因为我们的 Fdfs 是通过http来获取图片的,所以不需要打开方法
    def _open(self, name, mode='rb'):
        pass

    # save  保存
    def _save(self, name, content, max_length=None):

        # name,              文件的名字 我们不能通过名字 获取文件的完整路径
        # content,          content 内容 就是上传的内容 二进制
        # max_length=None

        # 1. 创建Fdfs的客户端,让客户端加载配置文件
        # client = Fdfs_client('utils/fastdfs/client.conf')
        # client = Fdfs_client(settings.FDFS_CLIENT_CONF)
        client = Fdfs_client(self.fdfs_config)
        # 2. 获取上传的文件
        # content.read() 就是读取 content的内容
        # 读取的是 二进制
        file_data = content.read()
        # 3. 上传图片,并获取 返回内容
        # upload_by_buffer 上传二进制流
        result = client.upload_by_buffer(file_data)
        # 4. 根据返回内容 获取 remote file_id
        """
        {'Group name': 'group1',
        'Local file name': '/home/python/Desktop/images/1.jpg',
         'Status': 'Upload successed.',
         'Uploaded size': '183.00KB',
          'Remote file_id': 'group1/M00/00/02/wKjllFw9M1mAU7RqAALd0X8OZb4393.jpg',
           'Storage IP': '192.168.229.148'}


        """

        if result.get('Status') == 'Upload successed.':
            # 说明上传成功
            file_id = result.get('Remote file_id')
        else:
            raise Exception('上传失败')

        # 需要把file_id 返回回去
        return file_id






        # class Person(object):
        #
        #
        #     def __int__(self,name=None):
        #         if not name:
        #             name =
        #         pass
        #
        # # p = Person()
        #
        # p = Person()

    # exists 存在
    # Fdfs 做了重名的处理 我们只需要上传就可以
    def exists(self, name):
        return False

    def url(self, name):

        # 默认调用 storage的 url方法 会返回 name(file_id)
        # group1/M00/00/02/wKjllFw9P_eAWHEgAALd0X8OZb4197.jpg
        # 实际我们访问图片的时候 是通过 http://ip:port/ + name(file_id)

        # return  'http://192.168.229.148:8888/' + name
        # return  settings.FDFS_URL + name
        return self.fdfs_url + name
