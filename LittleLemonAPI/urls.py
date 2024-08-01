from django.urls import path
from . import views

urlpatterns = [
    path('category', views.CategoryView.as_view()),
    path('category/<int:pk>', views.SingleCategoryView.as_view()),
    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.SingleItemView.as_view()),
    path('cart', views.CartView.as_view()),
    path('orders', views.OrdersView.as_view()),
    path('orders/<int:pk>', views.OrderItemView.as_view()),
    path('groups/<str:group_name>/users', views.GroupView.as_view()),
    path('groups/<str:group_name>/users/<int:pk>', views.SingleGroupView.as_view()),
]