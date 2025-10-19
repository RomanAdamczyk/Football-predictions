from django.contrib import admin
from .models import League, Season, Team, UserGroup, Fixture, Prediction

class LeagueAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'country', 'level', 'api_id']
    search_fields = ['name', 'country']
    list_filter = ['country', 'level']

class SeasonAdmin(admin.ModelAdmin):
    list_display = ['id', 'league', 'year', 'start_year']
    search_fields = ['league__name', 'year']
    list_filter = ['league', 'start_year']

class TeamAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'api_id']
    search_fields = ['name']
    list_filter = ['season']

class UserGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    search_fields = ['name']

class FixtureAdmin(admin.ModelAdmin):
    list_display = ['id', 'season', 'date', 'home_team', 'away_team', 'home_score', 'away_score', 'api_id', 'status']
    search_fields = ['home_team__name', 'away_team__name']
    list_filter = ['season', 'date', 'status']

class PredictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'fixture', 'predicted_home_score', 'predicted_away_score','points_awarded' ,'created_at']
    search_fields = ['user__username', 'fixture__home_team__name', 'fixture__away_team__name']
    list_filter = ['created_at']

admin.site.register(League, LeagueAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(UserGroup, UserGroupAdmin)
admin.site.register(Fixture, FixtureAdmin)
admin.site.register(Prediction, PredictionAdmin)