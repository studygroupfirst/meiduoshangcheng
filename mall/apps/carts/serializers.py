from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):

    sku_id = serializers.IntegerField(label='物品id', required=True)
    count = serializers.IntegerField(label='数量', required=True)
    selected = serializers.BooleanField(label='选中状态', required=False, default=True)

    def validate(self, attrs):

        sku_id = attrs.get('sku_id')
        try:
            sku = SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')
        if sku.stock < attrs['count']:
            raise serializers.ValidationError('库存不足')

        return attrs


class CartSKUSerializer(serializers.ModelSerializer):

    count = serializers.IntegerField(label='数量', read_only=True)
    selected = serializers.BooleanField(label='选中状态', read_only=True)

    class Meta:
        model = SKU
        fields = ('id', 'count', 'name', 'default_image_url', 'price', 'selected')


class CartDeleteSerializer(serializers.Serializer):

    sku_id = serializers.IntegerField(label='商品id', required=True)

    def validate(self, attrs):
        sku_id = attrs.get('sku_id')
        try:
            SKU.objects.get(pk=sku_id)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return attrs
