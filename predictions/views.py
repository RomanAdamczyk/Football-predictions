from rest_framework import generics
from .models import League, Season, Fixture, Prediction, UserGroup
from .serializers import LeagueSerializer, SeasonSerializer, FixtureSerializer, PredictionSerializer, PredictionCreateSerializer, UserGroupSerializer
from rest_framework.permissions import IsAuthenticated

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

class PredictionListView(generics.ListAPIView):
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer

class PredictionDetailView(generics.RetrieveAPIView):
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer

class GroupListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserGroupSerializer

    def get_queryset(self):
        return UserGroup.objects.filter(members=self.request.user)

class PredictionCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]


    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PredictionCreateSerializer
        return PredictionSerializer
    
    def get_queryset(self):
        access_code = self.request.query_params.get('access_code')
        if access_code:
            user_group = UserGroup.objects.filter(
                acces_code=access_code, members=self.request.user).first()
            if user_group and user_group.season:
                return Prediction.objects.filter(
                    user=self.request.user,
                    user_group=user_group
                ).select_related('fixture', 'fixture__season', 'fixture__season__league','user_group')
        
        return Prediction.objects.filter(user=self.request.user).select_related('fixture', 'fixture__season', 'fixture__season__league')
    
    def perform_create(self, serializer):
        serializer.save()
