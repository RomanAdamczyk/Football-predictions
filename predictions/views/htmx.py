# predictions/views/htmx.py

from multiprocessing import context
from urllib import request
from rest_framework.request import Request

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django_htmx.http import HttpResponseClientRefresh
from ..models import Fixture, Prediction, UserGroup
from predictions.serializers import FixtureSerializer
from predictions.views.api import FixtureListView

from django.http import HttpResponse

from rest_framework.test import APIRequestFactory

# ========================
# Widoki HTMX
# ========================

from rest_framework.request import Request

@login_required
def fixtures_partial(request):
    """HTMX view returning fixtures using existing DRF FixtureListView logic."""
    
    print("User:", request.user)
    print("Is authenticated:", request.user.is_authenticated)

    # Tworzymy poprawny DRF Request
    drf_request = Request(request)
    drf_request.user = request.user   # ręcznie zapewniamy użytkownika

    # Używamy logiki z FixtureListView
    drf_view = FixtureListView()
    drf_view.request = drf_request

    fixtures = drf_view.get_queryset()

    if fixtures is None:
        fixtures = Fixture.objects.none()

    # Serializacja z poprawnym DRF requestem w kontekście
    serializer = FixtureSerializer(
        fixtures, 
        many=True, 
        context={'request': drf_request}   # <--- tu musi być drf_request
    )

    context = {
        'fixtures': serializer.data,
        'user_group': None
    }

    if request.htmx:
        return render(request, 'partials/fixtures_list.html', context)

    return render(request, 'predictions/test_fixtures.html', context)

@login_required
def prediction_create_partial(request):
    """HTMX type saving support"""
    if request.method == 'POST':
        # Tu później dodamy logikę tworzenia Prediction
        # Na razie zwrócimy odświeżenie listy
        return HttpResponseClientRefresh()   # proste rozwiązanie na początek