import base64
import logging
from json import JSONDecodeError

import requests

logger = logging.getLogger('django')


class SearchmetricsAPI:

    api = 'https://api.searchmetrics.com/v4/'

    def __init__(self, key=None, secret=None):
        self._set_access_token(key, secret)

    def _concatenate_api(self, api):
        return self.api + api

    def _set_access_token(self, key, secret):
        credentials = f'{key}:{secret}'
        auth_encoded = credentials.encode('utf-8')
        auth = str(base64.b64encode(auth_encoded), "utf-8")
        headers = {
            'Authorization': f'Basic {auth}'
        }
        data = {
            'grant_type': 'client_credentials'
        }
        r = requests.post(url=self._concatenate_api('token'), headers=headers, data=data)

        try:
            access_token = r.json()['access_token']
            self.access_token = access_token
        except (KeyError, JSONDecodeError) as err:
            logger.info(f"API: Could not receive access token with credentials: {credentials}. "
                        f"Error message: {err}")
            self.access_token = None

    @classmethod
    def _process_response(cls, response, api):
        try:
            response = response.json(encoding='utf-8')
        except JSONDecodeError as err:
            logger.info(f"API: Error occurred while handling API call: {err}\nAPI Call: {api}")
            return False, err

        try:
            response = response["response"]
            return True, response
        except (TypeError, KeyError) as err:
            logger.info(f"API: Error occurred while handling API call: {err}\nAPI Call: {api}")

        try:
            error_message = response["error_message"]
            return False, error_message
        except (TypeError, KeyError) as err:
            logger.warning(f"API: Error occurred while handling API call: {err}\nAPI Call: {api}")

        return False, None

    def _get_processed_keyword_volume(self, response, api):
        status, response = self._process_response(response, api)

        if not status:
            return False, None

        try:
            search_volume = response[0]["search_volume"]
        except (KeyError, IndexError, TypeError):
            return False, None

        return True, search_volume

    def get_list_keyword_info(self, keyword, country_code='us', return_sv=False):
        """

        """
        keyword = keyword.lower().strip()
        api = self._concatenate_api('ResearchKeywordsGetListKeywordinfo.json')
        response = requests.get(
            api,
            params=
            {
                'keyword': keyword,
                'countrycode': country_code,
                'access_token': self.access_token,
            }
        )

        if return_sv:
            return self._get_processed_keyword_volume(
                response=response,
                api=api
            )

        return self._process_response(
            response=response,
            api=api
        )

    def get_rankings_domain(self, domain, country_code='us', offset=0):
        """

        """
        api = self._concatenate_api('ResearchOrganicGetListRankingsDomain.json')
        response = requests.get(
            api,
            params=
            {
                'url': domain,
                'countrycode': country_code,
                'access_token': self.access_token,
                'limit': 250,
                'offset': offset
            }
        )
        return self._process_response(
            response=response,
            api=api
        )

    def get_rankings_domain_historic(self, domain, date, country_code='us', offset=0):
        """

        """
        api = self._concatenate_api('ResearchOrganicGetListRankingsDomainHistoric.json')
        response = requests.get(
            api,
            params=
            {
                'url': domain,
                'countrycode': country_code,
                'access_token': self.access_token,
                'date': date,
                'limit': 250,
                'offset': offset
            }
        )
        return self._process_response(
            response=response,
            api=api
        )

    def get_list_similar_keywords(self, keyword, country_code='us'):
        """

        """
        keyword = keyword.lower().strip()
        api = self._concatenate_api('ResearchKeywordsGetListSimilarKeywords.json')
        response = requests.get(
            api,
            params=
            {
                'keyword': keyword,
                'countrycode': country_code,
                'access_token': self.access_token,
                'limit': 250
            }
        )
        return self._process_response(
            response=response,
            api=api
        )

    def get_list_rankings_keyword(self, keyword, country_code='us'):
        """

        """
        keyword = keyword.lower().strip()
        api = self._concatenate_api('ResearchOrganicGetListRankingsKeyword.json')
        response = requests.get(
            api,
            params=
            {
                'keyword': keyword,
                'countrycode': country_code,
                'access_token': self.access_token,
                'limit': 25
            }
        )
        return self._process_response(
            response=response,
            api=api
        )
