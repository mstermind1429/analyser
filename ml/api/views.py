from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_406_NOT_ACCEPTABLE

from core.helpers import save_csv_file
from .serializers import CausalImpactSerializer
from ml.core import get_casual_impact_reports


class CasualImpactAPI(APIView):
    """
    API Class for getting casual impact

    Needed query parameters:
        csv_file (file): file of the .csv format with column of keywords
        date (datetime)
    """
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('file')
        date = request.POST.get('impact_date')

        serializer = CausalImpactSerializer(
            data=
            {
                'csv_file': csv_file,
                'date': date
            }
        )

        if not serializer.is_valid():
            return Response(serializer.error_messages,
                            status=HTTP_406_NOT_ACCEPTABLE)

        uploaded_file_url = save_csv_file(
            csv_file=csv_file,
            filename=f'{settings.REPORT_PATH}/casual_impact.csv'
        ) if csv_file else None

        if uploaded_file_url:
            get_casual_impact_reports(
                uploaded_file_url=uploaded_file_url,
                date=date,
                schedule=0
            )
            return Response({}, status=HTTP_200_OK)
        else:
            return Response({}, status=HTTP_400_BAD_REQUEST)

