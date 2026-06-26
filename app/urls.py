from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.franchise_list, name='franchise_list'),

    # --- Authentication URLs ---
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    # ADDED: This maps to the custom signup view in views.py
    path('signup/', views.signup, name='signup'), 

    # --- Movie & Franchise URLs ---
    path('franchise/<int:franchise_id>/', views.franchise_detail, name='franchise_detail'),
    path('toggle/<int:movie_id>/', views.toggle_watched, name='toggle_watched'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('movies/', views.all_movies, name='all_movies'),
]