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

class League(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    level = models.IntegerField()
    api_id = models.IntegerField(unique=True)

    def __str__(self):
        return f"{self.country} {self.name}"
    
class Season(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='seasons')
    year = models.CharField(max_length=9)  # walidacja ze start_year f"{start_year}-{start_year+1}"
    start_year = models.IntegerField() 

    class Meta:
        unique_together = ('league', 'start_year')

    def __str__(self):
        return f"{self.league.name} {self.year}"
    
class Team(models.Model):
    name = models.CharField(max_length=100)
    season = models.ManyToManyField(Season, related_name='teams')
    api_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.name
    
class Fixture(models.Model):
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='predictions')
    predicted_home_score = models.IntegerField()
    predicted_away_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    user_group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='predictions')
    points_awarded = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'user_group','fixture')
        indexes = [
            models.Index(fields=['user_group', 'fixture']),
            models.Index(fields=['user', 'user_group']),
        ]

    def __str__(self):
        return f"{self.user.username}'s prediction: {self.predicted_home_score}-{self.predicted_away_score} for {self.fixture}"
