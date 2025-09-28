"""Script to fetch and save seasons from API-Football to the database.

Requires:
    requests: For HTTP requests to API-Football.
    python-decouple: For loading API key from .env.

Example:
    python manage.py runscript fetch_seasons
"""

import requests
from decouple import config
from predictions.models import Season, League


API_KEY = config('API_FOOTBALL_KEY')
API_URL = "https://v3.football.api-sports.io"

def fetch_seasons():
    """
    Fetches available seasons from API-Football.
    
    Returns:
        list: A list of seasons years (e.g. [2008, ..., 2027]) 
        Empty list if request fails.
    """
    
    headers = {'x-apisports-key': API_KEY}
    response = requests.get(f"{API_URL}/leagues/seasons", headers=headers)
    if response.status_code == 200:
        return response.json().get('response')
    else:
        print(f"Error fetching seasons: {response.status_code}")
        print(response.text)
        return []
    
def save_seasons_to_db():
    """ 
    Saves selected seasons (2021, 2022, 2023) to the database.
     
    Returns:
        None
    """

    leagues = League.objects.all()
    seasons = fetch_seasons()
    seasons = [year for year in seasons if year in [2021, 2022, 2023]]

    for league in leagues:
        for year in seasons:
            Season.objects.get_or_create(league=league, start_year=year, defaults={'year':f"{year}-{year+1}"})

def run():
    """Entry point for django-extensions runscript."""
    save_seasons_to_db()
