from django_filters import rest_framework as filters
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.filters import SearchFilter
from django.contrib.auth.models import User
import random
from .models import Category, MenuItems, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, OrderSerializer, CartSerializer, UserSerializer
from .pagination import CustomPagination
from .permissions import IsManager
from .filters import MenuItemFilter

# GET: list (multiple objects) / retrieve (single object)
# POST: create
# PUT: update
# PATCH: partial_update
# DELETE: destroy

class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    def create(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists() or request.user.is_superuser:
            return super().create(request, *args, **kwargs)
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
    
class SingleCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    def destroy(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            return super().destroy(request, *args, **kwargs)
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemSerializer   
    filterset_class = MenuItemFilter
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    search_fields = ['title', 'category__title']    # /menu-items?search=desert
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            #create the item and return 201 created
            return super().create(request, *args, **kwargs)
        #return 403 unauthorized
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

class SingleItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    def update(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            return super().update(request, *args, **kwargs)
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
    def partial_update(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            return super().partial_update(request, *args, **kwargs)
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
    def destroy(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            return super().destroy(request, *args, **kwargs)
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = CartSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        menuitem_id = request.data.get('menuitem')
        if not menuitem_id:
            return Response({'detail': 'Menu item is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            menuitem = MenuItems.objects.get(pk=menuitem_id)
        except MenuItems.DoesNotExist:
            return Response({'detail': 'The menu item you are looking for does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        quantity = request.data.get('quantity', 1)
        try:
            quantity = int(quantity)
        except ValueError:
            return Response({'detail': 'Quantity must be a number'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity < 1:
            return Response({'detail': 'Must be at least 1 item to add to cart'}, status=status.HTTP_400_BAD_REQUEST)

        unit_price = menuitem.price

        try:
            cart_item = Cart.objects.get(user=request.user, menuitem=menuitem)
            cart_item.quantity += quantity
            cart_item.price = int(cart_item.quantity)*unit_price
            cart_item.save()
            created = False
        except Cart.DoesNotExist:
            cart_item = Cart.objects.create(
                user=request.user,
                menuitem=menuitem,
                quantity=quantity,
                unit_price=unit_price,
                price=quantity * unit_price
            )
            created = True
        serializer = CartSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        cart_items = Cart.objects.filter(user=request.user)
        cart_items.delete()
        return Response({'detail': 'Cart has been emptied'}, status=status.HTTP_204_NO_CONTENT)

class OrderFilter(filters.FilterSet):
    status = filters.CharFilter(method='filter_by_status')
    def filter_by_status(self, queryset, name, value):
        status_map = {'pending': 0, 'delivered': 1}
        return queryset.filter(status=status_map[value])

    class Meta:
        model = Order
        fields = ['user', 'delivery_crew', 'total', 'date', 'status']

class OrdersView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    filterset_class = OrderFilter
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            return super().list(request, *args, **kwargs)
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew=request.user)
        else:
            orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # get current cart items
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        total_price = sum(int(item.quantity)*item.price for item in cart_items)

        delivery_crew_members = User.objects.filter(groups__name='Delivery crew')
        if not delivery_crew_members.exists():
            return Response({'detail': 'No delivery crew available'}, status=status.HTTP_400_BAD_REQUEST)
        delivery_crew = random.choice(delivery_crew_members)
        order = Order.objects.create(
            user=request.user,
            status=0,
            delivery_crew=delivery_crew,
            total=total_price
        )

        #add cart items to order table
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.quantity*item.price
            )
        cart_items.delete()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user == request.user:
            return super().retrieve(request, *args, **kwargs)
        return Response({'detail': 'This is not your order'}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user == request.user:
            return super().partial_update(request, *args, **kwargs)
        return Response({'detail': 'This is not your order'}, status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        # manager can update delivery crew and status
        if request.user.groups.filter(name='Manager').exists():
            delivery_crew = request.data.get('delivery_crew')
            status = request.data.get('status')

            if delivery_crew is not None:
                instance.delivery_crew = delivery_crew
            if status is not None:
                instance.status = status

            if delivery_crew is not None or status is not None:
                instance.save()
                return Response(self.get_serializer(instance).data)
            return Response({'detail': 'Please update the delivery crew or status.'}, status=status.HTTP_400_BAD_REQUEST)

        # allow delivery crew to update status only
        if request.user.groups.filter(name='Delivery crew').exists():
            status = request.data.get('status')
            if status is not None:
                instance.status = status    # access the instance object and update the status
                instance.save() # save the instance
                return Response(self.get_serializer(instance).data)   # serialize and return the updated instance
            return Response({'detail': 'Please update the status.'}, status=status.HTTP_400_BAD_REQUEST)

        # user can update their order
        if instance.user == request.user:
            return super().partial_update(request, *args, **kwargs)
        return Response({'detail': 'This is not your order'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        if request.user.groups.filter(name='Manager').exists():
            return super().destroy(request, *args, **kwargs)
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)


class GroupView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated, IsManager]
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        group_name = self.kwargs.get('group_name')
        if group_name == 'delivery-crew':
            all_delivery_crew = User.objects.filter(groups__name='Delivery crew')
            serializer = UserSerializer(all_delivery_crew, many=True)
            return Response(serializer.data)
        elif group_name == 'manager':
            all_managers = User.objects.filter(groups__name='Manager')
            serializer = UserSerializer(all_managers, many=True)
            return Response(serializer.data)
        return Response({'detail': 'You can only list delivery-crew or manager groups.'}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        group_name = self.kwargs.get('group_name')
        user = User.objects.get(pk=request.data.get('user'))
        if group_name == 'delivery-crew':
            if user.groups.filter(name='Delivery crew').exists():
                return Response({'detail': 'User is already in delivery crew'}, status=status.HTTP_200_OK)
            user.groups.add(2)

            # remove user from manager group if they are in it
            if user.groups.filter(name='Manager').exists():
                user.groups.remove(1)
            return Response({'detail': 'User added to delivery crew'}, status=status.HTTP_201_CREATED)
        elif group_name == 'manager':
            if user.groups.filter(name='Manager').exists():
                return Response({'detail': 'User is already manager'}, status=status.HTTP_200_OK)
            user.groups.add(1)

            if user.groups.filter(name='Delivery crew').exists():
                user.groups.remove(2)
            return Response({'detail': 'User added to manager group'}, status=status.HTTP_201_CREATED)
        return Response({'detail': 'You can only add user to delivery-crew or manager groups.'}, status=status.HTTP_404_NOT_FOUND)

class SingleGroupView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsAuthenticated, IsManager]

    def destroy(self, request, *args, **kwargs):
        group_name = self.kwargs.get('group_name')
        user = self.get_object()
        if group_name == 'delivery-crew':
            if user.groups.filter(name='Delivery crew').exists():
                user.groups.remove(2)
                return Response({'detail': 'User removed from delivery crew'}, status=status.HTTP_200_OK)
            return Response({'detail': 'User is not in delivery crew'}, status=status.HTTP_404_NOT_FOUND)
        elif group_name == 'manager':
            if user.groups.filter(name='Manager').exists():
                user.groups.remove(1)
                return Response({'detail': 'User removed from manager group'}, status=status.HTTP_200_OK)
            return Response({'detail': 'User is not manager'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'detail': 'You can only remove user from delivery-crew or manager groups.'}, status=status.HTTP_404_NOT_FOUND)