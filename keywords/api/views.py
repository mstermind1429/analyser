from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_406_NOT_ACCEPTABLE, HTTP_204_NO_CONTENT

from core.helpers import save_csv_file, get_access_token, get_keywords_phrase
from .serializers import (CategoryDomainSerializer, DomainSearchMetricsSerializer, ExampleKeywordSerializer,
                          SearchVolumeSerializer, KeywordSearchSerializer, KeywordDomainSerializer,
                          SearchVolumeCountSerializer, TagsBySearchVolumeSerializer, TrafficCountSerializer,
                          SearchmetricsToolSerializer)
from keywords.core import (KeywordsAnalysis, category_domain_task, get_example_url_keywords, get_group_keywords,
                           run_domain_searchmetrics_complete, run_domain_searchmetrics_simple, search_volume_task,
                           get_keyword_domain, get_similar_keywords, get_tags_by_search_volume, get_url_key_patterns,
                           get_url_searchmetrics)


class CategoryDomainAPI(APIView):
    """
    API Class for getting category domain

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
        date (datetime)
    """
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('file')
        key = request.POST.get('key')
        secret = request.POST.get('secret')
        country_code = request.POST.get('country_code')

        serializer = CategoryDomainSerializer(
            data={
                'csv_file': csv_file,
                'country_code': country_code,
                'key': key,
                'secret': secret
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        uploaded_file_url = save_csv_file(
            csv_file=csv_file,
            filename=f'{settings.REPORT_PATH}/category_domain.csv'
        ) if csv_file else None

        if uploaded_file_url:
            category_domain_task(
                uploaded_file_url=uploaded_file_url,
                key=key,
                secret=secret,
                country_code=country_code,
                schedule=0
            )
            return Response({}, status=HTTP_200_OK)
        else:
            return Response({}, status=HTTP_400_BAD_REQUEST)


class DomainSearchmetricsAnalysis(APIView):
    parser_classes = [MultiPartParser]
    """
    API Class for getting full search metrics analysis

    Needed query parameters:
        domain (str): domain of the url without http/https
        key (str): key for API
        secret (str): secret for API
        amount (int): amount of keywords needed
    """
    def post(self, request):
        domain = request.POST.get('domain')
        key = request.POST.get('key')
        secret = request.POST.get('secret')
        amount = int(request.POST.get('amount'))
        country_code = request.POST.get('country_code')
        analysis_type = int(request.POST.get('type'))

        serializer = DomainSearchMetricsSerializer(
            data=
            {
                'domain': domain,
                'key': key,
                'secret': secret,
                'amount': amount,
                'country_code': country_code,
                'analysis_type': analysis_type
            }
        )
        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        if analysis_type == 1:
            run_domain_searchmetrics_simple(
                key=key,
                secret=secret,
                amount=amount,
                country_code=country_code,
                domain=domain,
                schedule=1
            )
        else:
            run_domain_searchmetrics_complete(
                key=key,
                secret=secret,
                amount=amount,
                country_code=country_code,
                domain=domain,
                schedule=1
            )
        return Response(status=HTTP_204_NO_CONTENT)


class ExampleKeywordsAPI(APIView):
    """
    API Class for getting example keywords

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
    """
    parser_classes = [MultiPartParser]

    def put(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv')
        sort_type = request.POST.get('sort')
        exclude = request.POST.get('exclude')

        serializer = ExampleKeywordSerializer(
            data=
            {
                'csv_file': csv_file,
                'sort_type': int(sort_type),
                'exclude': exclude
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        exclude_inner = exclude.split()

        if sort_type == 'Traffic Index':
            limit = int(request.POST.get('traffic-limit'))
            sort_label = 'traffic'
        else:
            limit = int(request.POST.get('search-limit'))
            sort_label = 'search'

        analysis = KeywordsAnalysis(
            csv_file=csv_file,
            filename="example_keywords",
            exclude_words=exclude_inner,
            analysis=sort_label,
            limit=limit
        )
        analysis.set_df()
        analysis.process_words_dict()
        analysis.sort()

        filename = analysis.save(table=False, example_keywords=True)
        return Response({'filename': filename}, status=HTTP_200_OK)


class ExampleURLKeywordsAPI(APIView):
    """
    API Class for getting example keywords for each directory

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
    """
    parser_classes = [MultiPartParser]

    def put(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv')
        sort_type = request.POST.get('sort')
        exclude = request.POST.get('exclude')

        serializer = ExampleKeywordSerializer(
            data=
            {
                'csv_file': csv_file,
                'sort_type': int(sort_type),
                'exclude': exclude
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        exclude_inner = exclude.split()

        if sort_type == 'Traffic Index':
            limit = int(request.POST.get('traffic-limit'))
            sort_label = 'traffic'
        else:
            limit = int(request.POST.get('search-limit'))
            sort_label = 'search'

        uploaded_file_url = save_csv_file(csv_file, 'example_url.csv')

        filename = get_example_url_keywords(
            uploaded_file_url,
            sort_type=sort_type,
            sort_label=sort_label,
            limit=limit,
            exclude_inner=exclude_inner
        )

        return Response(
            {
                'filename': filename
            },
            status=HTTP_200_OK
        )


class GetSearchVolumeAPI(APIView):
    """
    API Class for getting search volume of the keywords

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
        key (string): api key
        secret (string): api secret
    """
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv')
        api_key = request.POST.get('key')
        api_secret = request.POST.get('secret')
        country_code = request.POST.get('country_code')

        serializer = SearchVolumeSerializer(
            data=
            {
                'csv_file': csv_file,
                'key': api_key,
                'secret': api_secret,
                'country_code': country_code
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        uploaded_file_url = save_csv_file(
            csv_file=csv_file,
            filename='search_volume.csv'
        )

        search_volume_task(
            uploaded_file_url,
            country_code,
            key=api_key,
            secret=api_secret,
            schedule=1,
            repeat=None
        )
        return Response({}, status=HTTP_204_NO_CONTENT)


class KeywordSearchAPI(APIView):
    """
    API Class for categorizing keywords into groups.

    Needed query parameters:
        csv_file (file): file of the .csv format with title and keyword columns
    """
    parser_classes = [MultiPartParser]

    def put(self, request):
        csv_file = request.FILES.get('csv')
        group_1 = request.POST.get('group1')
        group_2 = request.POST.get('group2')

        serializer = KeywordSearchSerializer(
            data=
            {
                'csv_file': csv_file,
                'group_1': group_1,
                'group_2': group_2
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        uploaded_file_url = save_csv_file(
            csv_file=csv_file,
            filename='keyword_search.csv'
        )

        filename, time_spent = get_group_keywords(
            uploaded_file_url,
            group_1=group_1,
            group_2=group_2
        )

        return Response(
            {
                'filename': filename,
                'time': time_spent
            },
            status=HTTP_200_OK
        )


class KeywordDomain(APIView):
    """
    API Class for getting keyword domain overview

    Needed query parameters:
        phrase (str): phrase
        key (str): key for API
        secret (str): secret for API
        amount (int): amount of keywords needed
    """
    def post(self, request):
        serializer = KeywordDomainSerializer(self.request.POST)
        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        access_token = get_access_token(serializer.key, serializer.secret)

        success, data = get_keywords_phrase(
            access_token=access_token,
            phrase=serializer.phrase,
            country_code=serializer.country_code
        )

        if not success:
            return Response(status=HTTP_400_BAD_REQUEST)

        filename = get_keyword_domain(
            data=data,
            access_token=access_token,
            country_code=serializer.country_code
        )

        return Response(
            {
                'filename': f"/reports/{filename}"
            },
            status=HTTP_200_OK
        )


class SearchCountAPI(APIView):
    """
    API Class for getting search volume of the keywords

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
    """
    parser_classes = [MultiPartParser]

    def put(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv')
        search_limit = int(request.POST.get('search-limit'))
        exclude = request.POST.get('exclude')

        serializer = SearchVolumeCountSerializer(
            data={
                'csv_file': csv_file,
                'search_limit': search_limit,
                'exclude': exclude
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        exclude_inner = exclude.split()
        analysis = KeywordsAnalysis(
            csv_file=csv_file,
            filename="search",
            exclude_words=exclude_inner,
            analysis="search",
            limit=search_limit
        )
        analysis.set_df()
        analysis.process_words_dict()
        analysis.sort()

        filename = analysis.save(table=True)
        list_filename = analysis.save(table=False)

        return Response(
            {
                'filename': filename,
                'list_filename': list_filename
            },
            status=HTTP_200_OK
        )


class SimilarKeywordsAPI(APIView):
    """
    API Class for getting similar keywords

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
    """
    parser_classes = [MultiPartParser]

    def put(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv')
        sort_type = request.POST.get('sort')
        exclude = request.POST.get('exclude')

        serializer = ExampleKeywordSerializer(
            data=
            {
                'csv_file': csv_file,
                'sort_type': int(sort_type),
                'exclude': exclude
            }
        )
        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        exclude_inner = []
        for exclude_word in exclude.split():
            exclude_inner.append(exclude_word)

        if sort_type == 'Traffic Index':
            limit = int(request.POST['traffic-limit'])
            sort_label = 'by_traffic'
        else:
            limit = int(request.POST['search-limit'])
            sort_label = 'by_search_volume'

        uploaded_file_url = save_csv_file(csv_file, 'similar.csv')

        filename = get_similar_keywords(
            uploaded_file_url=uploaded_file_url,
            sort_type=sort_type,
            sort_label=sort_label,
            limit=limit
        )

        return Response({'filename': filename}, status=HTTP_200_OK)


class SearchMetricsAPI(APIView):
    """
    API Class for getting tags from keywords sorted by search volume

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
    """
    parser_classes = [MultiPartParser]

    def put(self, request):
        csv_file = request.FILES.get('csv')

        serializer = TagsBySearchVolumeSerializer(
            data=
            {
                'csv_file': csv_file
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        uploaded_file_url = save_csv_file(csv_file, 'search-metrics.csv')
        filename = get_tags_by_search_volume(
            uploaded_file_url=uploaded_file_url
        )

        return Response(
            {
                'filename': filename
            },
            status=HTTP_200_OK
        )


class TrafficCountAPI(APIView):
    """
    API Class for getting traffic index of the keywords

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
    """
    parser_classes = [MultiPartParser]

    def put(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv')
        traffic_limit = int(request.POST.get('traffic-limit'))
        exclude = request.POST.get('exclude')

        serializer = TrafficCountSerializer(
            data=
            {
                'csv_file': csv_file,
                'traffic_limit': traffic_limit,
                'exclude': exclude
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        exclude_inner = exclude.split()
        analysis = KeywordsAnalysis(
            csv_file=csv_file,
            filename="traffic",
            exclude_words=exclude_inner,
            analysis="traffic",
            limit=traffic_limit
        )
        analysis.set_df()
        analysis.process_words_dict()
        analysis.sort()

        filename = analysis.save(table=True)
        list_filename = analysis.save(table=False)

        return Response(
            {
                'filename': filename,
                'list_filename': list_filename
            },
            status=HTTP_200_OK
        )


class KeyPatternExtractionAPI(APIView):
    """
    API Class for getting key (important) patterns based on the set of urls:
    directories, subdomains, extensions, url parameters and values

    Needed query parameters:
        csv_file (file): file of the .csv format with column of urls named URL
    """
    parser_classes = [MultiPartParser]

    def put(self, request):
        csv_file = request.FILES.get('csv')

        serializer = TagsBySearchVolumeSerializer(
            data=
            {
                'csv_file': csv_file
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        uploaded_file_url = save_csv_file(csv_file, 'key_patterns.csv')
        filename, time_spent = get_url_key_patterns(uploaded_file_url=uploaded_file_url)
        return Response(
            {
                'filename': filename,
                'time': time_spent
            },
            status=HTTP_200_OK
        )


class SearchMetricsToolAPI(APIView):
    """
    API Class for getting full search metrics analysis

    Needed query parameters:
        domain (str): domain of the url withour http/https
        key (str): key for API
        secret (str): secret for API
        amount (int): amount of keywords needed
        date_from (str): the initial date
        date_to (str): the final date
    """
    def post(self, request):
        domain = request.POST.get('domain')
        key = request.POST.get('key')
        secret = request.POST.get('secret')
        amount = int(request.POST.get('amount'))
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')

        serializer = SearchmetricsToolSerializer(data=request.POST)

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        status, response = get_url_searchmetrics(
            date_from=date_from,
            date_to=date_to,
            amount=amount,
            domain=domain,
            key=key,
            secret=secret
        )

        if not status:
            return Response({'error_message': response}, status=503)

        return Response(response, status=HTTP_200_OK)


class WordsCountAPI(APIView):
    """
    API Class for getting words combinations count based on set of keywords

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
    """
    parser_classes = [MultiPartParser]

    def put(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv')
        count_limit = int(request.POST.get('count-limit'))
        exclude = request.POST.get('exclude')

        serializer = TrafficCountSerializer(
            data=
            {
                'csv_file': csv_file,
                'traffic_limit': count_limit,
                'exclude': exclude
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        exclude_inner = exclude.split()
        analysis = KeywordsAnalysis(
            csv_file=csv_file,
            filename="count",
            exclude_words=exclude_inner,
            analysis="count",
            limit=count_limit
        )
        analysis.set_df()
        analysis.process_words_dict()
        analysis.sort()

        filename = analysis.save(table=True)
        list_filename = analysis.save(table=False)

        return Response(
            {
                'filename': filename,
                'list_filename': list_filename
            },
            status=HTTP_200_OK
        )

