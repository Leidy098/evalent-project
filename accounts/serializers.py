from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(write_only=True, default="candidate")
    experience_level = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "role", "experience_level"]

    def create(self, validated_data):
        role = validated_data.pop("role", "candidate")
        experience_level = validated_data.pop("experience_level", "")
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        Profile.objects.create(user=user, role=role, experience_level=experience_level)
        return user
