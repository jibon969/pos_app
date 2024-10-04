from django.core.paginator import Paginator
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def dashboard(request):
    context = {
        'object_list': '' ,
    }
    return render(request, "dashboard/dashboard.html", context)

