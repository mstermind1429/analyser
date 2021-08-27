import csv
from datetime import datetime
from json import JSONDecodeError
import logging
from operator import itemgetter
import os
import re
from time import time
import urllib.parse as urlparse
from urllib.parse import parse_qs

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage

from background_task import background
import pandas as pd
import requests
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

from keywords.models import DomainData
from core.searchmetrics import SearchmetricsAPI
from core.helpers import (generate_random_number, add_to_dictionary, get_rankings_data, filtered_array,
                          average, get_access_token, get_keyword_info, get_domain, generate_directories,
                          get_keyword_data, send_mail, is_included, top_words, get_subdomain, get_list_rankings)

logger = logging.getLogger('django')

EXCLUDE_WORDS = ["in", "for", "a", "of", "to", "that", "on", "at",
                 "it", "can", "is", "do", "an", "-", "me", "when",
                 "with", "you", "how", "from", "near", "old", "does"]

WORD_REG_EXP = r"^[A-Za-z\-`'’]+"

RED_TO_GREEN = ["#B60A1C", "#E03531", "#FF684C", "#FF684C", "#E39802", "#E39802", "#F0BD27", "#F0BD27",
                "#FFDA66", "#FFDA66", "#8ACE7E", "#8ACE7E", "#51B364", "#51B364", "#309143"]
GREEN_TO_WHITE = ["#309143", "#3E9850", "#4DA05D", "#5CA86B", "#6BB078", "#79B886", "#88C093", "#97C8A1",
                  "#A6CFAE", "#B5D7BB", "#B5D7BB", "#D2E7D6", "#E1EFE4", "#F0F7F1", "#FFFFFF"]
RED_TO_WHITE = ["#B60A1C", "#BB1B2C", "#C02D3C", "#C53E4C", "#CA505C", "#D0616D", "#D5737D", "#DA848D",
                "#DF969D", "#E4A7AD", "#EAB9BE", "#EFCACE", "#F4DCDE", "#F9EDEE", "#FFFFFF"]

CATEGORY_NAMES = {
    'gender': ['man', 'men', 'women', 'woman', 'boy', 'girl', 'womens', 'mens', "men's", "women's", 'boys', 'girls'],
    'color': ['red', 'yellow', 'blue', 'brown', 'orange', 'green', 'violet', 'black', 'carnation pink',
              'yellow orange', 'blue green', 'red violet', 'red orange', 'yellow green', 'blue violet',
              'white', 'violet red', 'dandelion', 'cerulean', 'apricot', 'scarlet', 'green yellow',
              'indigo and gray', 'grey'],
    'silhouette': ['mid', 'low', 'high', 'mids', 'lows', 'highs'],
    'shoes': ['retro', 'og'],
    'brand': ['nike', 'adidas'],
}

N_SAMPLES, N_FEATURES, N_COMPONENTS, N_TOP_WORDS = 20000, 20000, 1, 5

tf_vectorizer = CountVectorizer(max_df=1.0, min_df=.0,
                                ngram_range=(1, 2),
                                token_pattern=r'\b[\w-]+\b',
                                max_features=N_FEATURES,
                                stop_words='english')

lda = LatentDirichletAllocation(n_components=N_COMPONENTS, max_iter=5,
                                learning_method='online',
                                learning_offset=50.,
                                random_state=0)


class KeywordsAnalysis:
    """
    Class for keywords analysis from csv files

    Attributes:
        csv_file (file): file of the .csv format
        filename (str): name of the file
        exclude_words (list): words to exclude
        analysis (str): type of the analysis
        limit (int): limit of the needed values
    """
    def __init__(self, csv_file=None, filename=None, exclude_words=None, analysis='count', limit=0):
        if exclude_words is None:
            exclude_words = []

        self.csv_file = csv_file
        self.filename = filename
        self.analysis = analysis
        self.exclude_words = exclude_words
        self.limit = limit

        self.words_dict = {}
        self.sorted_dict = {}
        self.sorted_list = []
        self.temp_file = None
        self.df = None

    def set_df(self, df=None):
        if df is None:
            self.temp_file = self.save_temp()
            self.df = self.get_df()
            os.remove(self.temp_file)
        else:
            self.df = df

    def get_df(self):
        return pd.read_csv(self.temp_file)

    def save_temp(self):
        fs = FileSystemStorage()
        filename = fs.save(self.filename + '.csv', self.csv_file)
        return fs.url(filename)

    def is_not_included(self, word, inner_only=False):
        for exclude_word in self.exclude_words:
            if word.lower().find(exclude_word.lower()) != -1:
                return False
        return True and (inner_only or word not in EXCLUDE_WORDS)

    def process_words_dict(self):
        keywords = self.df['Keyword']
        traffic_index = self.df['Traffic Index'] if 'Traffic Index' in self.df.columns else None
        search_volume = self.df['Search Volume'] if 'Search Volume' in self.df.columns else None
        value = {'count': 1}

        for index, keyword in enumerate(keywords):
            if traffic_index is not None:
                value['traffic'] = traffic_index[index]
            if search_volume is not None:
                value['search'] = search_volume[index]

            temp_words = []
            words = keyword.split()

            if self.analysis is 'count' or value[self.analysis] >= self.limit:
                for word in words:
                    if self.is_not_included(word, self.exclude_words) and re.match(WORD_REG_EXP, word):
                        temp_words.append(word)
                        if word not in self.words_dict.keys():
                            self.words_dict[word] = {word: value[self.analysis]}
                        else:
                            self.words_dict[word][word] += value[self.analysis]

            for temp_word in temp_words:
                for word in temp_words:
                    if word is not temp_word:
                        try:
                            self.words_dict[temp_word][word] += value[self.analysis]
                        except KeyError:
                            self.words_dict[temp_word][word] = value[self.analysis]

    def _prepare_count_sort(self):
        for word in self.words_dict.keys():
            if self.words_dict[word][word] >= self.limit:
                self.sorted_dict[word] = self.words_dict[word][word]

    def _prepare_sort(self):
        for word in self.words_dict.keys():
            max_traffic = -1
            max_key = 0
            for word_key in self.words_dict[word].keys():
                if self.words_dict[word][word_key] > max_traffic:
                    max_traffic = self.words_dict[word][word_key]
                    max_key = word_key
            try:
                self.sorted_dict[word] = self.words_dict[word][max_key]
            except KeyError:
                pass

    def _get_sorted_list(self, example_keywords=False):
        sorted_list = {}
        for word in self.sorted_list:
            for row_word in self.sorted_list:
                if word is not row_word:
                    try:
                        if self.words_dict[row_word][word] >= self.limit:
                            if f'{row_word} {word}' not in sorted_list.keys():
                                sorted_list[f'{word} {row_word}'] = self.words_dict[row_word][word]
                    except KeyError:
                        pass

        if example_keywords:
            sorted_list = [key for key, _ in sorted(sorted_list.items(),
                                                    key=itemgetter(1),
                                                    reverse=True)]
        else:
            sorted_list = [[key, value] for key, value in sorted(sorted_list.items(),
                                                                 key=itemgetter(1),
                                                                 reverse=True)]
        return sorted_list

    def sort(self):
        if self.analysis == 'count':
            self._prepare_count_sort()
        else:
            self._prepare_sort()

        self.sorted_list = [key for key, _ in sorted(self.sorted_dict.items(), key=itemgetter(1), reverse=True)]

    def save(self, table=False, example_keywords=False):
        filename = f"{self.filename}_{generate_random_number()}.csv"
        filepath = f"{settings.REPORT_PATH}/{filename}"

        with open(filepath, 'w+', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            if table:
                writer.writerow([None] + self.sorted_list)

                for word in self.sorted_list:
                    row = [word]
                    for row_word in self.sorted_list:
                        try:
                            row.append(self.words_dict[row_word][word])
                        except KeyError:
                            row.append("-")
                    writer.writerow(row)
            else:
                if not example_keywords:
                    writer.writerow(['Combinations', 'Count'])
                else:
                    writer.writerow(['-' for _ in range(25)])

                sorted_list = self._get_sorted_list(example_keywords)
                for word in sorted_list:
                    if example_keywords:
                        row = [word]
                        for words in self.df['Keyword']:
                            if all(elem in words.split() for elem in word.split()):
                                row.append(words)
                        writer.writerow(row)
                    else:
                        writer.writerow(word)
        return filename


@background(schedule=1)
def category_domain_task(
        uploaded_file_url: str,
        key: str,
        secret: str,
        country_code: str
) -> None:
    """

    """

    data = pd.read_csv(f'/{uploaded_file_url}')

    category_dict = {}
    for keyword, integration in zip(data['Keyword'], data['SERP Feature Integrations']):
        words = keyword.replace('air jordan', '').split()
        labels_keyword, label_added = [], False

        for word in words:
            try:
                numeric_value = int(word)
                if len(word) == 4:
                    add_to_dictionary(category_dict, 'year', keyword, integration)
                    label_added = True
                elif 'size' in words:
                    add_to_dictionary(category_dict, 'size', keyword, integration)
                    label_added = True
            except ValueError:
                for category_name in CATEGORY_NAMES:
                    if word in CATEGORY_NAMES[category_name]:
                        add_to_dictionary(category_dict, category_name, keyword, integration)
                        label_added = True

        if re.findall(r'air jordan ([1-9]|[12]\d|3[0-3])', keyword):
            add_to_dictionary(category_dict, 'air jordan', keyword, integration)
            label_added = True

        if not label_added:
            add_to_dictionary(category_dict, 'other', keyword, integration)

    domains = {}
    keywords_list, search_volumes, integrations = [], [], {}
    num_of_failed_keywords = 0

    category_filename = f"category_top_domains_{generate_random_number()}.xlsx"
    filepath = f"{settings.REPORT_PATH}/{category_filename}"
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')

    for category in category_dict:
        for index, keyword in enumerate(category_dict[category]['keywords']):
            keywords_list.append(keyword)

            access_token = get_access_token(key, secret)
            success, keywords_data = get_keyword_info(
                access_token=access_token,
                keyword=keyword,
                country_code=country_code
            )

            if not success:
                num_of_failed_keywords += 1

            if success:
                for keyword_data in keywords_data:
                    domain = get_domain(f"https://{keyword_data['url']}")
                    if domain not in domains:
                        domains[domain] = {}

                    if 'keywords' not in domains[domain]:
                        domains[domain]['keywords'] = [keyword]
                    else:
                        if keyword not in domains[domain]['keywords']:
                            domains[domain]['keywords'].append(keyword)

                    if 'urls' not in domains[domain]:
                        domains[domain]['urls'] = [keyword_data['url']]
                    else:
                        if keyword not in domains[domain]['urls']:
                            domains[domain]['urls'].append(keyword_data['url'])

                    if 'position' not in domains[domain]:
                        domains[domain]['position'] = [int(keyword_data['position'])]
                    else:
                        domains[domain]['position'].append(int(keyword_data['position']))

        domains_tuple = []
        for domain in domains:
            domains_tuple.append((domain, len(domains[domain]['keywords']), len(domains[domain]['urls'])))

        sorted_domains = [key for key, _, _ in sorted(domains_tuple, key=itemgetter(1), reverse=True)]

        df = pd.DataFrame(
            {
                'Domain': [domain for domain in sorted_domains],
                'Total keywords ranking for': [len(domains[domain]['keywords']) for domain in sorted_domains],
                'Total unique URLs': [len(domains[domain]['urls']) for domain in sorted_domains],
                'Avg. Ranking': [average(domains[domain]['position']) for domain in sorted_domains],
            }
        )
        df.to_excel(writer, sheet_name=category, index=False)
    writer.save()

    # text_clf = Pipeline([
    #     ('vect', CountVectorizer()),
    #     ('tfidf', TfidfTransformer()),
    #     ('clf', SGDClassifier(loss='hinge', penalty='l2',
    #                           alpha=1e-3, random_state=42,
    #                           max_iter=5, tol=None)),
    # ])
    #
    # text_clf.fit(keywords[:-50], labels[:-50])
    # predicted = text_clf.predict(keywords[-50:])

    filename = f'category_domain_{generate_random_number()}.xlsx'
    writer = pd.ExcelWriter(f'{settings.REPORT_PATH}/{filename}', engine='xlsxwriter')

    for category in category_dict:
        df = pd.DataFrame({
            'Keyword': category_dict[category]['keywords']
        })
        df.to_excel(writer, sheet_name=category, index=False)

    df = pd.DataFrame({
        'Category': [category for category in category_dict.keys()],
        'Total Search Volume': [sum(category_dict[category]['search_volume']) for category in category_dict.keys()],
        'Average Search Volume': [average(category_dict[category]['search_volume']) for category in
                                  category_dict.keys()],
        'Top 5 Integration': [",".join(list(set(sorted(category_dict[category]['integration'],
                                                       key=category_dict[category]['integration'].count,
                                                       reverse=True)))[:5]) for category in category_dict],
        'Number of keywords': [len(category_dict[category]['keywords']) for category in category_dict.keys()]
    })

    df.to_excel(writer, sheet_name='stats', index=False)
    writer.save()

    subject = 'Category Domain Tool'
    message = 'Your Category Domain analysis is ready to download.'

    from_email = settings.EMAIL_HOST_USER
    mail = EmailMessage(subject, message, from_email, ['abror.ruzibayev@gmail.com', 'k.kleinschmidt@searchmetrics.com'])
    mail.attach_file(f'{settings.REPORT_PATH}/{filename}')
    mail.attach_file(f'{settings.REPORT_PATH}/{category_filename}')
    mail.send(fail_silently=False)


@background(schedule=1)
def run_domain_searchmetrics_simple(
        key: str,
        secret: str,
        amount: str,
        country_code: str,
        domain: str
) -> None:
    """

    """
    access_token = get_access_token(key, secret)

    offset = 0
    file_path = settings.REPORT_PATH + f'/simple_domain_sm_analysis_{generate_random_number()}.csv'
    with open(file_path, "w+", encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Keyword", "URL", "Position", "Page", "Title", "Description", "Traffic", "Competition",
                         "CPC", "Ad Budget", "Potential", "Avg Popularity", "Last Months Count"])

        for _ in range(amount // 250):
            data = get_rankings_data(domain, country_code, access_token, offset)

            if data:
                for element in data['response']:
                    try:
                        writer.writerow([element['keyword'], element['url'], element['position'], element['page'],
                                         element['title'], element['description'], element['traffic'],
                                         element['competition'], element['cpc'], element['adbudget'], element['potential'],
                                         element['avg_popularity'], element['last_months_count']])
                    except Exception as e:
                        logger.info(f"Something went wrong while accessing response element. Error: {e}")

            offset += 250

    subject = 'Domain Search Metrics Simple Analysis To CSV'
    message = f'Domain Search Metrics Analysis is Ready. Look at the attachment below.' \
              f'\n\nParameters:\nDomain: {domain}\nCountry Code: {country_code}'

    from_email = settings.EMAIL_HOST_USER
    mail = EmailMessage(subject, message, from_email, settings.ADMIN_EMAILS)
    mail.attach_file(file_path)

    try:
        mail.send(fail_silently=False)
    except Exception as e:
        logger.info(f"Something went wrong while sending an email. Error: {e}")


@background(schedule=1)
def run_domain_searchmetrics_complete(
        key: str,
        secret: str,
        amount: str,
        country_code: str,
        domain: str
) -> None:
    """

    """
    access_token = get_access_token(key, secret)

    keyword_info = {}
    keywords = []
    offset = 0
    for _ in range(amount // 250):
        data = get_rankings_data(domain, country_code, access_token, offset)

        if data:
            for keyword in data['response']:
                try:
                    keywords.append(keyword['keyword'])
                    keyword_info[keyword['keyword']] = keyword
                except KeyError:
                    logger.info(f"Not found key in keywords data: {keyword}")

        offset += 250

    ranking = []
    for index, keyword in enumerate(keywords):
        keyword = keyword.strip()
        api_url = 'http://api.searchmetrics.com/v3/ResearchOrganicGetListRankingsKeyword.json' \
                  f'?keyword={keyword}&countrycode={country_code}&access_token={access_token}'
        response = requests.get(api_url)

        try:
            ranking_info = response.json()['response']
        except Exception as e:
            logger.info(f"No response data found: {e}")
            continue

        api_url = 'http://api.searchmetrics.com/v3/ResearchKeywordsGetListKeywordinfo.json' \
                  f'?keyword={keyword}&countrycode={country_code}&access_token={access_token}'
        response = requests.get(api_url)
        data = response.json()

        keyword_data = None
        try:
            for item in data['response']:
                if item['keyword'] == keyword:
                    keyword_data = item
        except KeyError:
            logger.info("No response data found")
            continue

        if len(ranking_info) == 0:
            ranking.append(keyword)

        for info in ranking_info:
            try:
                DomainData.objects.create(keyword=keyword, position=info['position'], url=info['url'],
                                          title=info['title'],
                                          traffic_index=int(keyword_info[keyword]['traffic']),
                                          search_volume=int(keyword_data['search_volume']),
                                          trend=info['trend']['trend'], cpc=keyword_data['cpc'],
                                          integration=keyword_data['integration'],
                                          competition=keyword_data['competition'], domain=domain)
            except Exception as e:
                logger.info(f"Error while saving Domain Data to database: {e}")

    subject = 'Domain Search Metrics Complete Analysis to DB'
    message = f'Domain Search Metrics Analysis is Ready. You can find it at http://karlkleinschmidt.com' \
              f'/admin/app/domaindata/?domain={domain}' \
              f'\n\nParameters:\nDomain: {domain}\nCountry Code: {country_code}'

    from_email = settings.EMAIL_HOST_USER
    mail = EmailMessage(subject, message, from_email, settings.ADMIN_EMAILS)

    try:
        mail.send(fail_silently=False)
    except Exception as e:
        logger.info(f"Something went wrong while sending an email. Error: {e}")


def get_example_url_keywords(
        uploaded_file_url: str,
        sort_type: str,
        sort_label: str,
        limit: int,
        exclude_inner: list
) -> str:
    """

    """
    df = pd.read_csv(f'/{uploaded_file_url}')

    df['URL'] = df['URL'].apply(generate_directories)
    data = df['URL']
    data_samples = data[:N_SAMPLES]

    words_dict = {}
    values_dict = {}
    for index, data in enumerate(data_samples):
        data = filtered_array(data)
        if len(data) > 0:
            if data[1:]:
                try:
                    words_dict[data[0]] += data[1:]
                except KeyError:
                    words_dict[data[0]] = data[1:]
                for key in data[1:]:
                    if key in values_dict:
                        values_dict[key] += df[sort_type][index]
                    else:
                        values_dict[key] = df[sort_type][index]

    file_name = f'example_url_keywords_{generate_random_number()}_by_{sort_label}.xlsx'
    output = f'{settings.REPORT_PATH}/{file_name}'
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    for key in words_dict:
        if len(words_dict[key]) > 5:
            words_list = []
            values_list = []
            for word in words_dict[key]:
                ready_word = " ".join(word.split('-'))
                if ready_word not in words_list:
                    words_list.append(ready_word)
                    values_list.append(values_dict[word])

            df = pd.DataFrame(data={'Keyword': words_list, sort_type: values_list})

            analysis = KeywordsAnalysis(filename="example_url_keywords", exclude_words=exclude_inner,
                                        analysis=sort_label, limit=limit)
            analysis.set_df(df=df)
            analysis.process_words_dict()
            analysis.sort()

            filename = analysis.save(table=False, example_keywords=True)
            df = pd.read_csv(filename, header=None)
            df.to_excel(writer, sheet_name=key, index=False, header=None)

    writer.save()

    return file_name


@background(schedule=1)
def search_volume_task(
        uploaded_file_url,
        country_code,
        key,
        secret
):
    df = pd.read_csv(f'/{uploaded_file_url}', encoding='unicode_escape')

    keywords_data = [keyword for keyword in df['Keyword']]

    logger.info('Search Volume Analysis have started')

    keywords = []
    search_volumes = []

    no_data_keywords = []
    no_data_reason = []

    access_token = get_access_token(key, secret)
    for keyword in keywords_data:
        response, keyword = get_keyword_data(keyword, country_code, access_token)

        if 'error_message' in response.text:
            access_token = get_access_token(key, secret)
            response, keyword = get_keyword_data(keyword, country_code, access_token)

        try:
            keyword_info = response.json()['response'][0]
            keywords.append(keyword)
            search_volumes.append(keyword_info['search_volume'])
        except (KeyError, TypeError, JSONDecodeError) as e:
            logger.info(e)
            no_data_keywords.append(keyword)
            no_data_reason.append("No info returned")

    file_name = f'search_volumes_{generate_random_number()}.xlsx'
    output = f'{settings.REPORT_PATH}/{file_name}'
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    result_df = pd.DataFrame({'Keyword': keywords, 'Search Volume': search_volumes})
    result_df.to_excel(writer, sheet_name='results', index=False)
    error_df = pd.DataFrame({'Keyword': no_data_keywords, 'Error Reason': no_data_reason})
    error_df.to_excel(writer, sheet_name='no-data', index=False)
    writer.save()

    send_mail('Search Volume Tool Analysis', 'Your Search Volume Analysis is ready to download.', output)


def get_group_keywords(
        uploaded_file_url: str,
        group_1: str,
        group_2: str,
) -> (str, float):
    """

    """
    t0 = time()

    group_1_words = [word for word in group_1.split()]
    group_2_words = [word for word in group_2.split()]

    with open(f"/{uploaded_file_url}", "r", encoding='utf-8') as f:
        reader = list(csv.reader(f))

    title_index = 0
    for index, col_name in enumerate(reader[0]):
        if col_name.lower() == 'title':
            title_index = index

    words_dict = {}
    for row in reader[1:]:
        if row[0] not in words_dict.keys():
            words_dict[row[0]] = [row[title_index]]
        else:
            words_dict[row[0]].append(row[title_index])

    result_words_dict = {}
    for key in words_dict.keys():
        if not is_included(key, group_1_words + group_2_words):
            result_words_dict[key] = words_dict[key]

    group_1_or_2, group_1, group_2 = [], [], []

    for key in result_words_dict:
        both_group_cnt, first_group_cnt, second_group_cnt = 0, 0, 0

        for title in result_words_dict[key]:

            if is_included(title, group_1_words + group_2_words):
                both_group_cnt += 1
            if is_included(title, group_1_words):
                first_group_cnt += 1
            if is_included(title, group_2_words):
                second_group_cnt += 1

        if both_group_cnt > 4:
            group_1_or_2.append(key)
        if first_group_cnt > 4:
            group_1.append(key)
        if second_group_cnt > 4:
            group_2.append(key)

    filename = f'keyword_search_{generate_random_number()}.csv'
    with open(f'{settings.REPORT_PATH}/{filename}', 'w+', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Total Unique Keywords", len(words_dict)])
        writer.writerow(["Total Unique Filtered Keywords", len(result_words_dict)])
        writer.writerow([])
        writer.writerow(["Group 1 OR 2 %", f'{round(len(group_1_or_2) / len(result_words_dict) * 100, 4)}%'])
        writer.writerow(["Group 1 OR 2 Amount", len(group_1_or_2)])
        writer.writerow(["Group 1 OR 2:"] + group_1_or_2)
        writer.writerow([])
        writer.writerow(["Group 1 %", f'{round(len(group_1) / len(result_words_dict) * 100, 4)}%'])
        writer.writerow(["Group 1 Amount", len(group_1)])
        writer.writerow(["Group 1:"] + group_1)
        writer.writerow([])
        writer.writerow(["Group 2 %", f'{round(len(group_2) / len(result_words_dict) * 100, 4)}%'])
        writer.writerow(["Group 2 Amount", len(group_2)])
        writer.writerow(["Group 2:"] + group_2)

    time_spent = "%0.3fs." % (time() - t0)
    os.remove(uploaded_file_url)

    return filename, time_spent


def get_keyword_domain(
        data,
        access_token,
        country_code
) -> str:
    keywords = []
    for item in data:
        keywords.append(item)

    domains = {}
    keywords_list, search_volumes, integrations = [], [], {}
    num_of_failed_keywords = 0
    for index, element in enumerate(keywords):
        keyword = element['keyword']

        keywords_list.append(keyword)
        search_volumes.append(int(element['search_volume']))

        success, keywords_data = get_keyword_info(
            access_token=access_token,
            keyword=keyword,
            country_code=country_code
        )

        if not success:
            num_of_failed_keywords += 1

        for integration in element['integration'].split(','):
            if integration in integrations:
                integrations[integration] += 1
            else:
                integrations[integration] = 1

        if success:
            for keyword_data in keywords_data:
                domain = get_domain(f"https://{keyword_data['url']}")
                if domain not in domains:
                    domains[domain] = {}

                if 'cpc' not in domains[domain]:
                    domains[domain]['cpc'] = [int(element['cpc'])]
                else:
                    domains[domain]['cpc'].append(int(element['cpc']))

                if 'keywords' not in domains[domain]:
                    domains[domain]['keywords'] = [keyword]
                else:
                    if keyword not in domains[domain]['keywords']:
                        domains[domain]['keywords'].append(keyword)

                if 'search_volume' not in domains[domain]:
                    domains[domain]['search_volume'] = [int(element['search_volume'])]
                else:
                    domains[domain]['search_volume'].append(int(element['search_volume']))

                if 'urls' not in domains[domain]:
                    domains[domain]['urls'] = [keyword_data['url']]
                else:
                    if keyword not in domains[domain]['urls']:
                        domains[domain]['urls'].append(keyword_data['url'])

                if 'position' not in domains[domain]:
                    domains[domain]['position'] = [int(keyword_data['position'])]
                else:
                    domains[domain]['position'].append(int(keyword_data['position']))

    domains_tuple = []
    for domain in domains:
        domains_tuple.append((domain, len(domains[domain]['keywords']), len(domains[domain]['urls'])))

    sorted_domains = [key for key, _, _ in sorted(domains_tuple, key=itemgetter(1), reverse=True)]

    filename = f"keyword_domain_{generate_random_number()}.xlsx"
    filepath = f"{settings.REPORT_PATH}/{filename}"
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    df = pd.DataFrame(
        {
            'Domain': [domain for domain in sorted_domains],
            'Total keywords ranking for': [len(domains[domain]['keywords']) for domain in sorted_domains],
            'Total unique URLs': [len(domains[domain]['urls']) for domain in sorted_domains],
            'Avg. Ranking': [average(domains[domain]['position']) for domain in sorted_domains],
            'Avg. Search Volume': [average(domains[domain]['search_volume']) for domain in sorted_domains],
            'Avg. Cpc': [average(domains[domain]['cpc']) for domain in sorted_domains],
            'Total Search Volume': [sum(domains[domain]['search_volume']) for domain in sorted_domains],
        }
    )
    df.to_excel(writer, sheet_name='results', index=False)

    df = pd.DataFrame(
        {
            'Keywords': keywords_list,
            'Search Volume': search_volumes,
        }
    )
    df.to_excel(writer, sheet_name='keywords', index=False)

    if len(keywords_list) != 0:
        df = pd.DataFrame(
            {
                'Integration': [key for key in integrations.keys()],
                '% of keywords': [f'{round(value / len(keywords), 2) * 100}%'
                                  for value in integrations.values()],
            }
        )
        df.to_excel(writer, sheet_name='integration', index=False)

    for domain in sorted_domains[:10]:
        min_len = min(len(domains[domain]['urls']), len(domains[domain]['keywords']))
        df = pd.DataFrame(
            {
                'URLs': domains[domain]['urls'][:min_len],
                'Keywords': domains[domain]['keywords'][:min_len]
            }
        )
        df.to_excel(writer, sheet_name=str(domain)[:30], index=False)

    writer.save()

    return filename


def get_similar_keywords(
        uploaded_file_url: str,
        sort_type: str,
        limit: int,
        sort_label: str
) -> str:
    words_dict = {}

    with open(uploaded_file_url, "r") as f:
        reader = list(csv.reader(f))

    line_num = 0
    row_num = 0

    for row in reader:
        if line_num == 0:
            for index, column in enumerate(row):
                if column == sort_type:
                    row_num = index
                    break
            line_num += 1
            continue

        phrase = row[0]
        words = row[0].split()
        index = int(row[row_num])

        if index >= limit:
            words_dict[phrase] = {phrase: index}

            for row1 in reader:
                if row is not row1:
                    if all(elem in row1[0].split() for elem in words):
                        words_dict[phrase][row1[0]] = int(row1[row_num])

    sorted_words = {}
    for word in words_dict.keys():
        try:
            sorted_words[word] = words_dict[word][word]
        except KeyError:
            pass

    sorted_words = [key for key, _ in sorted(sorted_words.items(), key=itemgetter(1), reverse=True)]

    filename = f'similar_keywords_{generate_random_number()}_{sort_label}.csv'
    with open(f'{settings.REPORT_PATH}/{filename}', 'w+', newline='') as f:
        writer = csv.writer(f)

        for word in sorted_words:
            row = [word]
            sorted_keys = {}
            for key in words_dict[word].keys():
                if key is not word:
                    sorted_keys[key] = words_dict[word][key]
            sorted_keys = [key for key, _ in sorted(sorted_keys.items(), key=itemgetter(1), reverse=True)]

            for key in sorted_keys:
                row.append(key)

            writer.writerow(row)

    os.remove(uploaded_file_url)

    return filename


def get_tags_by_search_volume(uploaded_file_url: str) -> str:
    words_dict = {}

    df = pd.read_csv(uploaded_file_url)
    for index, keyword in enumerate(df['Keyword']):
        search_volume = df['Search Volume'][index]
        words_dict[keyword] = search_volume

    sorted_words = [key for key, _ in sorted(words_dict.items(), key=itemgetter(1), reverse=True)]

    filename = f'searchmetrics_project_keyword_import.csv'
    with open(f'{settings.REPORT_PATH}/{filename}', 'w+', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        for word in sorted_words:
            tags = []
            tag_count = 0
            for tag in word.split():
                tag_count += 1
                if tag_count > 2:
                    break
                tags.append(tag)

            row = [word + ';' + ';'.join(tags) + ';']
            writer.writerow(row)

    os.remove(uploaded_file_url)
    return filename


def get_url_key_patterns(uploaded_file_url: str) -> (str, float):
    t0 = time()
    df = pd.read_csv(uploaded_file_url)

    url_params = {}
    url_params_values = {}
    url_extensions = {}

    for url in df['URL']:
        params = []
        values = []

        parsed_url = urlparse.urlparse(url)
        parsed_params = parse_qs(parsed_url.query)
        for key in parsed_params:
            params.append(key)
            values.append(parsed_params[key][0])

        ext = os.path.splitext(os.path.basename(parsed_url.path))[1]
        if ext.find("%") != -1:
            ext = None

        try:
            directory = filtered_array(generate_directories(url))[0]
        except IndexError:
            directory = None

        if directory:
            if ext:
                try:
                    url_extensions[directory] += [ext]
                except KeyError:
                    url_extensions[directory] = [ext]

            try:
                url_params[directory] += params
            except KeyError:
                url_params[directory] = params

            try:
                url_params_values[directory] += values
            except KeyError:
                url_params_values[directory] = values

    df['URL'] = df['URL'].apply(generate_directories)
    data = df['URL']
    data_samples = data[:N_SAMPLES]

    words_dict = {}
    sub_dict = {}
    for data in data_samples:
        data = filtered_array(data)
        if len(data) > 0:
            if data[1:]:
                try:
                    words_dict[data[0]] += data[1:]
                except KeyError:
                    words_dict[data[0]] = data[1:]

                if data[0] not in sub_dict.keys():
                    sub_dict[data[0]] = {}

                for index, item in enumerate(data[1:], 1):
                    try:
                        sub_dict[data[0]][index].append(item)
                    except KeyError:
                        sub_dict[data[0]][index] = [item]

    sorted_words = {}
    for key in words_dict.keys():
        sorted_words[key] = len(words_dict[key])

    sorted_words = [key for key, _ in sorted(sorted_words.items(), key=itemgetter(1), reverse=True)]

    filename = f'url_patterns_{generate_random_number()}.csv'
    with open(f'{settings.REPORT_PATH}/{filename}', 'w+', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Directory", "1 sub-d", "2 sub-d", "3 sub-d",
                         "Top Keyword 1", "Top Keyword 2", "Top Keyword 3", "Top Keyword 4", "Top Keyword 5",
                         "URL Param 1", "URL Param 2", "URL Param 3", "URL Param 4", "URL Param 5",
                         "URL Param Value 1", "URL Param Value 2", "URL Param Value 3", "Extension"])
        for key in sorted_words:
            if len(words_dict[key]) >= 5:
                sub_dirs = []
                for index in range(1, 4):
                    try:
                        tf = tf_vectorizer.fit_transform(sub_dict[key][index])
                        lda.fit(tf)

                        tf_feature_names = tf_vectorizer.get_feature_names()
                        sub_dirs += top_words(lda, tf_feature_names, 1)
                    except (KeyError, ValueError):
                        pass

                for index, word in enumerate(words_dict[key]):
                    if word in sub_dirs:
                        words_dict[key][index] = ''

                try:
                    tf = tf_vectorizer.fit_transform(words_dict[key])
                    lda.fit(tf)

                    tf_feature_names = tf_vectorizer.get_feature_names()
                    dir_features = top_words(lda, tf_feature_names, N_TOP_WORDS)
                except ValueError:
                    dir_features = []

                url_features = [None]
                if url_params[key]:
                    tf = tf_vectorizer.fit_transform(url_params[key])
                    lda.fit(tf)

                    tf_feature_names = tf_vectorizer.get_feature_names()
                    url_features = top_words(lda, tf_feature_names, N_TOP_WORDS)

                url_values_features = [None]
                if url_params_values[key]:
                    tf = tf_vectorizer.fit_transform(url_params_values[key])
                    lda.fit(tf)

                    tf_feature_names = tf_vectorizer.get_feature_names()
                    url_values_features = top_words(lda, tf_feature_names, 3)

                ext_features = [None]
                try:
                    if url_extensions[key]:
                        tf = tf_vectorizer.fit_transform(url_extensions[key])
                        lda.fit(tf)

                        tf_feature_names = tf_vectorizer.get_feature_names()
                        ext_features = top_words(lda, tf_feature_names, 1)
                except KeyError:
                    pass

                url_features = [None] * (5 - len(url_features))
                url_values_features = [None] * (5 - len(url_values_features))
                dir_features = [None] * (5 - len(dir_features))
                sub_dirs = [None] * (3 - len(sub_dirs))

                writer.writerow([key] + sub_dirs + dir_features + url_features + url_values_features + ext_features)

    time_spent = "%0.3fs." % (time() - t0)
    os.remove(uploaded_file_url)

    return filename, time_spent


def get_url_searchmetrics(
        date_from: str,
        date_to: str,
        amount: int,
        domain: str,
        key: str,
        secret: str
) -> (bool, str):
    date_from = datetime.strftime(datetime.strptime(date_from, '%Y-%m-%d'), '%Y%m%d')
    date_to = datetime.strftime(datetime.strptime(date_to, '%Y-%m-%d'), '%Y%m%d')

    access_token = get_access_token(key, secret)

    offset = 0
    before_data, after_data = [], []
    n_requests = int(amount / 250)
    for _ in range(n_requests):
        from_date_info = get_list_rankings(access_token, domain, date_from, offset)
        after_date_info = get_list_rankings(access_token, domain, date_to, offset)

        if from_date_info[0]:
            before_data += from_date_info[1]
        else:
            error_message = 'API Error: ' + from_date_info[1]
            return False, error_message

        if after_date_info[0]:
            after_data += after_date_info[1]
        else:
            error_message = 'API Error: ' + after_date_info[1]
            return False, error_message

        offset += 250

    words_dict = {}
    for first in before_data:
        exists = False

        full_url = f'https://{first["url"]}' if not urlparse.urlparse(first['url']).scheme else first['url']
        directories = generate_directories(full_url)
        subdomain = get_subdomain(full_url)
        if subdomain and subdomain != 'www':
            directories += [subdomain]
        else:
            subdomain = ''

        for index, directory in enumerate(directories):
            if subdomain and index == len(directories) - 1:
                diry = directory
            else:
                diry = '/' + directory + '/' if directory else '/'

            if diry not in words_dict.keys():
                words_dict[diry] = {}

            required_fields = ['losers', 'winners', 'out', 'new']

            for field in required_fields:
                if field not in words_dict[diry]:
                    words_dict[diry][field] = {}

            if 'type' not in words_dict[diry]:
                if index == 0:
                    dir_type = 'directory'
                elif (0 < index < len(directories) and not subdomain or
                      0 < index < len(directories) - 1 and subdomain):
                    dir_type = 'subdirectory'
                else:
                    dir_type = 'subdomain'

                words_dict[diry]['type'] = dir_type

            for second in after_data:
                if first['url'] == second['url'] and first['keyword'] == second['keyword']:
                    rank_change = first['position'] - second['position']
                    traffic_change = second['traffic_monthly'] - first['traffic_monthly']
                    if rank_change >= 0:
                        words_dict[diry]['winners'][first['keyword']] = {'url': first['url'],
                                                                         'traffic': first['traffic_monthly'],
                                                                         'position_trend': rank_change,
                                                                         'position': first['position'],
                                                                         'search_volume':
                                                                             first['search_volume_monthly'],
                                                                         'type': '',
                                                                         'traffic_change': traffic_change}
                    else:
                        words_dict[diry]['losers'][first['keyword']] = {'url': first['url'],
                                                                        'traffic': first['traffic_monthly'],
                                                                        'position_trend': rank_change,
                                                                        'position': first['position'],
                                                                        'search_volume':
                                                                            first['search_volume_monthly'],
                                                                        'type': '',
                                                                        'traffic_change': traffic_change}
                    if 'search_volume' in words_dict[diry].keys():
                        words_dict[diry]['search_volume'] += first['search_volume_monthly']
                    else:
                        words_dict[diry]['search_volume'] = first['search_volume_monthly']

                    exists = True

            if not exists:
                traffic_change = -1 * first['traffic_monthly']
                if 'search_volume' in words_dict[diry].keys():
                    words_dict[diry]['search_volume'] += first['search_volume_monthly']
                else:
                    words_dict[diry]['search_volume'] = first['search_volume_monthly']

                words_dict[diry]['out'][first['keyword']] = {'url': first['url'],
                                                             'traffic': first['traffic_monthly'],
                                                             'position': first['position'],
                                                             'position_trend': -1 * first['position'],
                                                             'search_volume':
                                                                 first['search_volume_monthly'],
                                                             'type': 'out',
                                                             'traffic_change': traffic_change}

    for second in after_data:
        exists = False
        full_url = f'https://{second["url"]}' if not urlparse.urlparse(second['url']).scheme else second['url']
        directories = generate_directories(full_url)
        subdomain = get_subdomain(full_url)
        if subdomain and subdomain != 'www':
            directories += [subdomain]
        else:
            subdomain = ''

        for index, directory in enumerate(directories):
            if subdomain and index == len(directories) - 1:
                diry = directory
            else:
                diry = '/' + directory + '/' if directory else '/'

            if diry not in words_dict.keys():
                words_dict[diry] = {}

            required_fields = ['losers', 'winners', 'out', 'new']

            for field in required_fields:
                if field not in words_dict[diry]:
                    words_dict[diry][field] = {}

            if 'type' not in words_dict[diry]:
                if index == 0:
                    dir_type = 'directory'
                elif (0 < index < len(directories) and not subdomain or
                      0 < index < len(directories) - 1 and subdomain):
                    dir_type = 'subdirectory'
                else:
                    dir_type = 'subdomain'

                words_dict[diry]['type'] = dir_type

            for first in before_data:
                if second['url'] == first['url'] and second['keyword'] == first['keyword']:
                    exists = True

            if not exists:
                traffic_change = second['traffic_monthly']
                words_dict[diry]['new'][second['keyword']] = {'url': second['url'],
                                                              'traffic': second['traffic_monthly'],
                                                              'position': second['position'],
                                                              'position_trend': second['position'],
                                                              'search_volume':
                                                                  second['search_volume_monthly'],
                                                              'type': 'new',
                                                              'traffic_change': traffic_change}
                if 'search_volume' in words_dict[diry].keys():
                    words_dict[diry]['search_volume'] += second['search_volume_monthly']
                else:
                    words_dict[diry]['search_volume'] = second['search_volume_monthly']

    file_name = f'winners_and_losers_{domain}_from_{date_from}_to_{date_to}.xlsx'
    output = f'{settings.REPORT_PATH}/{file_name}'
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    total_keywords = [(len({**words_dict[diry]['winners'], **words_dict[diry]['losers'],
                            **words_dict[diry]['out'], **words_dict[diry]['new']}), diry)
                      for diry in words_dict.keys()]
    sorted_dirs = [key for _, key in sorted(total_keywords, key=itemgetter(0), reverse=True)]
    total_keywords = [len({**words_dict[diry]['winners'], **words_dict[diry]['losers'],
                           **words_dict[diry]['out'], **words_dict[diry]['new']})
                      for diry in sorted_dirs]
    total_search = [words_dict[diry]['search_volume'] for diry in sorted_dirs]

    total_winners = [len({**words_dict[diry]['winners'], **words_dict[diry]['new']})
                     for diry in sorted_dirs][:15]
    sorted_winners = sorted(total_winners, reverse=True)
    winners_colored = {}
    for winner, gradient in zip(sorted_winners, reversed(RED_TO_GREEN)):
        winners_colored[str(winner)] = gradient
    total_winners = [[winner, winners_colored[str(winner)]] for winner in total_winners]

    total_losers = [len({**words_dict[diry]['losers'], **words_dict[diry]['out']})
                    for diry in sorted_dirs][:15]
    sorted_losers = sorted(total_losers, reverse=True)
    losers_colored = {}
    for loser, gradient in zip(sorted_losers, RED_TO_GREEN):
        losers_colored[str(loser)] = gradient
    total_losers = [[loser, losers_colored[str(loser)]] for loser in total_losers]

    total_out = [len(words_dict[diry]['out']) for diry in sorted_dirs][:15]
    sorted_out = sorted(total_out, reverse=True)
    out_colored = {}
    for out, gradient in zip(sorted_out, RED_TO_GREEN):
        out_colored[str(out)] = gradient
    total_out = [[out, out_colored[str(out)]] for out in total_out]

    total_new = [len(words_dict[diry]['new']) for diry in sorted_dirs][:15]
    sorted_new = sorted(total_new, reverse=True)
    new_colored = {}
    for new, gradient in zip(sorted_new, reversed(RED_TO_GREEN)):
        new_colored[str(new)] = gradient
    total_new = [[new, new_colored[str(new)]] for new in total_new]

    types = [words_dict[diry]['type'] for diry in sorted_dirs]

    total_traffic_diff, total_ranking = [], []
    winners_traffic, losers_traffic = [], []
    winners_traffic_dict, losers_traffic_dict = {}, {}
    winners_traffic_val, losers_traffic_val = [], []
    sub_directories, unique_urls, element_files, element_project_files = [], [], [], []
    for diry in sorted_dirs:
        winners_dict = {**words_dict[diry]['winners'], **words_dict[diry]['new']}
        losers_dict = {**words_dict[diry]['losers'], **words_dict[diry]['out']}
        common_dict = {**winners_dict, **losers_dict}
        winners = [(winner, winners_dict[winner]['traffic'])
                   for winner in winners_dict]
        losers = [(loser, losers_dict[loser]['traffic'])
                  for loser in losers_dict]
        total_traffic = [common_dict[keyword]['traffic_change'] for keyword in common_dict]
        ranking = [common_dict[keyword]['position_trend'] for keyword in common_dict]
        urls = [common_dict[keyword]['url'] for keyword in common_dict]

        element_filename = f'{diry.replace("/", "")}_{generate_random_number()}.csv'
        with open(f'{settings.REPORT_PATH}/{element_filename}', 'w+', encoding='utf-8', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(['Keyword', 'URL', 'Position', 'Position Trend', 'TableHeadTrendPositionStatus',
                                 'Traffic Index Trend', 'Search Volume'])
            keywords = []
            for keyword in common_dict:
                if keyword not in keywords:
                    keywords.append(keyword)
                    csv_writer.writerow([keyword, common_dict[keyword]['url'],
                                         common_dict[keyword]['position'],
                                         common_dict[keyword]['position_trend'],
                                         common_dict[keyword]['type'],
                                         common_dict[keyword]['traffic_change'],
                                         common_dict[keyword]['search_volume']])

        with open(f'{settings.REPORT_PATH}/{element_filename}', 'r', encoding='utf-8') as f:
            search_words_dict = {}

            df = pd.read_csv(f)
            for index, keyword in enumerate(df['Keyword']):
                search_volume = df['Search Volume'][index]
                search_words_dict[keyword] = search_volume

            sorted_words = [key for key, _ in sorted(search_words_dict.items(), key=itemgetter(1), reverse=True)]

            element_project_name = f'searchmetrics_{element_filename}.csv'
            with open(f'{settings.REPORT_PATH}/{element_project_name}', 'w+', newline='', encoding='utf-8') as f:
                project_writer = csv.writer(f)

                for word in sorted_words:
                    tags = []
                    tag_count = 0
                    try:
                        for tag in word.split():
                            tag_count += 1
                            if tag_count > 2:
                                break
                            tags.append(tag)
                    except:
                        continue

                    row = [word + ';' + ';'.join(tags) + ';']
                    project_writer.writerow(row)

        element_files.append(f'<a href="/reports/{element_filename}">Download</a>')
        element_project_files.append(f'<a href="/reports/{element_project_name}">Download</a>')

        max_winner = max(winners, key=itemgetter(1)) if winners else 0
        winners_traffic.append(max_winner[0] if winners else 0)
        winners_traffic_val.append(max_winner[1] if winners else 0)
        winners_traffic_dict[(max_winner[0], max_winner[1]) if winners else (0, 0)] = \
            max_winner[1] if winners else 0

        max_loser = max(losers, key=itemgetter(1)) if losers else 0
        losers_traffic.append(max_loser[0] if losers else 0)
        losers_traffic_val.append(max_loser[1] if losers else 0)
        losers_traffic_dict[(max_loser[0], max_loser[1]) if losers else (0, 0)] = \
            max_loser[1] if losers else 0

        total_traffic_diff.append(sum(total_traffic))
        total_ranking.append(round(sum(ranking) / len(ranking), 3) if len(ranking) != 0 else 0)
        unique_urls.append(len(set(urls)))

    data = {'Element': [directory for directory in sorted_dirs][:15],
            'Type': types[:15],
            'Total amount of keywords in Winners and Losers': total_keywords[:15],
            'Total Search Volume': total_search[:15],
            'Total amount of Winners': [winner[0] for winner in total_winners][:15],
            'Total amount of Losers': [loser[0] for loser in total_losers][:15],
            'Total Change in Traffic Index': total_traffic_diff[:15],
            'Average Ranking Change': total_ranking[:15],
            'Biggest Traffic Index Winner': winners_traffic[:15],
            'Biggest Traffic Index Loser': losers_traffic[:15],
            'Amount of keywords that no longer rank': [out[0] for out in total_out][:15],
            'Amount of newly ranking keywords': [new[0] for new in total_new][:15],
            'Amount of unique urls': unique_urls[:15]}

    df = pd.DataFrame(data=data)
    df.to_excel(writer, sheet_name='results', index=False)
    writer.save()

    sorted_traffic_diff = sorted(total_traffic_diff[:15], reverse=True)
    diff_colored = {}
    for diff, gradient in zip(sorted_traffic_diff, reversed(RED_TO_GREEN)):
        diff_colored[str(diff)] = gradient
    total_traffic_diff = [[diff, diff_colored[str(diff)]] for diff in total_traffic_diff[:15]]

    sorted_ranking = sorted(total_ranking[:15], reverse=True)
    ranking_colored = {}
    for ranking, gradient in zip(sorted_ranking, reversed(RED_TO_GREEN)):
        ranking_colored[str(ranking)] = gradient
    total_ranking = [[ranking, ranking_colored[str(ranking)]] for ranking in total_ranking[:15]]

    for dict_key in list(winners_traffic_dict):
        if dict_key[0] not in winners_traffic[:15]:
            del winners_traffic_dict[dict_key]

    sorted_winners_traffic = [(key[0], value) for key, value in sorted(winners_traffic_dict.items(),
                                                                       key=itemgetter(1), reverse=True)]
    winners_traffic_colored = {}
    for winners_traffic_elem, gradient in zip(sorted_winners_traffic, reversed(GREEN_TO_WHITE)):
        winners_traffic_colored[winners_traffic_elem] = gradient
    winners_traffic = [[winners_traffic_elem,
                        winners_traffic_colored[(winners_traffic_elem, winners_traffic_value)]]
                       for winners_traffic_elem, winners_traffic_value in
                       zip(winners_traffic[:15], winners_traffic_val)]

    for dict_key in list(losers_traffic_dict):
        if dict_key[0] not in losers_traffic[:15]:
            del losers_traffic_dict[dict_key]

    sorted_losers_traffic = [(key[0], value) for key, value in sorted(losers_traffic_dict.items(),
                                                                      key=itemgetter(1), reverse=True)]
    losers_traffic_colored = {}
    for losers_traffic_elem, gradient in zip(sorted_losers_traffic, reversed(RED_TO_WHITE)):
        losers_traffic_colored[losers_traffic_elem] = gradient
    losers_traffic = [[losers_traffic_elem,
                       losers_traffic_colored[(losers_traffic_elem, losers_traffic_value)]]
                      for losers_traffic_elem, losers_traffic_value in
                      zip(losers_traffic[:15], losers_traffic_val)]

    colored_data = {'Element': [directory for directory in sorted_dirs][:15],
                    'Type': types[:15],
                    'Total amount of keywords in Winners and Losers': total_keywords[:15],
                    'Total Search Volume': total_search[:15],
                    'Total amount of Winners': total_winners[:15],
                    'Total amount of Losers': total_losers[:15],
                    'Total Change in Traffic Index': total_traffic_diff[:15],
                    'Average Ranking Change': total_ranking[:15],
                    'Biggest Traffic Index Winner': winners_traffic[:15],
                    'Biggest Traffic Index Loser': losers_traffic[:15],
                    'Amount of keywords that no longer rank': total_out[:15],
                    'Amount of newly ranking keywords': total_new[:15],
                    'Amount of unique urls': unique_urls[:15],
                    'Element Details': element_files[:15],
                    'Element Project Details': element_project_files[:15]}

    types = ['all', 'directory', 'subdirectory', 'subdomain']
    keywords_files = []
    search_metrics_files = []
    for key_type in types:
        keyword_file = f'keywords_{key_type}.csv'
        keywords_files.append(keyword_file)
        with open(f'{settings.REPORT_PATH}/{keyword_file}', 'w+', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'URL', 'Position', 'Position Trend', 'TableHeadTrendPositionStatus',
                             'Traffic Index Trend', 'Search Volume'])
            keywords = []
            for diry in sorted_dirs:
                if words_dict[diry]['type'] == key_type or key_type is 'all':
                    winners_dict = {**words_dict[diry]['winners'], **words_dict[diry]['new']}
                    losers_dict = {**words_dict[diry]['losers'], **words_dict[diry]['out']}
                    common_dict = {**winners_dict, **losers_dict}

                    for keyword in common_dict:
                        if keyword not in keywords:
                            keywords.append(keyword)
                            writer.writerow([keyword, common_dict[keyword]['url'],
                                             common_dict[keyword]['position'],
                                             common_dict[keyword]['position_trend'],
                                             common_dict[keyword]['type'],
                                             common_dict[keyword]['traffic_change'],
                                             common_dict[keyword]['search_volume']])

        with open(f'{settings.REPORT_PATH}/{keyword_file}', 'r', encoding='utf-8') as f:
            search_words_dict = {}

            df = pd.read_csv(f)
            for index, keyword in enumerate(df['Keyword']):
                search_volume = df['Search Volume'][index]
                search_words_dict[keyword] = search_volume

            sorted_words = [key for key, _ in sorted(search_words_dict.items(), key=itemgetter(1), reverse=True)]

            file_name = f'searchmetrics_project_keyword_{key_type}.csv'
            with open(f'{settings.REPORT_PATH}/{file_name}', 'w+', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                for word in sorted_words:
                    tags = []
                    tag_count = 0
                    for tag in word.split():
                        tag_count += 1
                        if tag_count > 2:
                            break
                        tags.append(tag)

                    row = [word + ';' + ';'.join(tags) + ';']
                    writer.writerow(row)
            search_metrics_files.append(file_name)

    response = {'filename': f'{file_name}', 'data': colored_data, 'keywords_all': keywords_files[0],
                'keywords_dir': keywords_files[1], 'keywords_subdir': keywords_files[2],
                'keywords_domain': keywords_files[3],  'searchmetrics_all': search_metrics_files[0],
                'searchmetrics_dir': search_metrics_files[1], 'searchmetrics_subdir': search_metrics_files[2],
                'searchmetrics_domain': search_metrics_files[3]}

    return True, response


