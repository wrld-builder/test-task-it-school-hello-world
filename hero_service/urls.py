"""
Root URL configuration for hero_service.

The urlpatterns list routes URLs to views.  We include the heroapp's
urls at the root so that the API endpoints are available directly
under ``/hero/``.
"""

from django.urls import path, include

urlpatterns = [
    path('', include('heroapp.urls')),
]