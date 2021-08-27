from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_200_OK

from htmltool.core import get_html_page, get_html_snippets
from .serializers import HtmlPageSerializer, HtmlSnippetsSerializer


class HtmlToolAPI(APIView):
    """
    API Class for getting html page file based on url.

    Needed query parameters:
        url (str): url of the page
    """
    def post(self, request):
        url = self.request.POST.get('url')

        serializer = HtmlPageSerializer(data={'url': url})

        if not serializer.is_valid():

            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        filename = get_html_page(url)

        return Response(
            {
                'filename': filename
            },
            status=HTTP_200_OK
        )


class HtmlSnippetAPI(APIView):
    """
    API Class for getting particular snippets in html code based on regular expressions.

    Needed query parameters:
        url (str): url of the site
        snippet (str): snippet with given expressions for scraping needed data
    """
    def post(self, request):
        url = self.request.POST.get('url')
        snippet = self.request.POST.get('snippet')
        post_render = True if self.request.POST.get('post-render') == 'true' else False

        serializer = HtmlSnippetsSerializer(data={'url': url, 'snippet': snippet, 'post_render': post_render})

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        response = get_html_snippets(
            url=url,
            snippet=snippet,
            post_render=post_render
        )

        return Response(response, status=HTTP_200_OK)
