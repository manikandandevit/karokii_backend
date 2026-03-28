from rest_framework import serializers

from .models import SeparationJob


class SeparationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeparationJob
        fields = ["id", "status", "error_message", "metadata", "created_at", "updated_at"]


class CreateJobSerializer(serializers.Serializer):
    file = serializers.FileField()


class MixRequestSerializer(serializers.Serializer):
    stems = serializers.ListField(
        child=serializers.ChoiceField(choices=["vocals", "drums", "bass", "other", "instrumental", "music"]),
        allow_empty=False,
    )
    output_name = serializers.CharField(required=False, allow_blank=True, max_length=128)
