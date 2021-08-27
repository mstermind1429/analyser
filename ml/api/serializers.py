from rest_framework import serializers


class CausalImpactSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    date = serializers.DateField()

