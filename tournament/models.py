from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class TournamentDb(models.Model):
    tournament_title = models.CharField(max_length=100)
    type_choices = [('team','Team'),('individual','Individual')]
    tournament_type = models.CharField(max_length=30,choices=type_choices)
    tournament_format = models.CharField(max_length=100,default='single elimination')
    participant_limit = models.PositiveIntegerField()
    date = models.DateField()
    location = models.CharField(max_length=100)
    status_choices = [('upcoming','Upcoming'),('ongoing','Ongoing'),('completed','Completed')]
    status = models.CharField(max_length=100,choices=status_choices,default='upcoming')
    tournament_winner = models.CharField(max_length=100,null=True,blank=True)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tournament_title

class TournamentMemberDb(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='tournament_participants')
    tournament = models.ForeignKey(TournamentDb,on_delete=models.CASCADE,related_name='tournament_details')
    joined_at = models.DateTimeField(auto_now_add = True)
    
    class Meta:
        constraints = [models.UniqueConstraint(fields=['tournament','user'],name='unique_tournament_participant')]

    def __str__(self):
        return f"{self.user.username} - {self.tournament.tournament_title}"

class TeamDb(models.Model):
    team_name = models.CharField(max_length=100)
    tournament = models.ForeignKey(TournamentDb,on_delete=models.CASCADE)
    created_by = models.ForeignKey(User,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.team_name
    
class TeamMemberDb(models.Model):
    team = models.ForeignKey(TeamDb,on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(
                        fields=['team', 'user'],
                        name='unique_team_member')
                    ]
    
    def __str__(self):
        return f"{self.user.username} - {self.team.team_name}"
