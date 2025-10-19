from django.urls import path
from .views import LeagueListView, LeagueDetailView
from .views import SeasonDetailView 
from .views import FixtureListView, FixtureDetailView
from .views import PredictionListView, PredictionDetailView, PredictionCreateView, PredictionUpdateView
from .views import GroupListView, CalculatePointsView

urlpatterns = [
    path('usergroups/', GroupListView.as_view(), name='usergroup-list'),
    path('leagues/', LeagueListView.as_view(), name='league-list'),
    path('leagues/<int:pk>/', LeagueDetailView.as_view(), name='league-detail'),
    path('seasons/<int:pk>/', SeasonDetailView.as_view(), name='season-detail'),
    path('fixtures/', FixtureListView.as_view(), name='fixture-list'),
    path('fixtures/<int:pk>/', FixtureDetailView.as_view(), name='fixture-detail'),
    path('predictions/', PredictionListView.as_view(), name='prediction-list'),
    path('predictions/<int:pk>/', PredictionDetailView.as_view(), name='prediction-detail'),
    path('predictions/create/', PredictionCreateView.as_view(), name='prediction-create'),
    path('predictions/<int:pk>/update/', PredictionUpdateView.as_view(), name='prediction-update'),
    path('predictions/calculate_points/', CalculatePointsView.as_view(), name='prediction-calculate-points'),

]