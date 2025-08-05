"""
Tests for the hero API.

These tests leverage pytest and pytest-django.  They mock out the
external API to avoid reliance on network access.  Each test runs
against a transactional database provided by pytest-django.
"""

import json
from unittest.mock import patch

import pytest
from django.urls import reverse

from heroapp.models import Hero


@pytest.mark.django_db
def test_post_hero_success(client):
    """Ensure that posting a valid hero name stores the hero."""
    payload = {'name': 'Batman'}
    # Data returned by mocked external API
    external_data = {
        'name': 'Batman',
        'intelligence': 100,
        'strength': 26,
        'speed': 27,
        'power': 47,
    }
    with patch('heroapp.views._fetch_hero_from_api', return_value=external_data):
        response = client.post('/hero/', json.dumps(payload), content_type='application/json')
    assert response.status_code == 201
    body = response.json()
    assert body['name'] == external_data['name']
    assert body['intelligence'] == external_data['intelligence']
    # Ensure the hero was persisted
    hero = Hero.objects.get(name=external_data['name'])
    assert hero.strength == external_data['strength']


@pytest.mark.django_db
def test_post_hero_not_found(client):
    """A missing hero in the external API should return 404."""
    payload = {'name': 'NonExisting'}
    with patch('heroapp.views._fetch_hero_from_api', return_value=None):
        response = client.post('/hero/', json.dumps(payload), content_type='application/json')
    assert response.status_code == 404
    body = response.json()
    assert 'error' in body


@pytest.mark.django_db
def test_get_hero_filtering(client):
    """Verify that the GET endpoint applies filters correctly."""
    # Populate the database with two heroes
    h1 = Hero.objects.create(
        name='HeroAlpha', intelligence=50, strength=60, speed=70, power=80
    )
    h2 = Hero.objects.create(
        name='HeroBravo', intelligence=90, strength=100, speed=110, power=120
    )

    # Without filters we should get both heroes
    res = client.get('/hero/')
    assert res.status_code == 200
    data = res.json()['heroes']
    assert len(data) == 2

    # Filter by exact name
    res = client.get('/hero/?name=HeroAlpha')
    assert res.status_code == 200
    data = res.json()['heroes']
    assert len(data) == 1
    assert data[0]['name'] == 'HeroAlpha'

    # Filter by intelligence >= 60 should return only HeroBravo
    res = client.get('/hero/?intelligence=>=60')
    assert res.status_code == 200
    data = res.json()['heroes']
    assert len(data) == 1
    assert data[0]['name'] == 'HeroBravo'

    # Filter by power <= 80 should return HeroAlpha
    res = client.get('/hero/?power=<=80')
    assert res.status_code == 200
    data = res.json()['heroes']
    assert len(data) == 1
    assert data[0]['name'] == 'HeroAlpha'

    # Filter by exact strength 100 should return HeroBravo
    res = client.get('/hero/?strength=100')
    assert res.status_code == 200
    data = res.json()['heroes']
    assert len(data) == 1
    assert data[0]['name'] == 'HeroBravo'

    # Filter resulting in no heroes should return 404
    res = client.get('/hero/?speed=>=200')
    assert res.status_code == 404
    assert 'error' in res.json()