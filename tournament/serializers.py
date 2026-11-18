from rest_framework import serializers
from django.contrib.auth.models import User
from tournament.models import TournamentDb,TournamentMemberDb


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