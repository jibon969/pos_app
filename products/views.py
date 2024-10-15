from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Product, InventoryBatch
from .forms import CategoryForm, ProductForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q


# Create a new category
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'products/category-crud/category_form.html', {'form': form})


# Read or list all categories
def category_list(request):
    categories = Category.objects.all()
    query = request.GET.get('q')
    page = request.GET.get('page')
    if query:
        query = query.strip()
        categories = categories.filter(
            Q(name__icontains=query)
        ).distinct()
    paginator = Paginator(categories, 10)
    try:
        categories = paginator.page(page)
    except PageNotAnInteger:
        categories = paginator.page(1)
    except EmptyPage:
        categories = paginator.page(paginator.num_pages)
    context = {
        'object_list': categories,
        'page': page,
        'query': query
    }
    return render(request, 'products/category-crud/category_list.html', context)


# Update an existing category
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        # Manually update the category object
        category.name = request.POST.get('name')
        category.save()
        return redirect('category_list')
    context = {
        'category': category
    }
    return render(request, 'products/category-crud/update_category.html', context)


# Delete a category
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    context = {
        'category': category
    }
    return render(request, 'products/category-crud/category_confirm_delete.html', context)


# Read or List Products
def product_list(request):
    products = Product.objects.all()
    query = request.GET.get('q')
    page = request.GET.get('page')
    if query:
        query = query.strip()
        products = products.filter(
            Q(name__icontains=query) |
            Q(name__startswith=query) |
            Q(name__endswith=query) |
            Q(description__icontains=query)
        ).distinct()
    paginator = Paginator(products, 10)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    context = {
        'object_list': products,
        'page': page,
        'query': query
    }
    
    return render(request, 'products/product-crud/product_list.html', context)


# Create a New Product
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    context = {'form': form }
    return render(request, 'products/product-crud/product_form.html', context)


# Update an Existing Product
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product-crud/product_update_form.html', {'form': form})


# Delete a Product
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    context = {'product': product}
    return render(request, 'products/product-crud/product_confirm_delete.html', context )
