from django.db import models
from django.contrib.auth.models import User


class Franchise(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True
    )

    poster_url = models.URLField(
        max_length=500,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Movie(models.Model):
    franchise = models.ForeignKey(
        Franchise,
        on_delete=models.CASCADE,
        related_name='movies'
    )

    title = models.CharField(
        max_length=255
    )

    release_year = models.IntegerField(
        blank=True,
        null=True
    )

    release_date = models.DateField(
        blank=True,
        null=True
    )

    distributor = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    chronological_order = models.IntegerField(
        blank=True,
        null=True
    )

    poster_url = models.URLField(
        max_length=500,
        blank=True,
        null=True
    )

    backdrop_url = models.URLField(
        max_length=500,
        blank=True,
        null=True
    )

    overview = models.TextField(
        blank=True,
        null=True
    )

    tagline = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    genres = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    runtime = models.IntegerField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            'chronological_order',
            'release_year'
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'franchise',
                    'title',
                    'release_year'
                ],
                name='unique_movie_in_franchise'
            )
        ]

    def __str__(self):
        return self.title


class WatchedMovie(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='watched_history'
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='watched_by'
    )

    watched_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            'user',
            'movie'
        )

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}"
    

class Watchlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='watchlist'
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='watchlisted_by'
    )
    added_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            'user',
            'movie'
        )

    def __str__(self):
        return f"{self.user.username} watchlisted {self.movie.title}"