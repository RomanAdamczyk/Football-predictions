from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from urllib3 import request
from ..models import League, Season, Fixture, Prediction, UserGroup, User
from ..serializers import LeagueSerializer, SeasonSerializer, FixtureSerializer, UserGroupSerializer
from ..serializers import PredictionSerializer, PredictionCreateSerializer, PredictionUpdateSerializer, PredictionUpsertSerializer
from ..serializers import CalculatePointsSerializer, UserRankingSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import models

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
    permission_classes = [IsAuthenticated]
    serializer_class = FixtureSerializer
    
    def get_queryset(self):
        access_code = self.request.query_params.get('access_code')
        round_param = self.request.query_params.get('round')
        print(f"Round: '{round_param}' (type: {type(round_param)})")

        if access_code:
            print(f"Round: {round_param}")
            user_group = UserGroup.objects.filter(
                access_code=access_code, members=self.request.user).first()
            if user_group and user_group.season:
                base = Fixture.objects.filter(season=user_group.season, status='NS')
                if round_param and round_param.isdigit():
                    round_num = int(round_param)
                    print(f"Filtering by round: {round_num}")
                    base = base.filter(round=round_num)
                else:
                    print("Round invalid, showing all")
                return base

class FixtureDetailView(generics.RetrieveAPIView):
    queryset = Fixture.objects.all()
    serializer_class = FixtureSerializer

class PredictionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PredictionSerializer
    
    def get_queryset(self):
        return Prediction.objects.filter(user=self.request.user)
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
                access_code=access_code, members=self.request.user).first()
            if user_group and user_group.season:
                return Prediction.objects.filter(
                    user=self.request.user,
                    user_group=user_group
                ).select_related('fixture', 'fixture__season', 'fixture__season__league','user_group')
        
        return Prediction.objects.filter(user=self.request.user).select_related('fixture', 'fixture__season', 'fixture__season__league')
    
    def perform_create(self, serializer):
        serializer.save()
class PredictionUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PredictionUpdateSerializer

    def perform_update(self, serializer):
        instance = self.get_object()

        if not instance.user_group.members.filter(id=self.request.user.id).exists():
            raise ValidationError("You are not a member of the user group associated with this prediction.")
        if instance.fixture.status != 'NS':
            raise ValidationError("You can only update predictions for unstarted fixtures.")
        
        serializer.save()
        
    def get_queryset(self):
        return Prediction.objects.filter(user=self.request.user)

class PredictionDetailView(generics.RetrieveAPIView):
    serializer_class = PredictionUpdateSerializer

    def get_queryset(self):
        return Prediction.objects.filter(user=self.request.user)

class GroupListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserGroupSerializer

    def get_queryset(self):
        return UserGroup.objects.filter(members=self.request.user)

class CalculatePointsView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CalculatePointsSerializer

    def post(self, request):
        predictions = Prediction.objects.filter(points_awarded__isnull=True, fixture__status='FT')
        predictions_list = []
        for prediction in predictions:
            fixture = prediction.fixture
            prediction.calculate_points()
            predictions_list.append(prediction)
        Prediction.objects.bulk_update(predictions_list, ['points_awarded'])

        return Response(status=204)
    
class UserRankingView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRankingSerializer

    def get_queryset(self):
        access_code = self.request.query_params.get('access_code')
        if not access_code:
            raise ValidationError("Access code is required to view rankings.")
        
        user_group = UserGroup.objects.filter(
            access_code=access_code, members=self.request.user).first()
        if not user_group:
            raise ValidationError("Invalid access code or you are not a member of this group.")
        users = User.objects.filter(user_groups__id=user_group.id).annotate(total_points=models.Sum('predictions__points_awarded')).order_by('-total_points')
        return users
        
def upsert_prediction(request):
    """
    Backendowa funkcja odpowiedzialna za upsert predykcji.
    Cała logika dostępu do bazy jest tutaj.
    """
    if request.method != 'POST':
        return None, False

    fixture_id = request.POST.get('fixture')
    user_group_id = request.POST.get('user_group')
    home_score = request.POST.get('predicted_home_score')
    away_score = request.POST.get('predicted_away_score')

    if not fixture_id or not user_group_id:
        return None, False

    prediction, created = Prediction.objects.update_or_create(
        user=request.user,
        fixture_id=fixture_id,
        user_group_id=user_group_id,
        defaults={
            'predicted_home_score': home_score,
            'predicted_away_score': away_score,
        }
    )

    return prediction, created