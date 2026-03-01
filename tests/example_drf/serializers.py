from rest_framework import serializers
from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "description", "price"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = "User"
        fields = "__all__"


class CustomDataSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
