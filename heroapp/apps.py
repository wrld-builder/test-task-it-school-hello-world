"""
App configuration for heroapp.

Defines the name used by Django to refer to this application.
"""

from django.apps import AppConfig


class HeroappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'heroapp'