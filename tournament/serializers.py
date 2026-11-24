from rest_framework import serializers
from django.contrib.auth.models import User
from tournament.models import TournamentDb,TournamentMemberDb,TeamDb,TeamMemberDb,MatchDb
from django.db import transaction


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=100,write_only=True)
    class Meta:
        model = User
        fields = ['id','username','email','password']
        read_only_fields = ['id']
    
    def create(self,validated_data):
        return User.objects.create_user(**validated_data)

class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentDb
        fields = '__all__'
        read_only_fields = ['id','created_by','created_at','updated_at']

class TournamentMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    participant_username = serializers.CharField(source='user.username',read_only=True)
    participant_user_id = serializers.IntegerField(source='user.id',read_only=True)
    tournament_title = serializers.CharField(source='tournament.tournament_title',read_only=True)

    class Meta:
        model = TournamentMemberDb
        fields = ['id','tournament_title','username','participant_username','participant_user_id','joined_at']
        read_only_fields = ['id','joined_at']
    
    def validate(self,data):
        username = data.get('username')
        user = User.objects.filter(username=username).first()
        tournament = self.context['tournament']
        if user is None:
            raise serializers.ValidationError('No registered participant exist')
        if tournament.created_by == user:
            raise serializers.ValidationError('Owner cant be added as a participant')
        if TournamentMemberDb.objects.filter(user=user,tournament=tournament).exists():
            raise serializers.ValidationError('This participant is already added')
        participant_count = TournamentMemberDb.objects.filter(tournament=tournament).count()
        if participant_count >= tournament.participant_limit:
            raise serializers.ValidationError('Number of participant have reached')
        return data
        
    def create(self,validated_data):
        username = validated_data.pop('username')
        user = User.objects.get(username=username)
        tournament = self.context['tournament']
        return TournamentMemberDb.objects.create(tournament=tournament,user=user)

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamDb
        fields = '__all__'
        read_only_fields = ['id','created_by','created_at','tournament']
    
    def validate(self,data):
        team_name = data.get('team_name')
        user = self.context['created_by']
        tournament = self.context['tournament']

        if tournament.tournament_type != 'team':
            raise serializers.ValidationError("Teams can only be created in team-based tournaments")
        if not self.instance:
            if TeamDb.objects.filter(tournament=tournament,created_by=user).exists():
                raise serializers.ValidationError("You have already created a team")
        existing_team = TeamDb.objects.filter(team_name__iexact=team_name,tournament=tournament)
        if self.instance:
            existing_team = existing_team.exclude(id=self.instance.id)
        if existing_team.exists():
            raise serializers.ValidationError("This team name is already used")
        return data
        
    def create(self, validated_data):
        with transaction.atomic():
            team = TeamDb.objects.create(**validated_data)
            TeamMemberDb.objects.create(team=team,user=team.created_by)
        return team

class TeamMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    member_username = serializers.CharField(source='user.username',read_only=True)
    member_user_id = serializers.IntegerField(source='user.id',read_only=True)
    team_name = serializers.CharField(source='team.team_name',read_only=True)

    class Meta:
        model = TeamMemberDb
        fields = ['id','team_name','username','member_username','member_user_id','joined_at']
        read_only_fields = ['id','joined_at']

    def validate(self,data):
        username = data.get('username')
        user = User.objects.filter(username=username).first()
        team = self.context['team']

        if user is None:
            raise serializers.ValidationError('Not a registered user')
        if team.created_by == user:
            raise serializers.ValidationError('Team owner is already a member')
        if TeamMemberDb.objects.filter(team=team,user=user).exists():
            raise serializers.ValidationError('This user is already a member of this team')
        if TeamMemberDb.objects.filter(user=user,team__tournament=team.tournament).exists():
            raise serializers.ValidationError('This user is already a member of another team in this tournament')
        return data

    def create(self, validated_data):
        username = validated_data.pop('username')
        user = User.objects.get(username=username)
        team = self.context['team']
        return TeamMemberDb.objects.create(team=team,user=user)

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model =MatchDb
        fields ='__all__'
        read_only_fields = ['id','tournament','score1','score2','winner_player','winner_team','status','created_at']

    def validate(self, data):
        tournament = self.context['tournament']
        team1 = data.get('team1')
        team2 = data.get('team2')
        player1 = data.get('player1')
        player2 = data.get('player2')

        if tournament.tournament_type == 'team':
            if player1 or player2:
                raise serializers.ValidationError("Player fields are not allowed in team tournaments")
            if team1.tournament != tournament or team2.tournament != tournament:
                raise serializers.ValidationError("Both teams must be registered to this tournament")
            if MatchDb.objects.filter(tournament=tournament,round=data.get('round'),team1=team1).exists() or MatchDb.objects.filter(tournament=tournament,round=data.get('round'),team2=team1).exists():
                raise serializers.ValidationError("This team is already assigned to a match in this round")
            if MatchDb.objects.filter(tournament=tournament,round=data.get('round'),team1=team2).exists() or MatchDb.objects.filter(tournament=tournament,round=data.get('round'),team2=team2).exists():
                raise serializers.ValidationError("This team is already assigned to a match in this round")
            if team1 == team2:
                raise serializers.ValidationError("Both participants teams are same")

        elif tournament.tournament_type == 'individual':
            if team1 or team2:
                raise serializers.ValidationError("Team fields are not allowed in individual tournaments")
            if not TournamentMemberDb.objects.filter(tournament=tournament,user=player1).exists() or not TournamentMemberDb.objects.filter(tournament=tournament,user=player2).exists():
                raise serializers.ValidationError("Both players must be registered in this tournament")
            if MatchDb.objects.filter(tournament=tournament,round=data.get('round'),player1=player1).exists() or MatchDb.objects.filter(tournament=tournament,round=data.get('round'),player2=player1).exists():
                raise serializers.ValidationError("This player is already assigned to a match in this round")
            if MatchDb.objects.filter(tournament=tournament,round=data.get('round'),player1=player2).exists() or MatchDb.objects.filter(tournament=tournament,round=data.get('round'),player2=player2).exists():
                raise serializers.ValidationError("This player is already assigned to a match in this round")
            if player1 == player2:
                raise serializers.ValidationError("Both participants players are same")
        
        return data

class MatchResultSerializer(serializers.ModelSerializer):
    score1 = serializers.IntegerField(min_value=0)
    score2 = serializers.IntegerField(min_value=0)

    class Meta:
        model = MatchDb
        fields = '__all__'
        read_only_fields = ['id','tournament','team1','team2','player1','player2','round','match_date','match_time','winner_player','winner_team','status','created_at']

    def validate(self,data):
        if data['score1'] == data['score2']:
            raise serializers.ValidationError('Match shouldnt be end in draw')
        return data

    def update(self,instance,validated_data):
        instance.score1 = validated_data['score1']
        instance.score2 = validated_data['score2']
        if instance.tournament.tournament_type == 'team':
            if instance.score1 > instance.score2:
                instance.winner_team = instance.team1
            else:
                instance.winner_team = instance.team2
        else:
            if instance.score1 > instance.score2:
                instance.winner_player = instance.player1
            else:
                instance.winner_player = instance.player2
        instance.status = 'completed'
        instance.save()
        return instance