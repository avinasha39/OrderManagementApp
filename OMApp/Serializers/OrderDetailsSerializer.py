from ..models import OrderDetails
from rest_framework import serializers


class OrderDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetails
        fields = ['Customer_name','Customer_add','Delivery_Distance',]
