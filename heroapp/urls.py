"""
URL definitions for heroapp.

The API exposes a single endpoint at ``/hero/`` that accepts both
GET and POST requests.  All logic is delegated to the view defined in
``heroapp.views``.
"""

from django.urls import path

from . import views

urlpatterns = [
    path('hero/', views.hero, name='hero'),
]