from django.contrib import admin
from .models import Franchise, Movie, WatchedMovie

admin.site.register(Franchise)
admin.site.register(Movie)
admin.site.register(WatchedMovie)