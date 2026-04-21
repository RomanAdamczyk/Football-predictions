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
    # id = serializers.IntegerField(read_only=True)
    season = SeasonSerializer(read_only=True)
    home_team = serializers.StringRelatedField(source='home_team.name', read_only=True)
    away_team = serializers.StringRelatedField(source='away_team.name', read_only=True)
    user_prediction = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()

    def get_user_prediction(self, obj):
        try:
            user = self.context['request'].user
        except (KeyError, AttributeError):
            return None
        
        access_code = self.context.get('access_code')
        if not access_code:
            access_code = self.context['request'].GET.get('access_code')

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
    
    def get_url(self, obj):
        try:
            req = self.context['request']
            
            # Bezpieczne pobieranie access_code
            access_code = None
            if hasattr(req, 'query_params'):
                access_code = req.query_params.get('access_code')
            elif hasattr(req, 'GET'):
                access_code = req.GET.get('access_code')

            if access_code:
                return reverse('prediction-detail', args=[obj.id], request=req) + f"?access_code={access_code}"
            else:
                return reverse('prediction-detail', args=[obj.id], request=req)
                
        except Exception:
            # Fallback jeśli coś pójdzie nie tak
            return "#"

    def get_formatted_date(self, obj):
            """Returns the date in a readable format for templates"""
            if obj.date:
                return obj.date.strftime("%d.%m.%Y %H:%M")
            return None
         
    class Meta:
        model = Fixture
        fields = ['id','url','season','formatted_date', 'home_team', 'away_team', 'home_score', 'away_score', 'status', 'round','round_name','api_id', 'user_prediction']

class PredictionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Prediction model, including user and fixture details.
    """
    user = serializers.StringRelatedField(source='user.username', read_only=True)
    fixture = FixtureSerializer(read_only=True)

    class Meta:
        model = Prediction
        fields = ['id', 'user', 'fixture', 'predicted_home_score', 'predicted_away_score', 'created_at', "points_awarded"]

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

    def validate_unique(self, attrs):
        """
        Pomijamy sprawdzanie unique_together przy aktualizacji istniejącego rekordu.
        """
        
        print("=== VALIDATE UNIQUE CALLED ===")
        if self.instance is not None:
            return

        super().validate_unique(attrs)
    
    def validate(self, attrs):
        """Basic validation for both create and update operations."""
        user = self.context['request'].user
        fixture = attrs['fixture']
        user_group = attrs['user_group']

        print("=== VALIDATE PREDICTION ===")
        if not user.user_groups.filter(id=user_group.id).exists():
            raise serializers.ValidationError("You are not a member of this group.")

        print(f"Validating prediction for user: {user.username}, fixture: {fixture.id}, group: {user_group.name}")
        if fixture.status != 'NS':
            raise serializers.ValidationError("You can only predict matches with status 'NS' (Not Started).")

        existing = Prediction.objects.filter(user=user, fixture=fixture, user_group=user_group).first()
        attrs['_existing_prediction'] = existing

        if existing and self.instance is None:
            raise serializers.ValidationError("You have already made a prediction for this fixture in this group.")

        return attrs
    
    def create(self, validated_data):
        """Create or update prediction (upsert logic)."""

        user = self.context['request'].user
        fixture = validated_data['fixture']
        user_group = validated_data['user_group']
        predicted_home_score = validated_data['predicted_home_score']
        predicted_away_score = validated_data['predicted_away_score']

        print("=== CREATE METHOD CALLED ===")
        print("User:", user)
        print("Fixture:", fixture.id)
        print("User Group:", user_group.id)

        # update_or_create - to jest sedno
        prediction, created = Prediction.objects.update_or_create(
            user=user,
            fixture=fixture,
            user_group=user_group,
            defaults={
                'predicted_home_score': predicted_home_score,
                'predicted_away_score': predicted_away_score,
            }
        )

        print("Prediction saved. Created new:", created)
        return prediction    

class PredictionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Prediction instances.
    Only predicted scores can be updated.
    """
    predicted_home_score = serializers.IntegerField(min_value=0)
    predicted_away_score = serializers.IntegerField(min_value=0)

    class Meta:
        model = Prediction
        fields = ['user', 'fixture', 'user_group', 'predicted_home_score', 'predicted_away_score']

class PredictionUpsertSerializer(serializers.ModelSerializer):
    """The serializer is responsible for saving (creating or updating) predictions.
    It accepts data from an HTMX form and decides whether to create a new entry or update an existing one."""

    predicted_home_score = serializers.IntegerField(min_value=0, max_value=99)
    predicted_away_score = serializers.IntegerField(min_value=0, max_value=99)

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    fixture = serializers.PrimaryKeyRelatedField(queryset=Fixture.objects.all())
    user_group = serializers.PrimaryKeyRelatedField(queryset=UserGroup.objects.none())
    class Meta:
        model = Prediction
        fields = ['user', 'fixture', 'user_group', 'predicted_home_score', 'predicted_away_score']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'request' in self.context:
            user = self.context['request'].user
            self.fields['user_group'].queryset = UserGroup.objects.filter(members=user)

    def validate(self, attrs):
        print("=== VALIDATE CALLED IN UPSERT SERIALIZER ===")
        user = self.context['request'].user
        fixture = attrs['fixture']
        user_group = attrs['user_group']

        if not user.user_groups.filter(id=user_group.id).exists():
            raise serializers.ValidationError("You are not a member of this group.")

        if fixture.season != user_group.season:
            raise serializers.ValidationError("This fixture does not belong to the selected group's season.")

        if fixture.status != 'NS':
            raise serializers.ValidationError("You can only predict matches with status 'NS' (Not Started).")

        return attrs

    def validate_unique(self, attrs):
        """Wyłączamy sprawdzanie unique_together przy aktualizacji."""
        print("=== VALIDATE UNIQUE CALLED IN UPSERT SERIALIZER ===")
        if self.instance is not None:
            # Jeśli aktualizujemy istniejący rekord - pomijamy sprawdzanie unikalności
            return
        # Przy tworzeniu nowego - zostawiamy normalne sprawdzanie
        super().validate_unique(attrs)

    def create(self, validated_data):
        """Create or update (upsert) prediction"""
        print("=== CREATE CALLED IN UPSERT SERIALIZER ===")
        user = validated_data['user']
        fixture = validated_data['fixture']
        user_group = validated_data['user_group']
        home_score = validated_data['predicted_home_score']
        away_score = validated_data['predicted_away_score']

        # update_or_create - jedyne miejsce z bezpośrednim odwołaniem do bazy
        prediction, created = Prediction.objects.update_or_create(
            user=user,
            fixture=fixture,
            user_group=user_group,
            defaults={
                'predicted_home_score': home_score,
                'predicted_away_score': away_score,
            }
        )

        return prediction, created
class CalculatePointsSerializer(serializers.ModelSerializer):
    """
    Serializer for calculating points for a user's predictions in a specific user group.
    """
    fixture_id = serializers.PrimaryKeyRelatedField(queryset=Fixture.objects.all(), required=False)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    group_id = serializers.PrimaryKeyRelatedField(queryset=UserGroup.objects.all(), required=False)
    class Meta:
        model = Prediction
        fields = ['id','points_awarded','predicted_home_score', 'predicted_away_score']

class UserRankingSerializer(serializers.ModelSerializer):
    """
    Serializer for user rankings within a group.
    """
    total_points = serializers.IntegerField()

    class Meta:
        model = User
        fields = ['id', 'username', 'total_points']


