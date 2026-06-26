from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator  # Required for pages (48 movies per page)
from .models import Franchise, Movie, WatchedMovie
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


# 1. The Home Page
def franchise_list(request):
    franchises = Franchise.objects.all().order_by('name')
    return render(request, 'franchise_list.html', {'franchises': franchises})


# 2. The Franchise Detail Page
@login_required(login_url='/login/')  # FIX #1: point to a real user-facing login page, not /admin/login/
def franchise_detail(request, franchise_id):
    franchise = get_object_or_404(Franchise, id=franchise_id)
    movies = franchise.movies.all().order_by('chronological_order')

    watched_movie_ids = WatchedMovie.objects.filter(
        user=request.user,
        movie__in=movies
    ).values_list('movie_id', flat=True)

    return render(request, 'franchise_detail.html', {
        'franchise': franchise,
        'movies': movies,
        # FIX #5: set instead of list -> O(1) membership checks in the template
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


# 4. The Individual Movie Detail Page
@login_required(login_url='/login/')
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    is_watched = WatchedMovie.objects.filter(user=request.user, movie=movie).exists()

    return render(request, 'movie_detail.html', {
        'movie': movie,
        'is_watched': is_watched
    })


# 5. The ALL MOVIES Directory (Netflix-style filterable grid)
@login_required(login_url='/login/')
def all_movies(request):
    # FIX #3: select_related for the FK to Franchise, prefetch_related for the M2M to Genre.
    # NOTE: this assumes `genres` is a ManyToManyField to a Genre model. If it's actually
    # a plain CharField (comma-separated string) on Movie, drop prefetch_related('genres')
    # entirely -- there's nothing to prefetch on a scalar field, and the .filter(genres__icontains=...)
    # below would already work fine as-is in that case.
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

    watched_movie_ids = WatchedMovie.objects.filter(
        user=request.user,
        movie__in=page_obj.object_list
    ).values_list('movie_id', flat=True)

    popular_genres = [
        'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
        'Documentary', 'Drama', 'Family', 'Fantasy', 'Horror',
        'Mystery', 'Romance', 'Science Fiction', 'Thriller'
    ]

    # FIX #2: build a querystring containing every GET param EXCEPT page, so the
    # template's pagination links can append it and carry genre/sort forward.
    # e.g. in the template: <a href="?{{ querystring }}&page={{ page_obj.next_page_number }}">Next</a>
    querystring = request.GET.copy()
    querystring.pop('page', None)

    return render(request, 'all_movies.html', {
        'page_obj': page_obj,
        # FIX #5: set instead of list
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
    
    return render(request, 'signup.html', {'form': form})