from rest_framework import serializers
from rest_framework.reverse import reverse
from django.contrib.auth.models import User
from .models import League, Season, Team, Fixture , Prediction, UserGroup

class SeasonSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Season model, including league details and associated teams.
    """
    
    league = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ['url','id','league', 'year', 'start_year']

    def get_league(self, obj):
        return {
            'id': obj.league.id,
            'name': obj.league.name,
            'country': obj.league.country,
            'level': obj.league.level,
            'api_id': obj.league.api_id
        }

    def validate_year(self, value):
        """Validating the year field to have the format 'start_year-(start_year+1)'"""
        start_year = self.initial_data.get('start_year')
        if start_year:
            expected_year = f"{start_year}-{int(start_year) + 1}"
            if value != expected_year:
                raise serializers.ValidationError(
                    f"Year must be in format 'start_year-(start_year+1)', expected: {expected_year}"
                )
        return value

class LeagueSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the League model, providing basic league information and related seasons.
    """
    seasons = SeasonSerializer(many=True, read_only=True)

    class Meta:
        model = League
        fields = ['url','name', 'country', 'level', 'api_id', 'seasons']

class FixtureSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Fixture model, including season details.
    Also includes user-specific prediction data if available.
    """

    season = SeasonSerializer(read_only=True)
    home_team = serializers.StringRelatedField(source='home_team.name', read_only=True)
    away_team = serializers.StringRelatedField(source='away_team.name', read_only=True)
    user_prediction = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_user_prediction(self, obj):
        user = self.context['request'].user
        access_code = self.context['request'].query_params.get('access_code')
        if access_code:
            user_group = UserGroup.objects.filter(access_code=access_code, members=user).first()
            if user_group:
                prediction = Prediction.objects.filter(user=user, fixture=obj, user_group=user_group).first()
                if prediction:
                    return {
                        'predicted_home_score': prediction.predicted_home_score,
                        'predicted_away_score': prediction.predicted_away_score,
                        'created_at': prediction.created_at,
                        'id': prediction.id
                    }
                   
        return None
    
    def get_url(self, obj):
        # user = self.context['request'].user
        access_code = self.context['request'].query_params.get('access_code')

        prediction = self.get_user_prediction(obj)
        if prediction:
            return reverse('prediction-detail', args=[prediction['id']], request=self.context['request']) + f"?access_code={access_code}"
        else:
            return reverse('prediction-create', request=self.context['request']) + f"?access_code={access_code}"
                        
    class Meta:
        model = Fixture
        fields = ['url','season', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'status', 'round','round_name','api_id', 'user_prediction']

class PredictionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Prediction model, including user and fixture details.
    """
    user = serializers.StringRelatedField(source='user.username', read_only=True)
    fixture = FixtureSerializer(read_only=True)

    class Meta:
        model = Prediction
        fields = ['id', 'user', 'fixture', 'predicted_home_score', 'predicted_away_score', 'created_at']

class UserGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for listiting user groups.
    """
    class Meta:
        model = UserGroup
        fields = ['id', 'name', 'access_code', 'season']

class PredictionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Prediction instances.
    User is automatically set from request context.
    User_group is selected by ID from frontend or URL.
    Fixture is limited to matches from the group's season.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_group = serializers.PrimaryKeyRelatedField(queryset=UserGroup.objects.all())
    fixture = serializers.PrimaryKeyRelatedField(queryset=Fixture.objects.filter(status='NS'))
    predicted_home_score = serializers.IntegerField(min_value=0)
    predicted_away_score = serializers.IntegerField(min_value=0)

    def __init__(self,*args , **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' in self.context:
            user = self.context['request'].user
            access_code = self.context['request'].query_params.get('access_code')
            if access_code:
                user_groups = UserGroup.objects.filter(members=user, access_code=access_code).first()
                if user_groups and user_groups.season:
                    self.fields['fixture'].queryset = Fixture.objects.filter(season=user_groups.season, status='NS')
                else:
                    raise serializers.ValidationError("Invalid group or no season associated")
            else:
                user_groups = UserGroup.objects.filter(members=user)
                if user_groups.exists():
                    self.fields['fixture'].queryset = Fixture.objects.filter(
                        season__in=user_groups.values_list('season'), status='NS'
                    )
                else:
                    raise serializers.ValidationError("User does not belong to any group")
    class Meta:
        model = Prediction
        fields = ['id', 'user', 'user_group','fixture', 'predicted_home_score', 'predicted_away_score', 'created_at']
        read_only_fields = ['id','user','created_at']

    def validate(self, attrs):
        """
        Ensure user can only predict once per fixture in the group and belongs to the group
        and predict only match with status NS.
        """
        user = self.context['request'].user
        fixture = attrs['fixture']
        user_group = attrs['user_group']
        if not  user.user_groups.filter(id=user_group.id).exists():
            raise serializers.ValidationError("You are not a member of this group.")
        if Prediction.objects.filter(user=user, fixture=fixture, user_group=attrs['user_group']).exists() and self.instance is None:
            raise serializers.ValidationError("You have already made a prediction for this fixture in this group.")
        if fixture.status != 'NS':
            raise serializers.ValidationError("You can only predict matches with status 'NS' (Not Started).")
        return attrs
    
class PredictionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Prediction instances.
    Only predicted scores can be updated.
    """
    predicted_home_score = serializers.IntegerField(min_value=0)
    predicted_away_score = serializers.IntegerField(min_value=0)

    class Meta:
        model = Prediction
        fields = ['id','fixture','user_group','predicted_home_score', 'predicted_away_score']
        read_only_fields = ['id','fixture','user_group']
