from ..models import OrderItems
from rest_framework import serializers


class OrderItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItems
        fields = ['Model_Number','Count','Order_Number']
