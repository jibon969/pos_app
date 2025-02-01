from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from sales.models import Sale, SaleDetail
from django.db.models import Q, Sum, Prefetch, Count


def dashboard(request):
    # Fetch all sales with prefetched details to reduce database queries
    queryset = Sale.objects.prefetch_related(
        Prefetch('details', queryset=SaleDetail.objects.select_related('product'))
    ).all()

    # Calculate totals in a single query
    totals = queryset.aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('grand_total'),
        total_tax=Sum('tax_amount'),
    )
    total_quantity_sold = SaleDetail.objects.filter(sale__in=queryset).aggregate(
        total_quantity=Sum('quantity')
    )['total_quantity'] or 0

    # Prepare context for the template
    context = {
        'total_sales': totals['total_sales'],
        'total_quantity_sold': total_quantity_sold,
        'total_revenue': totals['total_revenue'] or 0,
        'total_tax': totals['total_tax'] or 0,
    }

    return render(request, "dashboard/dashboard.html", context)


def sales_report(request):
    # Fetch all sales with prefetched details to reduce database queries
    queryset = Sale.objects.prefetch_related(
        Prefetch('details', queryset=SaleDetail.objects.select_related('product'))
    ).order_by('id')

    # Handle search functionality
    query = request.GET.get('q')
    if query:
        query = query.strip()
        # Filter queryset based on search query
        queryset = queryset.filter(
            Q(id__icontains=query) | 
            Q(details__product__name__icontains=query)
        ).distinct()

    # print("query :", query)
    
    # Prepare sales details for the template
    sales_details = []
    for sale in queryset:
        product_names = ", ".join(sale.details.values_list('product__name', flat=True))
        sales_details.append({
            'sale_id': sale.id,
            'date_added': sale.date_added,
            'sub_total': sale.sub_total,
            'tax_amount': sale.tax_amount,
            'grand_total': sale.grand_total,
            'quantity_sold': sale.details.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0,
            'revenue': sale.grand_total,
            'product_names': product_names,
        })
    
    # Paginate the queryset
    page = request.GET.get('page')
    paginator = Paginator(queryset, 10)  # Show 10 sales per page
    try:
        sales = paginator.page(page)
    except PageNotAnInteger:
        sales = paginator.page(1)
    except EmptyPage:
        sales = paginator.page(paginator.num_pages)

    # Prepare context for the template
    context = {
        'sales': sales,
        'query': query,
        'object_list': sales_details,
    }

    return render(request, "dashboard/sales_report.html", context)