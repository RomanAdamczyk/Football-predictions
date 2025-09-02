from rest_framework import serializers
from django.contrib.auth.models import User
from .models import League, Season, Team, Fixture    

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
    """
    season = SeasonSerializer(many=True, read_only=True)
    home_team = serializers.StringRelatedField(source='home_team.name', read_only=True)
    away_team = serializers.StringRelatedField(source='away_team.name', read_only=True)

    class Meta:
        model = Fixture
        fields = ['url','season', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'status', 'round','round_name','api_id']