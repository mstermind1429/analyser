from rest_framework import serializers


class HtmlSnippetsSerializer(serializers.Serializer):
    url = serializers.URLField()
    snippet = serializers.CharField(max_length=8192)
    post_render = serializers.BooleanField()


class HtmlPageSerializer(serializers.Serializer):
    url = serializers.URLField()
