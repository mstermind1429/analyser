import re

from django.conf import settings

import requests
from selenium import webdriver

from core.helpers import generate_random_number


def get_html_page(url: str):
    driver = webdriver.PhantomJS()
    driver.get(url)
    content = driver.page_source

    filename = f'html_get_{generate_random_number()}.html'
    with open(f'{settings.REPORT_PATH}/{filename}', 'w+',
              newline='',
              encoding='utf-8') as f:
        f.write(content)

    return filename


def get_html_snippets(
        url: str,
        snippet: str,
        post_render: bool
):
    if post_render:
        driver = webdriver.PhantomJS()
        driver.get(url)
        content = driver.page_source
    else:
        page = requests.session().get(url=url)
        try:
            content = page.content.decode()
        except UnicodeDecodeError:
            content = page.content.decode('Windows-1251')

    snippet = snippet.replace("/", "\/").replace("*", "(.*?)")
    if snippet.find("##") == -1:
        if re.findall(snippet, content, re.DOTALL):
            return True
        return False
    else:
        snippet = snippet.replace("##", "(.*?)")
        founded_patterns = re.findall(snippet, content, re.DOTALL)
        if founded_patterns:
            return {
                'patterns': founded_patterns
            }
        return False
