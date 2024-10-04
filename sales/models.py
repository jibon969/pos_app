from django.db import models
from products.models import Product
from django.utils import timezone



# Sale model to handle POS transactions
class Sale(models.Model):
    date_added = models.DateTimeField(default=timezone.now)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # e.g., 5.00 for 5%
    amount_payed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_change = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'sales'

    def __str__(self):
        return f"Sale ID: {self.id} | Grand Total: {self.grand_total} | Datetime: {self.date_added}"

    def sum_items(self):
        return sum([detail.quantity for detail in self.details.all()])

    def calculate_totals(self):
        # Sum up all sale details
        self.sub_total = sum([detail.total_detail for detail in self.details.all()])
        self.tax_amount = self.sub_total * (self.tax_percentage / 100)
        self.grand_total = self.sub_total + self.tax_amount
        self.amount_change = self.amount_payed - self.grand_total
        self.save()


# SaleDetail model to handle individual items in a sale
class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, related_name='details', on_delete=models.CASCADE, db_column='sale')  
    product = models.ForeignKey(Product, on_delete=models.PROTECT, db_column='product')  
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_detail = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'sale_details'

    def __str__(self):
        return f"Detail ID: {self.id} | Sale ID: {self.sale.id} | Quantity: {self.quantity}"

    def save(self, *args, **kwargs):
        # Calculate total for each sale detail
        self.total_detail = self.price * self.quantity
        super().save(*args, **kwargs)