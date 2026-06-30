from django.contrib import admin
from .models import Franchise, Movie, WatchedMovie


@admin.register(Franchise)
class FranchiseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "franchise",
        "release_year",
        "release_date",
        "chronological_order",
        "distributor",
    )

    search_fields = (
        "title",
        "franchise__name",
        "distributor",
        "overview",
        "tagline",
    )

    list_filter = (
        "franchise",
        "release_year",
        "distributor",
    )

    autocomplete_fields = (
        "franchise",
    )

    ordering = (
        "title",
    )

    list_select_related = (
        "franchise",
    )


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "movie",
        "watched_at",
    )

    search_fields = (
        "user__username",
        "movie__title",
    )

    autocomplete_fields = (
        "user",
        "movie",
    )