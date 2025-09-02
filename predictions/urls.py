from django.urls import path
from .views import LeagueListView, LeagueDetailView, SeasonDetailView, FixtureListView, FixtureDetailView

urlpatterns = [
    path('leagues/', LeagueListView.as_view(), name='league-list'),
    path('leagues/<int:pk>/', LeagueDetailView.as_view(), name='league-detail'),
    path('seasons/<int:pk>/', SeasonDetailView.as_view(), name='season-detail'),
    path('fixtures/', FixtureListView.as_view(), name='fixture-list'),
    path('fixtures/<int:pk>/', FixtureDetailView.as_view(), name='fixture-detail'),
]