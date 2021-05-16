from ..models import DeliveryTeam
from rest_framework import serializers


class DeliveryTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryTeam
        fields = '__all__'
