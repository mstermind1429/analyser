from django.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_406_NOT_ACCEPTABLE, HTTP_200_OK

from alighthouse.core import run_domain_lighthouse, lighthouse_report
from core.helpers import save_csv_file
from .serializers import DomainLighthouseSerializer, LighthouseReportSerializer


class DomainLighthouseAnalysis(APIView):
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
        domains = request.POST.get('domains')
        key = request.POST.get('key')
        secret = request.POST.get('secret')
        amount = int(request.POST.get('amount'))
        country_code = request.POST.get('country_code')
        file = request.FILES.get('file')

        serializer = DomainLighthouseSerializer(
            data=
            {
                'file': file,
                'key': key,
                'secret': secret,
                'amount': amount,
                'country_code': country_code,
                'domains': domains
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        uploaded_file_url = save_csv_file(file,
                                          f'{settings.REPORT_PATH}/domain_lighthouse.xlsx') if file else None

        for domain in domains.splitlines():
            run_domain_lighthouse(
                key=key,
                secret=secret,
                amount=amount,
                country_code=country_code,
                domain=domain,
                uploaded_file_url=uploaded_file_url,
                schedule=1
            )

        return Response({}, status=HTTP_204_NO_CONTENT)


class ReportAPI(APIView):
    """
    API Class for getting Google Lighthouse Report.

    Needed query parameters:
        url (str): url of the site to get report of
    """
    def get(self, request):
        url = self.request.query_params.get('url')

        serializer = LighthouseReportSerializer(data={'url': url})

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        serializer = lighthouse_report(url)
        return Response(serializer, status=HTTP_200_OK)
