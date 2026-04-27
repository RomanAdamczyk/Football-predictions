from django.urls import path
from .views.api import LeagueListView, LeagueDetailView
from .views.api import SeasonDetailView 
from .views.api import FixtureListView, FixtureDetailView
from .views.api import PredictionListView, PredictionDetailView, PredictionCreateView, PredictionUpdateView
from .views.api import GroupListView, CalculatePointsView, UserRankingView
from .views.htmx import fixtures_partial, prediction_create_partial, matchdays_partial

urlpatterns = [
    path('partial/fixtures/', fixtures_partial, name='htmx-fixtures'),
    path('partial/predictions/create/', prediction_create_partial, name='htmx-prediction-create'),
    path('partial/matchdays/', matchdays_partial, name='htmx-matchdays'),
    path('api/usergroups/', GroupListView.as_view(), name='usergroup-list'),
    path('api/leagues/', LeagueListView.as_view(), name='league-list'),
    path('api/leagues/<int:pk>/', LeagueDetailView.as_view(), name='league-detail'),
    path('api/seasons/<int:pk>/', SeasonDetailView.as_view(), name='season-detail'),
    path('api/fixtures/', FixtureListView.as_view(), name='fixture-list'),
    path('api/fixtures/<int:pk>/', FixtureDetailView.as_view(), name='fixture-detail'),
    path('api/predictions/', PredictionListView.as_view(), name='prediction-list'),
    path('api/predictions/<int:pk>/', PredictionDetailView.as_view(), name='prediction-detail'),
    path('api/predictions/create/', PredictionCreateView.as_view(), name='prediction-create'),
    path('api/predictions/<int:pk>/update/', PredictionUpdateView.as_view(), name='prediction-update'),
    path('api/predictions/calculate_points/', CalculatePointsView.as_view(), name='prediction-calculate-points'),
    path('api/user_rankings/', UserRankingView.as_view(), name='user-ranking-list'),

]