from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from products.models import Product, Inventory
from sales.models import Sale, SaleDetail


def pos(request):
    products = Product.objects.all()
    
    # Fetch sale details from session, or start a new sale if necessary
    sale_id = request.session.get('sale_id')
    sale = Sale.objects.filter(id=sale_id).first()
    sale_details = sale.details.all() if sale else []

    context = {
        "products": products,
        "sale_details": sale_details,
        "sale": sale
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
            return redirect('pos')

        # Create or fetch an existing sale
        sale, created = Sale.objects.get_or_create(
            id=request.session.get('sale_id'), defaults={'sub_total': 0, 'grand_total': 0}
        )
        request.session['sale_id'] = sale.id

        # Add item to sale or update the quantity if already in sale
        sale_detail, detail_created = SaleDetail.objects.get_or_create(
            sale=sale, 
            product=product, 
            defaults={
                'price': product.price, 
                'quantity': quantity
            }
        )

        if not detail_created:
            # Update the quantity and check stock if product is already in cart
            new_quantity = sale_detail.quantity + quantity
            if new_quantity > inventory.stock:
                messages.error(request, f"Cannot add {quantity} more units. Only {inventory.stock} available.")
                return redirect('pos')

            sale_detail.quantity = new_quantity
            sale_detail.save()

        # Update inventory stock after adding to cart
        inventory.stock -= quantity
        inventory.save()

        # Recalculate totals in the sale
        sale.calculate_totals()

        messages.success(request, f"{product.name} added to cart successfully.")
        return redirect('pos')

    messages.error(request, "Invalid request.")
    return redirect('pos')


def update_quantity(request, sale_detail_id):
    if request.method == 'POST':
        sale_detail = get_object_or_404(SaleDetail, id=sale_detail_id)
        product = sale_detail.product
        inventory = get_object_or_404(Inventory, product=product)

        try:
            new_quantity = int(request.POST.get('quantity', sale_detail.quantity))

            if new_quantity > inventory.stock:
                messages.error(request, f"Only {inventory.stock} units of {product.name} are available.")
            elif new_quantity < 1:
                messages.error(request, f"Quantity cannot be less than 1.")
            else:
                # Adjust inventory stock
                difference = new_quantity - sale_detail.quantity
                if difference > 0:
                    if difference <= inventory.stock:
                        sale_detail.quantity = new_quantity
                        inventory.stock -= difference
                        sale_detail.save()
                        inventory.save()
                        messages.success(request, f"Quantity of {product.name} updated.")
                    else:
                        messages.error(request, f"Insufficient stock for {product.name}.")
                else:
                    sale_detail.quantity = new_quantity
                    inventory.stock += abs(difference)  # Increase inventory when decreasing quantity
                    sale_detail.save()
                    inventory.save()
                    messages.success(request, f"Quantity of {product.name} updated.")

                # Recalculate the sale totals
                sale_detail.sale.calculate_totals()

        except ValueError:
            messages.error(request, "Invalid quantity. Please enter a valid number.")

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
        try:
            sub_total = Decimal(request.POST.get('sub-total', '0'))
            tax_percentage = Decimal(request.POST.get('tax_percentage', '0'))
            amount_payed = Decimal(request.POST.get('amount_payed', '0'))

            # Calculate tax amount and grand total
            tax_amount = sub_total * (tax_percentage / Decimal('100'))
            grand_total = sub_total + tax_amount
            amount_change = amount_payed - grand_total

            # Fetch current sale using session
            sale_id = request.session.get('sale_id')
            sale = get_object_or_404(Sale, id=sale_id)

            # Update sale details
            sale.sub_total = sub_total
            sale.tax_percentage = tax_percentage
            sale.tax_amount = tax_amount
            sale.grand_total = grand_total
            sale.amount_payed = amount_payed
            sale.amount_change = amount_change
            sale.save()

            # Clear sale_id from session after successful checkout
            request.session.pop('sale_id', None)

            # Redirect to success page or dashboard
            return redirect('checkout_success', sale_id=sale.id)

        except InvalidOperation:
            messages.error(request, "Invalid input for totals. Please enter valid numeric values.")
            return redirect('pos')

    return render(request, 'sales/pos.html')


def checkout_success_view(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, 'sales/checkout_success.html', {'sale': sale})
