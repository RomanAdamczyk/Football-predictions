"""
Requires:
    requests: For HTTP requests to API-Football.
    python-decouple: For loading API key from .env.

Example:
    1. Using Django shell:
        ```bash
        python manage.py shell
        >>> from predictions.utils import fetch_and_save_seasons_from_api, fetch_and_save_teams_from_api
        >>> fetch_and_save_seasons_from_api()  # Fetches and saves all seasons for all leagues
        >>> fetch_and_save_teams_from_api(league_id=106, season_year=2023)  # Fetches teams for Ekstraklasa 2023    
"""

import requests
from decouple import config
from predictions.models import Season, League, Team


API_KEY = config('API_FOOTBALL_KEY')
API_URL = "https://v3.football.api-sports.io"

def fetch_and_save_seasons_from_api():
    """
    Fetches available seasons from API-Football and save them to the database.
    
    Returns:
        int: The number of seasons added to the database.
    """
    
    headers = {'x-apisports-key': API_KEY}
    response = requests.get(f"{API_URL}/leagues/seasons", headers=headers)

    if response.status_code != 200:
        print(f"Error fetching seasons: {response.status_code} - {response.text}")
        return 0

    seasons = response.json().get('response')
    leagues = League.objects.all()
    count = 0

    for league in leagues:
        for year in seasons:
            Season.objects.get_or_create(
                league=league,
                start_year=year,
                defaults={'year':f"{year}-{year+1}"}
                )
            count += 1
    
    return count

def fetch_and_save_teams_from_api(league_id, season_year):
    """
    Fetches teams for a given league and season from(2021,2022,2023) API-Football and saves them to the database.
    Teams are stored with unique api_id and linked to seasons via ManyToManyField..
    
    Args:
        league_id (int): The ID of the league (e.g., 106 for Ekstraklasa).
        season_year (int): The starting year of the season (e.g., 2021 for 2021-2022).
    
    Returns:
        int: The number of teams added to the database.
    """
    
    headers = {'x-apisports-key': API_KEY}
    params = {'league': league_id, 'season': season_year}
    response = requests.get(f"{API_URL}/teams", headers=headers, params=params)
    if response.status_code != 200:
        print(f"Error fetching teams for league {league_id}, season {season_year}: {response.status_code} - {response.text}")
        return 0
    
    teams = response.json().get('response', [])

    try:
        season = Season.objects.get(league__api_id=league_id, start_year=season_year)
    except Season.DoesNotExist:
        print(f'Season {season_year} for league ID {league_id} does not found.')
        return 0

    count = 0

    for team_info in teams:
        team_data = team_info.get('team', {})
        if team_data:
            team, _ = Team.objects.get_or_create(
                api_id=team_data['id'],
                defaults={'name': team_data['name']}
            )
            team.season.add(season)  
            count += 1
    
    return count