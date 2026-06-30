from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator  # Required for pages (48 movies per page)
from .models import Franchise, Movie, WatchedMovie, Watchlist
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models import Max, Count, Q
from django.utils import timezone
import datetime


# 1. The Home Page
def franchise_list(request):
    franchises = Franchise.objects.all().order_by('name')
    return render(request, 'franchise_list.html', {'franchises': franchises})


# 2. The Franchise Detail Page
def franchise_detail(request, franchise_id):
    franchise = get_object_or_404(Franchise, id=franchise_id)
    movies = franchise.movies.all().order_by('chronological_order')

    if request.user.is_authenticated:
        watched_movie_ids = WatchedMovie.objects.filter(
            user=request.user,
            movie__in=movies
        ).values_list('movie_id', flat=True)
    else:
        watched_movie_ids = []

    return render(request, 'franchise_detail.html', {
        'franchise': franchise,
        'movies': movies,
        'watched_movie_ids': set(watched_movie_ids)
    })


# 3. The Checkbox Toggle logic
@login_required(login_url='/login/')
def toggle_watched(request, movie_id):
    if request.method == "POST":
        movie = get_object_or_404(Movie, id=movie_id)

        # FIX #4: get_or_create() is atomic at the DB level, so two near-simultaneous
        # POSTs can't both "see" no record and both insert one.
        # This still requires unique_together = ('user', 'movie') on the WatchedMovie
        # model (+ a migration) so the DB itself rejects a duplicate row if the race
        # is somehow still hit (e.g. on a backend without SELECT ... FOR UPDATE support).
        watched_record, created = WatchedMovie.objects.get_or_create(
            user=request.user,
            movie=movie
        )

        if not created:
            # It already existed, so this click means "uncheck it"
            watched_record.delete()
            return JsonResponse({'status': 'unchecked'})

        return JsonResponse({'status': 'checked'})

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required(login_url='/login/')
def toggle_watchlist(request, movie_id):
    if request.method == "POST":
        movie = get_object_or_404(Movie, id=movie_id)

        watchlist_record, created = Watchlist.objects.get_or_create(
            user=request.user,
            movie=movie
        )

        if not created:
            watchlist_record.delete()
            return JsonResponse({'status': 'removed'})

        return JsonResponse({'status': 'added'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

# 4. The Individual Movie Detail Page
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.user.is_authenticated:
        is_watched = WatchedMovie.objects.filter(user=request.user, movie=movie).exists()
        is_in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
    else:
        is_watched = False
        is_in_watchlist = False

    return render(request, 'movie_detail.html', {
        'movie': movie,
        'is_watched': is_watched,
        'is_in_watchlist': is_in_watchlist,
    })


# 5. The ALL MOVIES Directory 
def all_movies(request):
    movies = Movie.objects.select_related('franchise').all()

    genre_query = request.GET.get('genre')
    if genre_query:
        movies = movies.filter(genres__icontains=genre_query)

    sort_query = request.GET.get('sort', '-release_year')
    if sort_query == 'title':
        movies = movies.order_by('title')
    elif sort_query == '-vote_average':
        movies = movies.order_by('-vote_average', '-release_year')
    else:
        movies = movies.order_by('-release_year', 'title')

    paginator = Paginator(movies, 48)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.user.is_authenticated:
        watched_movie_ids = WatchedMovie.objects.filter(
            user=request.user,
            movie__in=page_obj.object_list
        ).values_list('movie_id', flat=True)
    else:
        watched_movie_ids = []

    popular_genres = [
        'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
        'Documentary', 'Drama', 'Family', 'Fantasy', 'Horror',
        'Mystery', 'Romance', 'Science Fiction', 'Thriller'
    ]

    querystring = request.GET.copy()
    querystring.pop('page', None)

    return render(request, 'all_movies.html', {
        'page_obj': page_obj,
        'watched_movie_ids': set(watched_movie_ids),
        'current_genre': genre_query,
        'current_sort': sort_query,
        'genres': popular_genres,
        'querystring': querystring.urlencode(),
    })


# 6. Create Account / Signup
def signup(request):
    # If the user clicks the "Create Account" button
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Save the new user to the database
            user = form.save()
            # Log them in immediately
            login(request, user)
            # Send them to the homepage
            return redirect('franchise_list') 
    else:
        # If they just navigated to the page, show a blank form
        form = UserCreationForm()
    
    return render(request, 'account/signup.html', {'form': form})


@login_required(login_url='/login/')
def watched_status(request):
    """Return which movies the user has watched (for bfcache sync)"""
    ids_param = request.GET.get('ids', '')
    movie_ids = [int(i) for i in ids_param.split(',') if i.isdigit()]
    
    watched = set(
        WatchedMovie.objects.filter(
            user=request.user, movie_id__in=movie_ids
        ).values_list('movie_id', flat=True)
    )
    
    return JsonResponse({'watched': list(watched)})

@login_required(login_url='/login/')
def watchlist_status(request):
    """Return the user's current watchlist movie ids (for bfcache sync on profile page)"""
    watchlist_ids = list(
        Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True)
    )
    return JsonResponse({'watchlist': watchlist_ids})

def search(request):
    query = request.GET.get("q", "").strip()
    movies = Movie.objects.none()
    franchises = Franchise.objects.none()
 
    if query:
        movies = Movie.objects.filter(
            Q(title__icontains=query) |
            Q(overview__icontains=query) |
            Q(tagline__icontains=query) |
            Q(distributor__icontains=query)
        )
        franchises = Franchise.objects.filter(name__icontains=query)
 
    return render(request, "profile-search/search.html", {
        "query": query,
        "movies": movies,
        "franchises": franchises,
    })
 
 
@login_required
def profile(request):
    watchlist_qs = Watchlist.objects.filter(
        user=request.user
    ).select_related('movie', 'movie__franchise').order_by('-added_at')

    watchlist_movies = [w.movie for w in watchlist_qs]

    return render(request, "profile-search/profile.html", {
        "user": request.user,
        "watchlist_movies": watchlist_movies,
    })


def _build_franchise_data(franchises_qs, user, last_watched_map=None):
    """
    Same .filter(movie__in=...) pattern as franchise_detail() — avoids the
    guessed related_name issue from before entirely.
    """
    last_watched_map = last_watched_map or {}
    data = []
    for franchise in franchises_qs:
        movies = franchise.movies.all().order_by('chronological_order')
        f_watched_ids = set(
            WatchedMovie.objects.filter(
                user=user, movie__in=movies
            ).values_list('movie_id', flat=True)
        )
        total_count = movies.count()
        watched_count = len(f_watched_ids)
        percent = int((watched_count / total_count) * 100) if total_count else 0
        data.append({
            'franchise': franchise,
            'movies': movies,
            'watched_ids': f_watched_ids,
            'watched_count': watched_count,
            'total_count': total_count,
            'percent': percent,
            'last_watched': last_watched_map.get(franchise.id),
        })
    return data


def _franchise_ids_and_last_watched(user):
    all_watched = WatchedMovie.objects.filter(
        user=user
    ).select_related('movie', 'movie__franchise')

    franchise_ids = set()
    last_watched_per_franchise = {}

    for w in all_watched:
        franchise = w.movie.franchise
        if franchise is None:
            continue
        franchise_ids.add(franchise.id)

        ts = getattr(w, 'watched_at', None)
        if ts and (
            franchise.id not in last_watched_per_franchise
            or ts > last_watched_per_franchise[franchise.id]
        ):
            last_watched_per_franchise[franchise.id] = ts

    return franchise_ids, last_watched_per_franchise


@login_required(login_url='/login/')
def watched_list(request):
    """Home watched page — two horizontal preview rails."""

    watched_qs = WatchedMovie.objects.filter(
        user=request.user
    ).select_related('movie', 'movie__franchise').order_by('-watched_at')

    total_movies_watched = watched_qs.count()
    watched_movies = [w.movie for w in watched_qs[:30]]  # capped for the rail

    franchise_ids, last_watched_per_franchise = _franchise_ids_and_last_watched(request.user)
    franchises_watched = Franchise.objects.filter(id__in=franchise_ids)

    franchise_data = _build_franchise_data(
        franchises_watched, request.user, last_watched_per_franchise
    )
    epoch = datetime.datetime.min.replace(tzinfo=timezone.utc)
    franchise_data.sort(key=lambda d: d['last_watched'] or epoch, reverse=True)

    return render(request, 'watched/watched_list.html', {
        'watched_movies': watched_movies,
        'total_movies_watched': total_movies_watched,
        'franchise_data': franchise_data,
        'total_franchises_watched': len(franchise_data),
    })


@login_required(login_url='/login/')
def watched_movies_all(request):
    """Show All → full filterable grid of every watched movie."""
    watched_qs = WatchedMovie.objects.filter(
        user=request.user
    ).select_related('movie', 'movie__franchise')

    genre = request.GET.get('genre')
    if genre:
        watched_qs = watched_qs.filter(movie__genres__icontains=genre)

    sort = request.GET.get('sort', '-watched_at')
    if sort == 'title':
        watched_qs = watched_qs.order_by('movie__title')
    else:
        sort = '-watched_at'
        watched_qs = watched_qs.order_by('-watched_at')

    watched_movies = [w.movie for w in watched_qs]

    popular_genres = [
        'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
        'Documentary', 'Drama', 'Family', 'Fantasy', 'Horror',
        'Mystery', 'Romance', 'Science Fiction', 'Thriller'
    ]

    return render(request, 'watched/watched_movies_all.html', {
        'watched_movies': watched_movies,
        'current_genre': genre,
        'current_sort': sort,
        'genres': popular_genres,
    })


@login_required(login_url='/login/')
def watched_franchises_all(request):
    """Show All → full sortable list of every franchise started."""
    franchise_ids, last_watched_per_franchise = _franchise_ids_and_last_watched(request.user)
    franchises_watched = Franchise.objects.filter(id__in=franchise_ids)

    sort = request.GET.get('sort', '-last_watched')
    if sort == 'title':
        franchises_watched = franchises_watched.order_by('name')

    franchise_data = _build_franchise_data(
        franchises_watched, request.user, last_watched_per_franchise
    )

    if sort != 'title':
        sort = '-last_watched'
        epoch = datetime.datetime.min.replace(tzinfo=timezone.utc)
        franchise_data.sort(key=lambda d: d['last_watched'] or epoch, reverse=True)

    return render(request, 'watched/watched_franchises_all.html', {
        'franchise_data': franchise_data,
        'current_sort': sort,
    })