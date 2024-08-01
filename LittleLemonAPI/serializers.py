from rest_framework import serializers
from django.contrib.auth.models import User 
from .models import MenuItems, Category, Cart, Order
import bleach


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title']

    def validate_title(self, value):
        return bleach.clean(value)

class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all()) # nested serializer
    class Meta:
        model = MenuItems
        fields = ['id', 'title', 'price', 'category', 'featured']
        # depth = 1
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['category'] = CategorySerializer(instance.category).data
        return rep

    def validate_title(self, value):
        return bleach.clean(value)

class CartSerializer(serializers.ModelSerializer):
    #automatically set the user to the current user
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']
        extra_kwargs = {
            'price': {'read_only': True, 'min_value': 1},
            'quantity': {'min_value': 1}
        }

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'total', 'date']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': False}
        }