from rest_framework import generics
from .models import League, Season, Fixture
from .serializers import LeagueSerializer, SeasonSerializer, FixtureSerializer

class LeagueListView(generics.ListAPIView):
    queryset = League.objects.all()
    serializer_class = LeagueSerializer

class LeagueDetailView(generics.RetrieveAPIView):
    queryset = League.objects.all()
    serializer_class = LeagueSerializer

class SeasonDetailView(generics.RetrieveAPIView):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer

class FixtureListView(generics.ListAPIView):
    queryset = Fixture.objects.all()
    serializer_class = FixtureSerializer

class FixtureDetailView(generics.RetrieveAPIView):
    queryset = Fixture.objects.all()
    serializer_class = FixtureSerializer