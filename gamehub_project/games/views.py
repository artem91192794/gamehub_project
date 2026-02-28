from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Game, Category
from .forms import UserRegisterForm, UserLoginForm, SearchForm

def cart_view(request):
    cart = request.session.get('cart', {})
    # cart is mapping slug->quantity
    games = Game.objects.filter(slug__in=cart.keys())
    # attach quantity to each game object for template
    games_with_qty = []
    for g in games:
        qty = cart.get(g.slug, 0)
        games_with_qty.append((g, qty))
    total = sum(g.price * qty for g, qty in games_with_qty)
    return render(request, 'games/cart.html', {'items': games_with_qty, 'total': total})

def cart_add(request, slug):
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    cart = request.session.get('cart', {})
    cart[slug] = cart.get(slug, 0) + 1
    request.session['cart'] = cart
    messages.success(request, 'Товар добавлен в корзину')
    return redirect(next_url)

def cart_remove(request, slug):
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    cart = request.session.get('cart', {})
    if slug in cart:
        del cart[slug]
        request.session['cart'] = cart
        messages.success(request, 'Товар удален из корзины')
    return redirect(next_url)

def index(request):
    form = SearchForm(request.GET)
    query = request.GET.get("q", "")
    category_slug = request.GET.get("category", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    featured_only = request.GET.get("featured", "") == "on"
    
    games = Game.objects.filter()
    
    # Поиск по тексту
    if query:
        games = games.filter(
            Q(title__icontains=query) | 
            Q(short_description__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Фильтр по категории
    if category_slug:
        games = games.filter(category__slug=category_slug)
    
    # Фильтр по цене
    if min_price:
        try:
            games = games.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            games = games.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Фильтр по рекомендуемым
    if featured_only:
        games = games.filter(featured=True)
    
    games = games.order_by('-featured', '-created_at')[:50]
    categories = Category.objects.filter(is_active=True)
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug, is_active=True).first()
    total_games_count = Game.objects.count()
    
    return render(request, "games/index.html", {
        "games": games, 
        "categories": categories, 
        "query": query,
        "selected_category": selected_category,
        "total_games_count": total_games_count,
        "search_form": form,
        "min_price": min_price,
        "max_price": max_price,
        "featured_only": featured_only
    })

def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    return render(request, "games/game_detail.html", {"game": game})

# Простая реализация "избранного" через сессию
def favorites_toggle(request, slug):
    favs = request.session.get("favorites", [])
    if slug in favs:
        favs.remove(slug)
    else:
        favs.append(slug)
    request.session["favorites"] = favs
    # redirect обратно на страницу откуда пришли или на деталь игры
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)

def favorites_list(request):
    favs = request.session.get("favorites", [])
    games = Game.objects.filter(slug__in=favs)
    return render(request, "games/favorites.html", {"games": games})

def community(request):
    """Страница сообщества"""
    return render(request, "games/community.html")

def library(request):
    """Страница библиотеки игр пользователя"""
    # Получаем игры из сессии (можно расширить для реальной библиотеки)
    library_slugs = request.session.get("library", [])
    games = Game.objects.filter(slug__in=library_slugs)
    return render(request, "games/library.html", {"games": games})

def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            login(request, user)
            return redirect('games:index')
    else:
        form = UserRegisterForm()
    return render(request, 'games/register.html', {'form': form})

def user_login(request):
    """Вход пользователя"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = UserLoginForm()
    return render(request, 'games/login.html', {'form': form})

@login_required
def user_logout(request):
    """Выход пользователя"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('games:index')

def search(request):
    """Расширенный поиск"""
    form = SearchForm(request.GET)
    games = Game.objects.all()
    
    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        category_slug = form.cleaned_data.get('category', '')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        featured_only = form.cleaned_data.get('featured', False)
        
        if query:
            games = games.filter(
                Q(title__icontains=query) | 
                Q(short_description__icontains=query) | 
                Q(description__icontains=query)
            )
        
        if category_slug:
            games = games.filter(category__slug=category_slug)
        
        if min_price:
            games = games.filter(price__gte=min_price)
        if max_price:
            games = games.filter(price__lte=max_price)
        
        if featured_only:
            games = games.filter(featured=True)
    
    games = games.order_by('-featured', '-created_at')[:100]
    categories = Category.objects.filter(is_active=True)
    
    return render(request, 'games/search.html', {
        'form': form,
        'games': games,
        'categories': categories
    })