from django_filters import rest_framework as filters
from .models import MenuItems

class MenuItemFilter(filters.FilterSet):
    price__gt = filters.NumberFilter(field_name='price', lookup_expr='gt')
    price__lt = filters.NumberFilter(field_name='price', lookup_expr='lt')

    class Meta:
        model = MenuItems
        fields = ['price', 'price__lt', 'price__gt', 'featured']