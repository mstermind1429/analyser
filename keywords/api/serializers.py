from rest_framework import serializers


class DomainSearchMetricsSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=512)
    key = serializers.CharField(max_length=1024)
    secret = serializers.CharField(max_length=1024)
    amount = serializers.IntegerField()
    country_code = serializers.CharField(max_length=3)
    analysis_type = serializers.IntegerField()


class ExampleKeywordSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    sort_type = serializers.IntegerField()
    exclude = serializers.CharField(max_length=1024)


class SearchVolumeSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    key = serializers.CharField(max_length=1024)
    secret = serializers.CharField(max_length=1024)
    country_code = serializers.CharField(max_length=3)


class KeywordSearchSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    group_1 = serializers.CharField(max_length=4096)
    group_2 = serializers.CharField(max_length=4096)


class SearchVolumeCountSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    search_limit = serializers.IntegerField()
    exclude = serializers.CharField(max_length=2048)


class TagsBySearchVolumeSerializer(serializers.Serializer):
    csv_file = serializers.FileField()


class TrafficCountSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    traffic_limit = serializers.IntegerField()
    exclude = serializers.CharField(max_length=2048)


class SearchmetricsToolSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=1024)
    key = serializers.CharField(max_length=2048)
    secret = serializers.CharField(max_length=2048)
    amount = serializers.IntegerField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()


class CategoryDomainSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    key = serializers.CharField(max_length=2048)
    secret = serializers.CharField(max_length=2048)
    country_code = serializers.CharField(max_length=3)


class KeywordDomainSerializer(serializers.Serializer):
    phrase = serializers.CharField(max_length=1024)
    key = serializers.CharField(max_length=2048)
    secret = serializers.CharField(max_length=2048)
    country_code = serializers.CharField(max_length=3)