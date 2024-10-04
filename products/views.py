from django.shortcuts import render

# Create your views here.
# pos/views.py
from django.shortcuts import render, redirect
from .models import Product, Order, OrderItem, Inventory, Transaction
from .forms import ProductForm, OrderItemForm

# Add new product to the inventory
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            Inventory.objects.create(product=product, stock=0)  # Initialize stock at 0
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'pos/add_product.html', {'form': form})

# Create an order
def create_order(request):
    order = Order.objects.create()
    return redirect('order_detail', order_id=order.id)

# Order detail view
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.price = item.product.price * item.quantity
            item.save()

            # Update inventory
            inventory = Inventory.objects.get(product=item.product)
            inventory.stock -= item.quantity
            inventory.save()

            # Update total price of the order
            order.total_price += item.price
            order.save()

            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderItemForm()
    return render(request, 'pos/order_detail.html', {'order': order, 'form': form})

# Process the payment
def process_payment(request, order_id):
    order = Order.objects.get(id=order_id)
    if request.method == 'POST':
        amount_paid = request.POST['amount_paid']
        payment_method = request.POST['payment_method']
        Transaction.objects.create(order=order, amount_paid=amount_paid, payment_method=payment_method)
        order.completed = True
        order.save()
        return redirect('order_summary', order_id=order.id)
    return render(request, 'pos/payment.html', {'order': order})
