"""Script to fetch and save teams from API-Football to the database.

Requires:
    requests: For HTTP requests to API-Football.
    python-decouple: For loading API key from .env.

Example:
    python manage.py runscript fetch_teams
"""

import requests
from decouple import config
from predictions.models import Season, League, Team

API_KEY = config('API_FOOTBALL_KEY')
API_URL = "https://v3.football.api-sports.io"

def fetch_teams(league_id, season_year):
    """
    Fetches teams for a given league and season from API-Football.
    
    Args:
        league_id (int): The ID of the league (e.g., 106 for Ekstraklasa).
        season_year (int): The starting year of the season (e.g., 2021 for 2021-2022).
    
    Returns:
        list: A list of team data dictionaries from the API (e.g., [{"team": {"id": 553, "name": "Legia Warszawa"}}])..
        Empty list if request fails.
    """
    
    headers = {'x-apisports-key': API_KEY}
    params = {'league': league_id, 'season': season_year}
    response = requests.get(f"{API_URL}/teams", headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('response', [])
    else:
        print(f"Error fetching teams for league {league_id}, season {season_year}: {response.status_code}")
        print(response.text)
        return []

def save_teams_to_db():
    """ 
    Fetches and saves teams for all leagues and seasons (2021,2022,2023) to the database.
    Teams are stored with unique api_id and linked to seasons via ManyToManyField.

    Returns:
        None
    """

    leagues = League.objects.all()
    seasons = Season.objects.filter(start_year__in=[2021, 2022, 2023])

    for league in leagues:
        for season in seasons.filter(league=league):
            teams_data = fetch_teams(league.api_id, season.start_year)
            for team_info in teams_data:
                team_data = team_info.get('team', {})
                if team_data:
                    team, created = Team.objects.get_or_create(
                        api_id=team_data['id'],
                        defaults={'name': team_data['name']}
                    )
                    team.season.add(season)  

def run():
    """Entry point for django-extensions runscript."""
    save_teams_to_db()
