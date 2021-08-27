import base64
from json import JSONDecodeError
import logging
import random
import re
import requests

from django.core.mail import EmailMessage
from django.core.files.storage import FileSystemStorage
from django.conf import settings

import urllib.parse as urlparse
import numpy as np


logger = logging.getLogger('django')

headers = {"sm-api-key": settings.SEARCH_METRICS_KEY,
           "sm-api-secret": settings.SEARCH_METRICS_SECRET}

keywords_query = '''
    query {
        search_experience:keywords(search:"%s",se_id:29) {
            keyword
            search_volume
            cpc
            keyword_id
        }
    }
'''


topic_query = '''
    query {
        content_experience:explore_topic(topic_id:%s, se_id:29) {
            nodes{
                id
                traffic_index
                text
                user_intent{
                    informational
                    transactional
                    navigational
                }
            }
        }
    }
'''

URL_REG_EXP = r'https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\/(.*?)$'
URL_PARAMS_EXP = r'https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}\/[-a-zA-Z0-9@:%._\+~#=]?(.*?)$'


def average(lst):
    return round(sum(lst) / len(lst), 2)


def generate_random_number():
    return random.randint(1000000, 9999999)


def generate_directories(url):
    return urlparse.urlparse(url).path.split("/")[1:]


def get_domain(url):
    return urlparse.urlparse(url).netloc


def get_subdomain(url):
    return '.'.join(urlparse.urlparse(url).netloc.split('.')[:-2])


def filtered_array(arr):
    array = []
    for elem in arr:
        if elem and re.match(r"[A-Za-z\-]+$", elem):
            array.append(elem)
    return array


def get_access_token(key, secret):
    credentials = f'{key}:{secret}'
    auth_encoded = credentials.encode('utf-8')
    auth = str(base64.b64encode(auth_encoded), "utf-8")
    headers = {'Authorization': f'Basic {auth}'}
    data = {'grant_type': 'client_credentials'}
    r = requests.post(url='https://api.searchmetrics.com/v4/token', headers=headers, data=data)
    try:
        access_token = r.json()['access_token']
    except (KeyError, JSONDecodeError):
        return None

    return access_token


def top_words(model, feature_names, n_top_words):
    return [feature_names[i] for i in model.components_[0].argsort()[:-n_top_words - 1:-1]]


def add_to_dictionary(cat_dict, key, new_keyword, integration):
    integration = '' if not integration or integration == 'nan' or integration == np.nan \
                        or isinstance(integration, float) else integration
    if key not in cat_dict:
        cat_dict[key] = {'keywords': [new_keyword]}
        cat_dict[key]['integration'] = integration.split("|||")
        cat_dict[key]['search_volume'] = [int(get_keyword_volume(new_keyword))]
    else:
        cat_dict[key]['keywords'].append(new_keyword)
        cat_dict[key]['integration'] += integration.split("|||")
        cat_dict[key]['search_volume'].append(int(get_keyword_volume(new_keyword)))


def save_csv_file(csv_file, filename):
    fs = FileSystemStorage()
    file_name = fs.save(filename, csv_file)
    uploaded_file_url = fs.url(file_name)
    return uploaded_file_url


def is_included(word, exclude_inner):
    for exclude_word in exclude_inner:
        if word.lower().find(exclude_word.lower()) != -1:
            return True
    return False


def get_keyword_data(keyword, country_code, access_token):
    keyword = keyword.lower().strip()
    api_url = 'http://api.searchmetrics.com/v3/ResearchKeywordsGetListKeywordinfo.json' \
              f'?keyword={keyword}&countrycode={country_code}&access_token={access_token}'
    response = requests.get(api_url)
    return response, keyword


def get_rankings_data(domain, country_code, access_token, offset):
    api_url = 'http://api.searchmetrics.com/v3/ResearchOrganicGetListRankingsDomain.json' \
              f'?url={domain}&countrycode={country_code}&access_token={access_token}&limit=250&offset={offset}'
    response = requests.get(api_url)

    try:
        data = response.json()
    except JSONDecodeError as e:
        logger.info(f"Something went wrong while connecting to {api_url}, "
                    f"failed with status code: {response.status_code}. Exception raised: {e}")
        data = None

    return data


def get_list_rankings(access_token, domain, date, offset=0):
    api_url = f'https://api.searchmetrics.com/v3/ResearchOrganicGetListRankingsDomainHistoric.json' \
              f'?access_token={access_token}&url={domain}&countrycode=de&date={date}&limit=250&offset={offset}'
    r = requests.get(url=api_url)

    try:
        response = r.json(encoding='utf-8')["response"]
        return True, response
    except (KeyError, JSONDecodeError):
        return False, r.json(encoding='utf-8')["error_message"]
    except (KeyError, JSONDecodeError):
        return False, None


def get_keywords_phrase(access_token, phrase, country_code):
    api_url = f'https://api.searchmetrics.com/v4/ResearchKeywordsGetListSimilarKeywords.json' \
              f'?access_token={access_token}&keyword={phrase}&countrycode={country_code}&limit=250'
    r = requests.get(url=api_url)

    try:
        response = r.json(encoding='utf-8')["response"]
        return True, response
    except (KeyError, JSONDecodeError):
        return False, r.json(encoding='utf-8')["error_message"]
    except JSONDecodeError:
        return False, None


def get_keyword_info(access_token, keyword, country_code):
    api_url = f'https://api.searchmetrics.com/v4/ResearchOrganicGetListRankingsKeyword.json' \
              f'?access_token={access_token}&keyword={keyword}&countrycode={country_code}&limit=25'
    r = requests.get(url=api_url)

    try:
        response = r.json(encoding='utf-8')["response"]
        return True, response
    except (KeyError, JSONDecodeError):
        return None, None


def run_graphql_query(query):
    request = requests.post('https://graphql.searchmetrics.com',
                            json={'query': query}, headers=headers)

    return request


def get_user_intents(keyword):
    request = run_graphql_query(keywords_query % keyword)
    if request.status_code != 200:
        return None

    data = request.json()
    topic_id = None
    try:
        for key in data['data']['search_experience']:
            if key['keyword'] == keyword:
                topic_id = key['keyword_id']
                break
    except (KeyError, TypeError):
        return None

    if topic_id is None:
        return None

    request = run_graphql_query(topic_query % topic_id)
    if request.status_code != 200:
        return None

    data = request.json()
    user_intent = None
    try:
        for topic in data['data']['content_experience']['nodes']:
            if topic['text'] == keyword:
                user_intent = topic['user_intent']
                break
    except (KeyError, TypeError):
        return None

    return user_intent


def log_to_telegram_bot(message):
    api_url = "https://api.telegram.org/bot732949305:AAGHuNat21SBhRki1BOSUrWfQ8_37lGdo4I/sendMessage?" \
              f"chat_id=48355225&text={message}"
    requests.get(url=api_url)


def get_keyword_volume(keyword):
    access_token = get_access_token(settings.SEARCH_METRICS_KEY, settings.SEARCH_METRICS_SECRET)
    api_url = f'https://api.searchmetrics.com/v3/ResearchKeywordsGetListKeywordinfo.json?keyword={keyword}' \
              f'&countrycode=us&access_token={access_token}'
    r = requests.get(url=api_url)

    try:
        search_volume = r.json(encoding='utf-8')["response"][0]["search_volume"]
        return search_volume
    except (KeyError, JSONDecodeError, IndexError, TypeError):
        return 0


def send_mail(subject, message, file_attachment=None):
    from_email = settings.EMAIL_HOST_USER
    mail = EmailMessage(subject, message, from_email,
                        ['abror.ruzibayev@gmail.com', 'k.kleinschmidt@searchmetrics.com'])
    if file_attachment:
        mail.attach_file(file_attachment)
    mail.send(fail_silently=False)