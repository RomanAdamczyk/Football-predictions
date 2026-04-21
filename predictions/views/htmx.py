# predictions/views/htmx.py

from multiprocessing import context
from urllib import request
from rest_framework.request import Request

from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django_htmx.http import HttpResponseClientRefresh
from ..models import Fixture, Prediction, UserGroup
from predictions.serializers import FixtureSerializer, PredictionCreateSerializer, PredictionUpsertSerializer
from predictions.views.api import FixtureListView, PredictionCreateView, upsert_prediction

from django.http import HttpResponse

from rest_framework.test import APIRequestFactory


# ========================
# Widoki HTMX
# ========================

from rest_framework.request import Request

@login_required
def fixtures_partial(request):
    """HTMX view returning fixtures using existing DRF FixtureListView logic."""

    drf_request = Request(request)
    drf_request.user = request.user   # ręcznie zapewniamy użytkownika

    drf_view = FixtureListView()
    drf_view.request = drf_request
    access_code = request.GET.get('access_code')
    user_group = UserGroup.objects.filter(
        access_code=access_code, 
        members=request.user
    ).first()

    fixtures = drf_view.get_queryset()

    if fixtures is None:
        fixtures = Fixture.objects.none()

    serializer = FixtureSerializer(
        fixtures, 
        many=True, 
        context={'request': drf_request}
    )

    context = {
        'fixtures': serializer.data,
        'user_group': user_group
    }

    if request.htmx:
        return render(request, 'partials/fixtures_list.html', context)

    return render(request, 'predictions/test_fixtures.html', context)

@login_required
def prediction_create_partial(request):
    """HTMX view for creating or updating a prediction."""
    
    if request.method != 'POST':
        return HttpResponse("Metoda nieobsługiwana", status=405)

    prediction, created = upsert_prediction(request)
    
    if prediction:
        access_code = request.GET.get('access_code') or request.POST.get('access_code')

        print(f"Prediction upserted: {prediction.id}, created: {created}")
        
        context = {
            'fixtures': [prediction.fixture],
            'user_group': prediction.user_group,
            'current_prediction': prediction,
            'just_saved': True,
            'was_created': created
        }
        html = render_to_string('partials/fixtures_list.html', context, request=request)
        return HttpResponse(html)
    else:
        html = "<div style='color: red; font-weight: bold; padding: 10px;'>✗ Błąd zapisu.</div>"
        return HttpResponse(html, content_type="text/html")