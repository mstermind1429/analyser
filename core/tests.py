import logging

from django.conf import settings
from django.test import TestCase

from .searchmetrics import SearchmetricsAPI

logger = logging.getLogger('django')

api = SearchmetricsAPI(key=settings.SEARCH_METRICS_KEY, secret=settings.SEARCH_METRICS_SECRET)


class SearchmetricsAPITest(TestCase):
    def setUp(self):
        return

    def test_list_keyword_info(self):
        status, response = api.get_list_keyword_info(
            keyword='shoes',
            country_code='us',
        )
        self.assertEquals(status, True)

    def test_list_keyword_info_sv(self):
        status, response = api.get_list_keyword_info(
            keyword='shoes',
            country_code='us',
            return_sv=True
        )
        self.assertEquals(status, True)

    def test_rankings_domain(self):
        status, response = api.get_rankings_domain(
            domain='zappos.com',
            country_code='us',
        )
        self.assertEquals(status, True)

    def test_rankings_domain_historic(self):
        status, response = api.get_rankings_domain_historic(
            domain='zappos.com',
            country_code='us',
            date='20190922'
        )
        self.assertEquals(status, True)

    def test_list_similar_keywords(self):
        status, response = api.get_list_similar_keywords(
            keyword='shoes',
            country_code='us',
        )
        self.assertEquals(status, True)

    def test_list_rankings_keyword(self):
        status, response = api.get_list_rankings_keyword(
            keyword='shoes',
            country_code='us',
        )
        self.assertEquals(status, True)
