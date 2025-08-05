"""
Database models for the hero API.

We persist a subset of the power statistics for each superhero.  The
``name`` field is unique to prevent duplicate entries.  Additional
fields can easily be added if more information is desired.
"""

from django.db import models


class Hero(models.Model):
    """Represents a superhero stored in the local database."""

    name = models.CharField(max_length=255, unique=True)
    intelligence = models.IntegerField()
    strength = models.IntegerField()
    speed = models.IntegerField()
    power = models.IntegerField()

    def __str__(self) -> str:
        return self.name