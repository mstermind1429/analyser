from rest_framework import serializers


class DomainLighthouseSerializer(serializers.Serializer):
    domains = serializers.CharField(max_length=4096)
    key = serializers.CharField(max_length=2048)
    secret = serializers.CharField(max_length=2048)
    amount = serializers.IntegerField()
    country_code = serializers.CharField(max_length=3)
    file = serializers.FileField()


class LighthouseReportSerializer(serializers.Serializer):
    url = serializers.URLField()
