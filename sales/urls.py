from django.urls import path
from . import views

urlpatterns = [
    path('pos/', views.pos, name='pos'),
    path('add-sale-item/', views.add_sale_item, name='add-sale-item'),
    path('update-quantity/<int:sale_detail_id>/', views.update_quantity, name='update_quantity'),
    path('remove-item/<int:sale_detail_id>/', views.remove_item, name='remove-item'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('checkout-success/<int:sale_id>/', views.checkout_success_view, name='checkout_success'),
   
]
