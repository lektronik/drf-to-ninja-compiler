"""
Real-world DRF serializers fixture — based on a production e-commerce API.
Tests complex patterns: nested serializers, SerializerMethodField,
custom to_representation overrides, and multiple inheritance.
"""

from rest_framework import serializers


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["name", "url"]

    def get_url(self, obj):
        return f"/api/categories/{obj.pk}/"


class TagSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ["name", "url"]

    def get_url(self, obj):
        return f"/api/tags/{obj.pk}/"


class IngredientSerializer(serializers.ModelSerializer):
    unit = serializers.StringRelatedField()

    class Meta:
        model = Ingredient
        fields = ["name", "quantity", "unit"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get("quantity") is None:
            data.pop("quantity", None)
        return data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    items = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "created_at", "status", "total", "items"]

    def get_total(self, obj):
        return sum(item.price for item in obj.items.all())

    def validate_status(self, value):
        if value not in ("pending", "confirmed", "shipped"):
            raise serializers.ValidationError("Invalid status.")
        return value
