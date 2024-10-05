from django.urls import path
from . import views

urlpatterns = [
    path('pos/', views.pos, name="pos"),
    path('add-sale-item/', views.add_sale_item, name='add-sale-item'),
    path('increase/<int:sale_detail_id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:sale_detail_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove/<int:sale_detail_id>/', views.remove_item, name='remove-item'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/success/<int:sale_id>/', views.checkout_success_view, name='checkout_success'),
]