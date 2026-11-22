from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from tournament.serializers import UserSerializer,TournamentSerializer,TournamentMemberSerializer,TeamSerializer
from tournament.models import TournamentDb,TournamentMemberDb,TeamDb
from rest_framework import authentication,permissions,serializers
from tournament.permissions import OwnerOnly
from rest_framework.exceptions import PermissionDenied


# Create your views here.
class RegisterUserView(APIView):
    def post(self,request):
        user = request.data
        serializer_instance = UserSerializer(data=user)
        if serializer_instance.is_valid():
            serializer_instance.save()
            return Response({"Message":"User Registered Successfully"})
        else:
            return Response(data=serializer_instance.errors)

class UsersListView(APIView):
    def get(self,request):
        user = User.objects.all()
        serializer_instance = UserSerializer(user,many=True)
        return Response(data=serializer_instance.data)

class TournamentView(APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [OwnerOnly]

    def get(self,request):
        tournament = TournamentDb.objects.filter(created_by=request.user)
        serializer_instance = TournamentSerializer(tournament,many=True)
        return Response(data=serializer_instance.data)

    def post(self,request):
        tournament = request.data
        serializer_instance = TournamentSerializer(data=tournament)
        if serializer_instance.is_valid():
            serializer_instance.save(created_by=request.user)
            return Response({"Message":"Tournament created successfully",
                            "Tournament Details":serializer_instance.data})
        else:
            return Response(data=serializer_instance.errors)

class TournamentRetrieveUpdateDeleteView(APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [OwnerOnly]
    
    def get(self,request,pk):
        tournament_object = get_object_or_404(TournamentDb,id=pk)
        serializer_instance = TournamentSerializer(tournament_object)
        if tournament_object.created_by != request.user:
            raise serializers.ValidationError('You dont have access to this')
        return Response(data=serializer_instance.data)
    
    def put(self,request,pk):
        tournament = request.data
        tournament_object = get_object_or_404(TournamentDb,id=pk)
        if tournament_object.created_by != request.user:
            raise serializers.ValidationError('You cant access this')
        serializer_instance = TournamentSerializer(data=tournament,instance=tournament_object)
        if serializer_instance.is_valid():
            serializer_instance.save()
            return Response({"Message":"Tournament Updated Successfully",
                            "Updated Tournament Details":serializer_instance.data})
        else:
            return Response(data=serializer_instance.errors)

    def delete(self,request,pk):
        tournament_object = get_object_or_404(TournamentDb,id=pk)
        if tournament_object.created_by != request.user:
            raise serializers.ValidationError('You are not the owner')
        tournament_object.delete()
        return Response({"Message":"Tournament Successfully Deleted"})

class TournamentParticipantView(APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self,request,tournament_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        is_owner = tournament_object.created_by == request.user 
        is_participant = TournamentMemberDb.objects.filter(tournament=tournament_object,user=request.user).exists() 
       
        if not (is_owner or is_participant):
         raise PermissionDenied("You cant access this tournament")
        participant = TournamentMemberDb.objects.filter(tournament=tournament_object)
        serializer_instance = TournamentMemberSerializer(participant,many=True)
        return Response(data=serializer_instance.data)
    
    def post(self,request,tournament_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        if tournament_object.created_by != request.user:
            raise PermissionDenied('Only Tournament Owner Can Add Participants')
        serializer_instance = TournamentMemberSerializer(data=request.data,context={'tournament' : tournament_object})
        if serializer_instance.is_valid():
            serializer_instance.save()
            return Response({"Message":"Participant Added Successfully"})
        else:
            return Response(data=serializer_instance.errors)

class TournamentParticipantDeleteView(APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [OwnerOnly]

    def delete(self,request,tournament_id,participant_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        if tournament_object.created_by != request.user:
            raise PermissionDenied('Only tournament owner can remove participnts')
        participant_object = get_object_or_404(TournamentMemberDb,id=participant_id,tournament=tournament_object)
        participant_object.delete()
        return Response({'Message':'Participant removed successfully'})
    
class TeamListCreateView(APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [OwnerOnly]

    def get(self,request,tournament_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        if tournament_object.created_by != request.user:
            raise PermissionDenied("Only tournament owner can view teams")
        team = TeamDb.objects.filter(tournament=tournament_object)
        serializer_instance = TeamSerializer(team,many=True)
        return Response(data=serializer_instance.data)
    
    def post(self,request,tournament_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        serializer_instance = TeamSerializer(data=request.data,context={'tournament' : tournament_object,'created_by' : request.user})
        if serializer_instance.is_valid():
            serializer_instance.save(tournament=tournament_object,created_by=request.user)
            return Response({"Message":"Team Successfully created"})
        else:
            return Response(data=serializer_instance.errors)

class TeamRetrieveUpdateDelete(APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self,request,tournament_id,team_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        if tournament_object.created_by != request.user:
            raise PermissionDenied("Only tournament owner can view teams")
        team = get_object_or_404(TeamDb,id=team_id,tournament=tournament_object)
        serializer_instance = TeamSerializer(team)
        return Response(data=serializer_instance.data)
    
    def put(self,request,tournament_id,team_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        team_object = get_object_or_404(TeamDb,id=team_id,tournament=tournament_object)
        if team_object.created_by != request.user:
            raise PermissionDenied('Only team creator can update the team')
        serializer_instance = TeamSerializer(data=request.data,instance=team_object,context={'tournament': tournament_object,'created_by' : request.user})
        if serializer_instance.is_valid():
            serializer_instance.save()
            return Response({"Message":"Team updated successfully"})
        else:
            return Response(data=serializer_instance.errors)

    def delete(self,request,tournament_id,team_id):
        tournament_object = get_object_or_404(TournamentDb,id=tournament_id)
        team_object = get_object_or_404(TeamDb,id=team_id,tournament=tournament_object)
        if team_object.created_by != request.user:
            raise PermissionDenied('Only team creator can delete the team')
        team_object.delete()
        return Response({"Message":"Team successfully deleted"})