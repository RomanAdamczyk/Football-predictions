"""Script to fetch and save fixtures from API-Football to the database.
Requires:
    requests: For HTTP requests to API-Football.
    python-decouple: For loading API key from .env.
"""


from predictions.models import Season,  Team, Fixture
import requests
from decouple import config

API_KEY = config('API_FOOTBALL_KEY')
API_URL = "https://v3.football.api-sports.io"

def fetch_fixtures(league_id, season_year, start_date, end_date):
    """
    Fetches fixtures for a given league and season from API-Football from a given date range.
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
    
    if response.status_code != 200 or not response.json().get('response'):
        print(f"Error or no data: {response.status_code} - {response.text}")
        return 0
    
    return response.json().get('response', [])

def save_fixtures_to_db(league_id, season_year, start_date, end_date, split_date):    
    """
    Fetches and saves fixtures for a given league and season from API-Football from a given date range to the database.
    
    Args:
        league_id (int): The ID of the league (e.g., 106 for Ekstraklasa).
        season_year (int): The starting year of the season (e.g., 2023 for 2023-2024).
        start_date (str): The start date in "YYYY-MM-DD" format.
        end_date (str): The end date in "YYYY-MM-DD" format.
        split_date (str): The date simulating today in "YYYY-MM-DD" format - only in demo version without payment plan."""
    

    fixtures = fetch_fixtures(league_id, season_year, start_date, end_date)
    if not fixtures:
        return []

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
            
        Fixture.objects.update_or_create(
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

def run():
    """Entry point for django-extensions runscript."""

    # today = datetime.now().strftime('%Y-%m-%d')
    # start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')  
    # end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')    
    save_fixtures_to_db(league_id=106, season_year=2023, start_date="2023-09-01", end_date="2023-09-30", split_date="2023-09-20")