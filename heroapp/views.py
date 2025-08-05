"""
Views for the hero API.

This module defines two endpoints on the same URL (``/hero/``) that
respond to both POST and GET requests.  The POST endpoint accepts a
``name`` parameter, looks up the superhero using an external API and
persist the hero into the database.  The GET endpoint supports
filtering heroes by name and a handful of numeric statistics.

To avoid dependency on the official superheroapi.com service—which
requires an access token—we default to using the open source
``https://akabab.github.io/superhero-api/api/all.json`` dataset.
Developers may optionally set ``SUPERHERO_API_TOKEN`` in the
environment to instruct the code to call the official service instead.

Error responses are returned with a 4xx status code and a JSON body
containing a single ``error`` key describing the problem.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

import requests
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Hero


def _parse_numeric_query(value: str) -> Tuple[str, int]:
    """Parse an incoming numeric query parameter into a Django lookup.

    The numeric query parameters can include comparison operators as a
    prefix.  Supported prefixes are ``>=``, ``<=``, ``>``, ``<``, or
    nothing (exact match).  The returned tuple contains the lookup
    suffix (e.g. ``'gte'``) and the integer value.

    :param value: raw query parameter from the request
    :return: tuple of (lookup_suffix, integer value)
    :raises ValueError: if the value cannot be converted to an integer
    """
    original = value.strip()
    if original.startswith('>='):
        number = original[2:]
        lookup = 'gte'
    elif original.startswith('<='):
        number = original[2:]
        lookup = 'lte'
    elif original.startswith('>'):
        number = original[1:]
        lookup = 'gt'
    elif original.startswith('<'):
        number = original[1:]
        lookup = 'lt'
    else:
        number = original
        lookup = 'exact'
    try:
        return lookup, int(number)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value: {original}") from exc


def _fetch_hero_from_api(name: str) -> Optional[Dict[str, Any]]:
    """Fetch a superhero by name using the configured external API.

    This helper will attempt to locate a hero with a matching name
    (case-insensitive).  When using the default open source API it
    fetches the entire list of heroes on first call and performs a
    linear search.  When using the official API it issues a search
    request which may return multiple candidates.

    :param name: The name of the hero to search for
    :return: A dictionary containing the hero's name and selected
             power statistics, or ``None`` if no hero is found
    """
    source = os.getenv('SUPERHERO_API_SOURCE')
    token = os.getenv('SUPERHERO_API_TOKEN')
    target_name = name.strip().lower()

    # If a custom source is provided and ends with ``/all.json`` we treat
    # it as an open dataset containing every hero.  This avoids the need
    # for API tokens and rate limits.
    if source and source.endswith('/all.json'):
        try:
            response = requests.get(source, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            return None
        try:
            heroes = response.json()
        except ValueError:
            return None
        for entry in heroes:
            if entry.get('name', '').lower() == target_name:
                powerstats = entry.get('powerstats', {}) or {}
                return {
                    'name': entry.get('name', name),
                    'intelligence': _convert_stat(powerstats.get('intelligence')),
                    'strength': _convert_stat(powerstats.get('strength')),
                    'speed': _convert_stat(powerstats.get('speed')),
                    'power': _convert_stat(powerstats.get('power')),
                }
        return None

    # Fallback to official superheroapi.com if a token is provided
    if token:
        url = f'https://superheroapi.com/api/{token}/search/{name}'
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            return None
        try:
            data = response.json()
        except ValueError:
            return None
        if data.get('response') != 'success':
            return None
        for result in data.get('results', []):
            if result.get('name', '').lower() == target_name:
                powerstats = result.get('powerstats', {}) or {}
                return {
                    'name': result.get('name', name),
                    'intelligence': _convert_stat(powerstats.get('intelligence')),
                    'strength': _convert_stat(powerstats.get('strength')),
                    'speed': _convert_stat(powerstats.get('speed')),
                    'power': _convert_stat(powerstats.get('power')),
                }
        return None

    # If no source or token is configured, we cannot perform a lookup
    return None


def _convert_stat(value: Any) -> int:
    """Normalize a power statistic value into an integer.

    The external API may represent statistics as strings, numbers, or
    placeholders such as ``'null'`` or ``'unknown'``.  Values that
    cannot be coerced to integers are treated as zero.

    :param value: raw stat value from the API
    :return: integer representation (falling back to zero on error)
    """
    try:
        if value is None:
            return 0
        # Some values arrive as strings that may contain non-numeric
        # characters (e.g. "null" or "unknown").  Coercing to int will
        # naturally raise a ValueError for these cases.
        return int(value)
    except (TypeError, ValueError):
        return 0


@csrf_exempt
def hero(request: HttpRequest) -> JsonResponse:
    """Combined view for creating and retrieving heroes.

    POST requests must supply a JSON body with a ``name`` key.  The
    endpoint attempts to find a hero with the given name using the
    external API and stores it in the local database.  If the hero
    already exists locally the record is updated with the latest
    statistics.  Successful requests return a JSON representation of
    the hero.

    GET requests support filtering by ``name`` and numeric power
    statistics using query parameters.  The numeric parameters may
    optionally include comparison operators (e.g. ``>=50``).  The
    response is a JSON array of matching heroes.  If no heroes match
    the supplied filters a 404 error is returned.
    """
    if request.method == 'POST':
        return _handle_post(request)
    if request.method == 'GET':
        return _handle_get(request)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def _handle_post(request: HttpRequest) -> JsonResponse:
    """Handle POST requests for creating heroes."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = request.POST
    name = (payload.get('name') or '').strip()
    if not name:
        return JsonResponse({'error': 'Parameter "name" is required'}, status=400)
    hero_data = _fetch_hero_from_api(name)
    if not hero_data:
        return JsonResponse({'error': f'Hero "{name}" not found'}, status=404)
    obj, created = Hero.objects.update_or_create(
        name=hero_data['name'],
        defaults={
            'intelligence': hero_data['intelligence'],
            'strength': hero_data['strength'],
            'speed': hero_data['speed'],
            'power': hero_data['power'],
        },
    )
    status_code = 201 if created else 200
    return JsonResponse(
        {
            'id': obj.id,
            'name': obj.name,
            'intelligence': obj.intelligence,
            'strength': obj.strength,
            'speed': obj.speed,
            'power': obj.power,
        },
        status=status_code,
    )


def _handle_get(request: HttpRequest) -> JsonResponse:
    """Handle GET requests for retrieving heroes with optional filters."""
    qs = Hero.objects.all()
    # Filter by name (exact, case-insensitive)
    name = request.GET.get('name')
    if name:
        qs = qs.filter(name__iexact=name)

    # Numeric filters: intelligence, strength, speed, power
    numeric_fields = ['intelligence', 'strength', 'speed', 'power']
    for field in numeric_fields:
        raw_value = request.GET.get(field)
        if raw_value:
            try:
                lookup, number = _parse_numeric_query(raw_value)
            except ValueError as exc:
                return JsonResponse({'error': str(exc)}, status=400)
            qs = qs.filter(**{f'{field}__{lookup}': number})

    if not qs.exists():
        return JsonResponse({'error': 'No heroes match the given criteria'}, status=404)
    heroes = [
        {
            'id': obj.id,
            'name': obj.name,
            'intelligence': obj.intelligence,
            'strength': obj.strength,
            'speed': obj.speed,
            'power': obj.power,
        }
        for obj in qs.order_by('name')
    ]
    return JsonResponse({'heroes': heroes}, status=200)