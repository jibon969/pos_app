# pos/forms.py
from django.forms import Textarea
from django import forms
from .models import Category, Product

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 
            'category', 
            'description', 
            'price', 
            'sku', 
            'status', 
            'slug'
        ]
        # Override the Customer some fields
        widgets = {
            'description': Textarea(attrs={'rows': 4, 'cols': 4}),
        }

