from django.db import models
from django.utils import timezone
from decimal import Decimal
from products.models import Product

class Sale(models.Model):
    date_added = models.DateTimeField(default=timezone.now)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount_payed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_change = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_totals(self):
        # Calculate the sub_total by summing the total_price of each SaleDetail
        self.sub_total = sum(detail.total_price for detail in self.details.all())

        # Calculate the tax amount based on the tax percentage
        self.tax_amount = self.sub_total * (Decimal(self.tax_percentage) / Decimal('100'))

        # Calculate the grand total (sub_total + tax)
        self.grand_total = self.sub_total + self.tax_amount

        # Calculate the amount of change (amount_payed - grand_total)
        self.amount_change = self.amount_payed - self.grand_total

        # Save the Sale instance
        self.save()


    def __str__(self):
        return f"Sale ID: {self.id} | Grand Total: {self.grand_total}"


class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, related_name='details', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT) 
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Product: {self.product.name} | Quantity: {self.quantity}"


