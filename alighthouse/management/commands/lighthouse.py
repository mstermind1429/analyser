import logging

import pandas as pd
from lighthouse import LighthouseRunner

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError
from alighthouse.models import *


numeric_aspects = {"first-contentful-paint": "first_cp", "largest-contentful-paint": "largest_cp",
                   "first-meaningful-paint": "first_mp", "speed-index": "speed_index",
                   "estimated-input-latency": "estimated_il", "total-blocking-time": "total_blocking_time",
                   "max-potential-fid": "max_potential_fid", "cumulative-layout-shift": "cumulative_ls",
                   "server-response-time": "server_response_time", "first-cpu-idle": "first_cpu_idle",
                   "interactive": "interactive", "redirects": "redirects",
                   "mainthread-work-breakdown": "mainthread_work_breakdown", "bootup-time": "bootup_time",
                   "uses-rel-preload": "uses_rel_preload", "network-rtt": "network_rtt",
                   "network-server-latency": "network_sl", "uses-long-cache-ttl": "long_cache_ttl"}

items = {"bootup-time": LighthouseReportBootupItems, "diagnostics": LighthouseReportDiagnosticsItems,
         "network-requests": LighthouseReportNetworkReqItems, "network-rtt": LighthouseReportNetworkRttItems,
         "network-server-latency": LighthouseReportNetworkSLItems, "long-tasks": LighthouseReportLongTaskItem,
         "offscreen-images": LighthouseReportOffscreenImagesItem}

FILE_PATH = settings.REPORT_PATH + '/urls_lighthouse.csv'


logger = logging.getLogger('django')


class Command(BaseCommand):
    help = "Get Lighthouse data"

    def handle(self, *args, **options):
        df = pd.read_csv(FILE_PATH)

        for url, keyword, position in zip(df["URL"], df["Keyword"], df["Position"]):
            url = "https://" + url
            report_types = ['mobile']

            for report_type in report_types:

                try:
                    report = LighthouseRunner(url, form_factor=report_type, quiet=False).report
                except Exception as e:
                    logger.info(e)
                    continue

                audits = report.get_audits()
                content_type, node = None, None
                try:
                    node = audits['largest-contentful-paint-element']['details']['items'][0]['node']['snippet']
                    node.replace('{', '').replace('}', '')
                    content_type = 'image'
                except Exception as e:
                    logger.info(e)
                    try:
                        node = audits['largest-contentful-paint-element']['details']['items'][0]['node']['nodeLabel']
                        node.replace('{', '').replace('}', '')
                        content_type = 'node'
                    except Exception as e:
                        logger.info(e)

                lighthouse_report = {}
                for key in numeric_aspects:
                    try:
                        lighthouse_report[numeric_aspects[key]] = round(audits[key]['numericValue'], 3)
                    except KeyError:
                        logger.info(key, ': Key Error')
                        continue

                lighthouse_report['domain'] = 'taz.de'
                lighthouse_report['url'] = url
                lighthouse_report['keyword'] = keyword
                lighthouse_report['type'] = report_type
                lighthouse_report['position'] = position
                lighthouse_report['content_type'] = content_type
                lighthouse_report['largest_cp_element'] = node

                try:
                    lighthouse_report = LighthouseReport.objects.create(**lighthouse_report)
                except IntegrityError:
                    logger.info(lighthouse_report['domain'], ': Integrity Error')
                    lighthouse_report = LighthouseReport.objects.filter(domain='taz.de', url=url, keyword=keyword)

                    if not lighthouse_report:
                        continue

                for key in ["screenshot-thumbnails", "final-screenshot"]:
                    try:
                        for item in audits[key]['details']['items']:
                            lighthouse_item = {}
                            for aspect in item:
                                if type(item[aspect]) == str:
                                    if '{' in item[aspect] or '}' in item[aspect]:
                                        continue
                                if aspect == 'data':
                                    lighthouse_item["content_type"] = item[aspect].split(";")[0]
                                    lighthouse_item["data"] = item[aspect].split(";")[1]
                                    continue
                                lighthouse_item[aspect] = item[aspect]

                            lighthouse_item["report"] = lighthouse_report

                            LighthouseReportItem.objects.create(**lighthouse_item)
                    except (KeyError, ValueError) as e:
                        logger.info(e)
                        continue

                for key in items:
                    try:
                        for item in audits[key]['details']['items']:
                            lighthouse_item = {}
                            for aspect in item:
                                if type(item[aspect]) == str:
                                    if '{' in item[aspect] or '}' in item[aspect]:
                                        continue
                                lighthouse_item[aspect] = round(item[aspect], 2) if type(item[aspect]) == float \
                                    else item[aspect]
                            lighthouse_item["report"] = lighthouse_report

                            items[key].objects.create(**lighthouse_item)
                    except (KeyError, ValueError) as e:
                        logger.info(e)
                        continue

                try:
                    for item in audits["layout-shift-elements"]['details']['items']:
                        node = item["node"]
                        lighthouse_item = {}
                        for aspect in node:
                            if aspect != "boundingRect":
                                if type(node[aspect]) == str:
                                    if '{' in node[aspect] or '}' in node[aspect]:
                                        continue
                                lighthouse_item[aspect] = round(node[aspect], 2) if type(node[aspect]) == float \
                                    else node[aspect]
                        lighthouse_item["report"] = lighthouse_report

                        LighthouseReportLayoutElementsItem.objects.create(**lighthouse_item)
                except (KeyError, ValueError) as err:
                    logger.info(err)
                    continue
