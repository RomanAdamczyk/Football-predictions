# predictions/views/htmx.py

from multiprocessing import context
from urllib import request
from rest_framework.request import Request

from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import QueryDict, HttpResponse
from django_htmx.http import HttpResponseClientRefresh
from ..models import Fixture, Prediction, UserGroup
from predictions.serializers import FixtureSerializer, PredictionCreateSerializer, PredictionUpsertSerializer
from predictions.views.api import FixtureListView, PredictionCreateView, upsert_prediction

from rest_framework.test import APIRequestFactory


# ========================
# Widoki HTMX
# ========================

from rest_framework.request import Request

# @login_required
# def fixtures_partial(request):
#     """HTMX view returning fixtures using existing DRF FixtureListView logic."""

#     drf_request = Request(request)
#     drf_request.user = request.user

#     drf_view = FixtureListView()
#     drf_view.request = drf_request
#     access_code = request.GET.get('access_code')
#     user_group = UserGroup.objects.filter(
#         access_code=access_code, 
#         members=request.user
#     ).first()

#     fixtures = drf_view.get_queryset()

#     if fixtures is None:
#         fixtures = Fixture.objects.none()

#     serializer = FixtureSerializer(
#         fixtures, 
#         many=True, 
#         context={'request': drf_request}
#     )

#     context = {
#         'fixtures': serializer.data,
#         'user_group': user_group,
        
#     }

#     if request.htmx:
#         return render(request, 'partials/fixtures_list.html', context)

#     return render(request, 'predictions/test_fixtures.html', context)

@login_required
def fixtures_partial(request):
    drf_request = Request(request)
    drf_request.user = request.user 
    
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

    params = request.GET.copy()  # Django GET (mutable!)
    params['round'] = ''
    
    all_request = Request(request, parsers=drf_request.parsers)
    all_request.user = request.user
    all_request.GET = params  # Django GET!
    
    # temp_params = drf_request.query_params.copy()
    # temp_params.pop('round', None)
    
    # temp_request = Request(request)
    # temp_request.user = request.user
    # temp_request.query_params = temp_params  # Nowa kopia

    
    drf_view_all = FixtureListView()
    # drf_view_all.request = temp_request
    drf_view_all.request = all_request
    all_fixtures = drf_view_all.get_queryset()
    rounds = all_fixtures.values('round').distinct().order_by('round') if all_fixtures else []


    # drf_view.request.query_params = drf_request.query_params.copy()
    # drf_view.request.query_params.pop('round', None)  # Usuń filtr round
    # all_fixtures = drf_view.get_queryset()
    # rounds = all_fixtures.values('round').distinct().order_by('round') if all_fixtures else []
    
    serializer = FixtureSerializer(fixtures, many=True, context={'request': drf_request, 'user_group': user_group})
    
    context = {
        'fixtures': serializer.data,
        'user_group': user_group,
        'rounds': rounds,  # Z FixtureListView!
        'selected_round': request.GET.get('round', ''),
        'access_code': access_code
    }
    
    print(f"TEMPLATE CONTEXT: rounds={len(rounds)}, fixtures={len(serializer.data)}, selected={request.GET.get('round')}")

    if request.htmx:
        html = render_to_string('partials/fixtures_list.html', context, request=request)
        print(f"HTML length: {len(html)}")
        return HttpResponse(html)
        # return render(request, 'partials/fixtures_list.html', context)
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
    
@login_required
def matchdays_partial(request):
    """HTMX view returning matchdays for a given season and league."""
    print("=== FIXTURES_PARTIAL START ===")
    access_code = request.GET.get('access_code', '1')
    round_param = request.GET.get('round')
    print(f"Fixtures: access_code={access_code}, round={round_param}")
    
    drf_request = Request(request)
    drf_request.user = request.user
    drf_view = FixtureListView()
    drf_view.request = drf_request
    
    fixtures = drf_view.get_queryset()
    print(f"Fixtures count: {fixtures.count() if fixtures else 'NONE'}")
    
    if fixtures is None:
        return HttpResponse("")  # PUSTY!
    
    serializer = FixtureSerializer(fixtures, many=True, context={'request': drf_request})
    print(f"Serialized: {len(serializer.data)} items")
    
    return render(request, 'partials/fixtures_list.html', {'fixtures': serializer.data})