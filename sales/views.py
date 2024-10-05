from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages  # To display messages
from products.models import Product, Sale, SaleDetail, Inventory
from .forms import CheckoutForm
from decimal import Decimal

def pos(request):
    products = Product.objects.all()
    sale_details = SaleDetail.objects.all()

    context = {
        "products": products,
        "sale_details": sale_details
    }
    return render(request, 'sales/pos.html', context)


def add_sale_item(request):
    if request.method == "POST":
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        inventory = get_object_or_404(Inventory, product=product)  # Fetch the inventory for the product

        # Check if requested quantity exceeds available stock
        if inventory.stock < quantity:
            messages.error(request, f"Only {inventory.stock} units of {product.name} are available.")
            return redirect('pos')  # Redirect to the cart or relevant page

        # Assuming you have an active sale (create if necessary)
        sale, created = Sale.objects.get_or_create(
            id=request.session.get('sale_id'), defaults={'sub_total': 0, 'grand_total': 0}
        )
        request.session['sale_id'] = sale.id

        # Check if the product is already in the cart (SaleDetail)
        sale_total, detail_created = SaleDetail.objects.get_or_create(
            sale=sale, 
            product=product, 
            defaults={
                'price': product.price, 
                'quantity': quantity
            }
        )

        if not detail_created:
            # Update the quantity and price if product is already in the cart
            new_quantity = sale_total.quantity + quantity
            if new_quantity > inventory.stock:
                messages.error(request, f"Cannot add {quantity} more units. Only {inventory.stock} available.")
                return redirect('pos')

            sale_total.quantity = new_quantity
            sale_total.price = product.price
            sale_total.save()

        # Update the inventory stock after adding to cart
        inventory.stock -= quantity
        inventory.save()

        # Recalculate totals in the sale
        sale.calculate_totals()

        messages.success(request, f"{product.name} added to cart successfully.")
        return redirect('pos')  # Redirect to the cart or the same page

    messages.error(request, "Invalid request.")
    return redirect('pos')  # Redirect to the cart or relevant page


def increase_quantity(request, sale_detail_id):
    sale_detail = get_object_or_404(SaleDetail, id=sale_detail_id)
    product = sale_detail.product
    inventory = get_object_or_404(Inventory, product=product)

    if sale_detail.quantity < inventory.stock:
        sale_detail.quantity += 1
        sale_detail.save()
        inventory.stock -= 1
        inventory.save()

        # Recalculate the sale totals
        sale_detail.sale.calculate_totals()

        messages.success(request, f"Increased quantity of {product.name}.")
    else:
        messages.error(request, f"Only {inventory.stock} units of {product.name} are available.")
    
    return redirect('pos')


def decrease_quantity(request, sale_detail_id):
    sale_detail = get_object_or_404(SaleDetail, id=sale_detail_id)
    product = sale_detail.product
    inventory = get_object_or_404(Inventory, product=product)

    if sale_detail.quantity > 1:
        sale_detail.quantity -= 1
        sale_detail.save()
        inventory.stock += 1
        inventory.save()

        # Recalculate the sale totals
        sale_detail.sale.calculate_totals()

        messages.success(request, f"Decreased quantity of {product.name}.")
    else:
        messages.error(request, "Quantity cannot be less than 1. Use the remove option to delete the item.")

    return redirect('pos')


def remove_item(request, sale_detail_id):
    sale_detail = get_object_or_404(SaleDetail, id=sale_detail_id)
    product = sale_detail.product
    inventory = get_object_or_404(Inventory, product=product)

    # Return the stock to inventory
    inventory.stock += sale_detail.quantity
    inventory.save()

    # Delete the SaleDetail (remove the item from cart)
    sale_detail.delete()

    # Recalculate the sale totals
    sale_detail.sale.calculate_totals()

    messages.success(request, f"Removed {product.name} from cart.")
    return redirect('pos')


def checkout_view(request):
    if request.method == 'POST':
        sub_total = Decimal(request.POST.get('sub-total', '0'))
        tax_percentage = Decimal(request.POST.get('tax-inclusive', '0'))
        amount_payed = Decimal(request.POST.get('amount-payed', '0'))

        # Calculate tax amount and grand total
        tax_amount = sub_total * (tax_percentage / Decimal('100'))
        grand_total = sub_total + tax_amount
        amount_change = amount_payed - grand_total

        # Create a new Sale instance
        sale = Sale.objects.create(
            sub_total=sub_total,
            tax_percentage=tax_percentage,
            tax_amount=tax_amount,
            grand_total=grand_total,
            amount_payed=amount_payed,
            amount_change=amount_change
        )

        # Redirect or show a success message
        return redirect('home', sale_id=sale.id)

    return render(request, 'sales/pos.html')


def checkout_success_view(request, sale_id):
    sale = Sale.objects.get(id=sale_id)
    return render(request, 'sales/checkout_success.html', {'sale': sale})