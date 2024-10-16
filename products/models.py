import uuid
from django.utils.text import slugify
from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=200)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    )

    name = models.CharField(max_length=256)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=100)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    slug = models.SlugField(null=True, blank=True, db_index=True, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        # Generate SKU only if it hasn't been set already
        if not self.sku:
            self.sku = str(uuid.uuid4()).split('-')[0].upper()  # Generate a unique, short UUID
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



# Inventory batch model to track batches for FIFO
class InventoryBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_received = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units at {self.purchase_price}"

    def has_stock(self, quantity_needed):
        return self.quantity >= quantity_needed





