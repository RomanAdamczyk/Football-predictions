STATUS_CHOICES = [
    ('NS', 'zaplanowany'),
    ('1H', '1 połowa'),
    ('HT', 'przerwa'),
    ('2H', '2 połowa'),
    ('LIVE', 'trwa'),
    ('FT', 'zakończony'),
    ('PST', 'przełożony'),
    ('CANC', 'odwołany'),
]

from django.contrib.auth.models import User
from django.db import models


#class Country(models.Model): UZUPEŁNIĆ
class League(models.Model):
    """ Represents a football league.
    
    Attributes:
        name (str): The name of the league.
        country (str): The country where the league is based.
        level (int): The level of the league (e.g., 1 for top-tier leagues).
        api_id (int): Unique identifier from the external API.
    """

    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    level = models.IntegerField()
    api_id = models.IntegerField(unique=True)

    def __str__(self):
        return f"{self.country} {self.name}"
    
class Season(models.Model):
    """
    Represents a football season within a league.
    
    Attributes:
        league (ForeignKey): The league to which the season belongs.
        year (str): The season year in the format "YYYY-YYYY".
        start_year (int): The starting year of the season.
    
    Meta:
        unique_together: Ensures that each league can have only one season per starting year.
    """

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='seasons')
    year = models.CharField(max_length=9)  # walidacja ze start_year f"{start_year}-{start_year+1}"
    start_year = models.IntegerField() 

    class Meta:
        unique_together = ('league', 'start_year')

    def __str__(self):
        return f"{self.league.name} {self.year}"
    
class Team(models.Model):
    """
    Represents a football team.
    
    Attributes:
        name (str): The name of the team.
        season (ManyToManyField): The seasons in which the team has participated.
        api_id (int): Unique identifier from the external API.
    """

    name = models.CharField(max_length=100)
    season = models.ManyToManyField(Season, related_name='teams')
    api_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.name
    
class Fixture(models.Model):
    """ Represents a football match (fixture) between two teams.
    
    Attributes:
        season (ForeignKey): The season in which the fixture takes place.
        date (DateTimeField): The date and time of the fixture.
        home_team (ForeignKey): The home team.
        away_team (ForeignKey): The away team.
        home_score (IntegerField): The score of the home team (nullable).
        away_score (IntegerField): The score of the away team (nullable).
        api_id (IntegerField): Unique identifier from the external API.
        status (CharField): The current status of the fixture, with choices defined in STATUS_CHOICES.
        round (IntegerField): The round number of the fixture (nullable).
        round_name (CharField): The name of the round (nullable).
    
    Meta:
        indexes: Defines database indexes for optimized queries."""
    
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='fixtures')
    date = models.DateTimeField()
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    api_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NS')
    round = models.IntegerField(null=True, blank=True)
    round_name = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['api_id','status']),
            models.Index(fields=['status']),
            models.Index(fields=['season', 'round']),
        ] 

    def __str__(self):
        return f"{self.home_team.name} {self.home_score or '-'} vs {self.away_score or '-'} {self.away_team.name} on {self.date}"
    
class UserGroup(models.Model):
    """
    Represents a group of users for making predictions.
    
    Attributes:
        name (str): The name of the user group.
        members (ManyToManyField): The users who are members of the group.
        access_code (str): A unique code for accessing the group.
        description (str): A description of the group (optional).
        start_date (DateField): The start date of the group (optional).
        end_date (DateField): The end date of the group (optional).
        season (ForeignKey): The season associated with the group (optional).
        admin (ForeignKey): The user who administers the group (optional).
        created_at (DateTimeField): The timestamp when the group was created.
        start_round (IntegerField): The starting round for predictions (optional).
        end_round (IntegerField): The ending round for predictions (optional).
        """
    
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='user_groups')
    access_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_groups')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='administered_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    start_round = models.IntegerField(null=True, blank=True)
    end_round = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class Prediction(models.Model):
    """
    Represents a user's prediction for a specific fixture within a user group.
    
    Attributes:
        user (ForeignKey): The user making the prediction.
        fixture (ForeignKey): The fixture for which the prediction is made.
        predicted_home_score (IntegerField): The predicted score for the home team.
        predicted_away_score (IntegerField): The predicted score for the away team.
        created_at (DateTimeField): The timestamp when the prediction was created.
        user_group (ForeignKey): The user group to which the prediction belongs.
        points_awarded (IntegerField): The points awarded for the prediction (default is 0).
        
    Meta:
        unique_together: Ensures that a user can make only one prediction per fixture within a user group.
        indexes: Defines database indexes for optimized queries.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='predictions')
    predicted_home_score = models.IntegerField()
    predicted_away_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='predictions')
    points_awarded = models.IntegerField(default=None, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'user_group','fixture')
        indexes = [
            models.Index(fields=['user_group', 'fixture']),
            models.Index(fields=['user', 'user_group']),
        ]

    def calculate_points(self):
        """
        Calculates points for the prediction based on the actual fixture result.
        
        Scoring System:
            - Exact score prediction: 3
            - Correct outcome (win/loss/draw) but wrong score: 1
            - Incorrect outcome: 0
        Updates the points_awarded attribute and saves the instance.
        """
        fixture = self.fixture
        if fixture.home_score is not None and fixture.away_score is not None:
            if (self.predicted_home_score == fixture.home_score and
                self.predicted_away_score == fixture.away_score):
                self.points_awarded = 3
            elif ((self.predicted_home_score - self.predicted_away_score) *
                  (fixture.home_score - fixture.away_score) > 0 or
                  (self.predicted_home_score == self.predicted_away_score and
                   fixture.home_score == fixture.away_score)):
                self.points_awarded = 1
            else:
                self.points_awarded = 0
            self.save()    

    def __str__(self):
        return f"{self.user.username}'s prediction: {self.predicted_home_score}-{self.predicted_away_score} for {self.fixture}"
