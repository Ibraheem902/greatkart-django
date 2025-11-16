from itertools import product
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from carts.views import _cart_id
from category.models import Category
from orders.models import OrderProduct
from store.models import Product, ProductGallery,ReviewRating
from carts.models import CartItem
from django.core.paginator import EmptyPage,PageNotAnInteger,Paginator
from django.db.models import Q
from .forms import ReviewForm

# Create your views here.

def store(request,category_slug=None):
    categories = None
    products = None
    if category_slug != None:
        categories = get_object_or_404(Category, slug = category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products,1)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products,3)
        page = request.GET.get('page')
        paged_product = paginator.get_page(page)
        product_count = products.count()
    context={
        'products': paged_product,
        'product_count': product_count,
    }
    return render(request,'store/store.html', context)

def product_detail(request,category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug = category_slug, slug = product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request),product=single_product).exists()
    except Exception as e:
        raise e
    if request.user.is_authenticated:
        try:
            order_product = OrderProduct.objects.filter(user=request.user,product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            order_product = None
    else:
        order_product = None
    #Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id,status=True)
    product_gallary = ProductGallery.objects.filter(product_id=single_product.id)
    context={
        'single_product': single_product,
        'in_cart' : in_cart,
        'order_product': order_product,
        'reviews': reviews,
        'product_gallary':product_gallary,
    }
    return render(request,'store/product_detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products= Product.objects.order_by('created_date').filter(Q(product_name__icontains=keyword) | Q(desqription__icontains=keyword))
            product_count = products.count()
    contexts={
        'products':products,
        'product_count':product_count
    }
    return render(request,'store/store.html',contexts)

def submit_review(request,product_id):
    url = request.META.get('HTTP_REFERER')
    form=ReviewForm(request.POST)
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id,product__id=product_id)
            form = ReviewForm(request.POST,instance=reviews)
            form.save()
            messages.success(request,'Thank you your review has been updated')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.raiting = form.cleaned_data['raiting']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id=product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request,'Thank you your review has been updated')
                return redirect(url)