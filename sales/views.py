from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from products.models import Product, InventoryBatch
from sales.models import Sale, SaleDetail
from django.http import HttpResponse
from weasyprint import HTML
import tempfile

def pos(request):
    products = Product.objects.all()
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
        inventory_batches = InventoryBatch.objects.filter(product=product).order_by('date_received')

        # Calculate total stock available across all batches
        total_stock = sum(batch.quantity for batch in inventory_batches)

        if total_stock < quantity:
            messages.error(request, f"Only {total_stock} units of {product.name} are available.")
            return redirect('pos')

        sale, created = Sale.objects.get_or_create(
            id=request.session.get('sale_id'), defaults={'sub_total': 0, 'grand_total': 0}
        )
        request.session['sale_id'] = sale.id

        sale_detail, detail_created = SaleDetail.objects.get_or_create(
            sale=sale,
            product=product,
            defaults={'price': product.price, 'quantity': quantity}
        )

        if not detail_created:
            new_quantity = sale_detail.quantity + quantity
            sale_detail.quantity = new_quantity
            sale_detail.save()

        # Now, reduce stock using FIFO
        remaining_quantity = quantity
        for batch in inventory_batches:
            if remaining_quantity <= 0:
                break
            if batch.quantity >= remaining_quantity:
                batch.quantity -= remaining_quantity
                batch.save()
                break
            else:
                remaining_quantity -= batch.quantity
                batch.quantity = 0
                batch.save()

        sale.calculate_totals()

        messages.success(request, f"{product.name} added to cart successfully.")
        return redirect('pos')

    messages.error(request, "Invalid request.")
    return redirect('pos')


def update_quantity(request, sale_detail_id):
    if request.method == 'POST':
        sale_detail = get_object_or_404(SaleDetail, id=sale_detail_id)
        product = sale_detail.product
        inventory_batches = InventoryBatch.objects.filter(product=product).order_by('date_received')

        total_stock = sum(batch.quantity for batch in inventory_batches) + sale_detail.quantity

        try:
            new_quantity = int(request.POST.get('quantity', sale_detail.quantity))

            if new_quantity > total_stock:
                messages.error(request, f"Only {total_stock} units of {product.name} are available.")
            elif new_quantity < 1:
                messages.error(request, "Quantity cannot be less than 1.")
            else:
                difference = new_quantity - sale_detail.quantity

                # If the quantity increases, reduce from inventory stock
                if difference > 0:
                    remaining_quantity = difference
                    for batch in inventory_batches:
                        if remaining_quantity <= 0:
                            break
                        if batch.quantity >= remaining_quantity:
                            batch.quantity -= remaining_quantity
                            batch.save()
                            break
                        else:
                            remaining_quantity -= batch.quantity
                            batch.quantity = 0
                            batch.save()

                # If the quantity decreases, return to inventory stock
                elif difference < 0:
                    remaining_quantity = abs(difference)
                    for batch in inventory_batches:
                        if batch.quantity > 0:
                            batch.quantity += remaining_quantity
                            batch.save()
                            break

                # Update the sale detail quantity
                sale_detail.quantity = new_quantity
                sale_detail.save()

                # Recalculate the sale totals
                sale_detail.sale.calculate_totals()

                messages.success(request, f"Quantity of {product.name} updated.")
        except ValueError:
            messages.error(request, "Invalid quantity. Please enter a valid number.")

    return redirect('pos')


def remove_item(request, sale_detail_id):
    sale_detail = get_object_or_404(SaleDetail, id=sale_detail_id)
    product = sale_detail.product
    inventory_batches = InventoryBatch.objects.filter(product=product).order_by('-date_received')

    # Return the stock to inventory
    remaining_quantity = sale_detail.quantity
    for batch in inventory_batches:
        if remaining_quantity <= 0:
            break
        batch.quantity += remaining_quantity
        batch.save()

    # Delete the SaleDetail (remove the item from cart)
    sale_detail.delete()

    # Recalculate the sale totals
    sale_detail.sale.calculate_totals()

    messages.success(request, f"Removed {product.name} from cart.")
    return redirect('pos')


def checkout_view(request):
    if request.method == 'POST':
        try:
            sale_id = request.session.get('sale_id')
            sale = get_object_or_404(Sale, id=sale_id)

            # Retrieve and calculate the sub_total from the SaleDetails
            sale.calculate_totals()

            # Extract the tax percentage and amount payed from the form
            tax_percentage = Decimal(request.POST.get('tax_percentage', '0'))
            amount_payed = Decimal(request.POST.get('amount_payed', '0'))

            # Update sale with user-provided tax percentage and payment info
            sale.tax_percentage = tax_percentage
            sale.amount_payed = amount_payed

            # Recalculate totals after setting tax percentage and payment amount
            sale.calculate_totals()

            # Clear sale_id from the session after successful calculation
            request.session.pop('sale_id', None)

            return redirect('checkout_success', sale_id=sale.id)

        except InvalidOperation:
            # Handle invalid numeric input
            messages.error(request, "Invalid input for totals. Please enter valid numeric values.")
            return redirect('pos')

    return render(request, 'sales/pos.html')



# View for checkout success
def checkout_success_view(request, sale_id):
    # Get the sale by ID or return 404
    sale = get_object_or_404(Sale, id=sale_id)
    # Get the details (SaleDetail) for this sale
    sale_details = sale.details.all()
    # Pass the sale and sale details to the template
    context = {
        'sale': sale, 
        'sale_details': sale_details
    }
    return render(request, 'sales/checkout_success.html', context)


def generate_pdf_view(request, sale_id):
    # Get the sale by ID or return 404
    sale = get_object_or_404(Sale, id=sale_id)
    sale_details = sale.details.all()

    # Create the context with sale data
    context = {
        'sale': sale,
        'sale_details': sale_details
    }

    # Render the HTML template with context data
    html_string = render(request, 'sales/checkout_success_pdf.html', context).content.decode('utf-8')

    # Generate the PDF from the HTML string
    html = HTML(string=html_string)

    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(delete=True) as output:
        html.write_pdf(output.name)

        # Move the file pointer to the start of the file
        output.seek(0)

        # Create the HttpResponse to send the file to the user
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sale_{sale_id}.pdf"'

        return response