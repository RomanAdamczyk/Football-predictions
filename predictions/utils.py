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
from predictions.models import Season, League, Team, Fixture
from datetime import datetime, timedelta


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
        print(f'Season {season_year} for league ID {league_id} does not exist.')
        return 0

    count = 0

    for team_info in teams:
        team_data = team_info.get('team', {})
        if team_data:
            team, created  = Team.objects.get_or_create(
                api_id=team_data['id'],
                defaults={'name': team_data['name']}
            )
            team.season.add(season)  
            if created:
                count += 1
    
    return count

def fetch_and_save_fixtures_from_api(league_id, season_year, start_date, end_date, split_date):
    """
    Fetches fixtures for a given league and season from API-Football from a given date range and saves them to the database.
    Fixtures are stored with unique api_id and linked to seasons via ForeignKey.
    
    Args:
        league_id (int): The ID of the league (e.g., 106 for Ekstraklasa).
        season_year (int): The starting year of the season (e.g., 2023 for 2023-2024).
        start_date (str): The start date in "YYYY-MM-DD" format.
        end_date (str): The end date in "YYYY-MM-DD" format.
        split_date (str): The date simulating today in "YYYY-MM-DD" format - only in demo version without payment plan.
        
    Returns:
        int: The number of fixtures added to the database.
    """
    if season_year not in [2021, 2022, 2023]:
        print("Season year must be one of [2021, 2022, 2023].")
        return 0    #in main app it will be deleted
    
    headers = {'x-apisports-key': API_KEY}
    params = {'league': league_id, 'season': season_year, 'from': start_date, 'to': end_date}
    response = requests.get(f"{API_URL}/fixtures", headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching fixtures for league {league_id}, season {season_year}: {response.status_code} - {response.text}")
        return 0
    
    fixtures = response.json().get('response', [])

    try:
        season = Season.objects.get(league__api_id=league_id, start_year=season_year)
    except Season.DoesNotExist:
        print(f'Season {season_year} for league ID {league_id} does not exist.')
        return 0
    
    count = 0

    for fixture_info in fixtures:
        fixture_data = fixture_info.get('fixture', {})
        teams_data = fixture_info.get('teams', {})
        goals_data = fixture_info.get('goals', {})
        league_data = fixture_info.get('league', {})
        
        home_team_data = teams_data.get('home', {})
        away_team_data = teams_data.get('away', {})
        try:        
            home_team = Team.objects.get(api_id=home_team_data.get('id'))
        except Team.DoesNotExist:
            print(f"Home team with api_id {home_team_data.get('id')} does not exist in DB.")
            continue
        try:
            away_team = Team.objects.get(api_id=away_team_data.get('id'))
        except Team.DoesNotExist:
            print(f"Away team with api_id {away_team_data.get('id')} does not exist in DB.")
            continue
        
        # status = fixture_data['status']['short'] it will be used in main app with payment plan

        if fixture_data.get('date'):  
            if fixture_data.get('date')[:10] > split_date: # in demo version without payment plan
                status = 'NS'
                home_score = None
                away_score = None
            else:
                status = 'FT'
                home_score = goals_data.get('home')
                away_score = goals_data.get('away')
        else:
            print(f"Fixture date is missing in fixture with id = {fixture_data.get('id')}.")
            continue
        
        if league_data.get('round'):
            try:
                round=int(league_data.get('round').split('-')[-1].strip())
            except ValueError:
                round=None
        else:
            round=None
            
        Fixture.objects.get_or_create(
            api_id=fixture_data.get('id'),
            defaults={
                'season': season,
                'date': fixture_data.get('date'),
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'status': status,
                'round': round,
                'round_name': league_data.get('round'),
                
            }
        )
        count += 1
    return count