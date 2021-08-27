import pandas as pd

from django.http import HttpResponse
from django.db.models import Func

from operator import itemgetter
from collections import Counter

from .helpers import generate_directories, get_domain, generate_random_number, log_to_telegram_bot


class Round(Func):
    function = 'ROUND'
    template = "%(function)s(%(expressions)s::numeric, 2)"


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/xlsx')
        response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(meta)

        data = {}
        for obj in queryset:
            for field in field_names:
                if field in data:
                    data[field].append(getattr(obj, field))
                else:
                    data[field] = [getattr(obj, field)]

        writer = pd.ExcelWriter(response, engine='xlsxwriter')
        df = pd.DataFrame(data=data)
        df['created_at'] = df['created_at'].apply(lambda a: pd.to_datetime(a).date())
        df['updated_at'] = df['updated_at'].apply(lambda a: pd.to_datetime(a).date())
        df.to_excel(writer, sheet_name='results', index=False)
        writer.save()

        return response

    export_as_csv.short_description = "Export Selected as CSV"


class CorrelationExport:
    def export_correlation(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(meta)

        data = {}
        for obj in queryset:
            for field in field_names:
                if field in data:
                    data[field].append(getattr(obj, field))
                else:
                    data[field] = [getattr(obj, field)]

        writer = pd.ExcelWriter(response, engine='xlsxwriter')
        df = pd.DataFrame(data=data)
        features = ['position', 'cumulative_ls', 'largest_cp', 'max_potential_fid']
        new_df = df[features].corr()
        new_df.to_excel(writer, sheet_name='correlation', index=True)
        writer.save()

        return response

    export_correlation.short_description = "Correlation Export"


class ExportAsURLGroups:
    def export_as_searchmetrics_csv(self, request, queryset):
        domain_filter = request.GET.get('domain')
        if not domain_filter:
            return

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        filename = f"domain_data_{generate_random_number()}.xlsx"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)

        words_dict = {}
        for obj in queryset:
            for field in field_names:
                url = getattr(obj, 'url')
                if url in words_dict:
                    words_dict[url][field] = getattr(obj, field)
                else:
                    words_dict[url] = {field: getattr(obj, field)}

        result_data = {}
        for key in words_dict:
            dirs = generate_directories(key)
            domain = get_domain(f'https://{key}')
            if domain.replace("www.", "") == domain_filter:
                for index, diry in enumerate(dirs):
                    current_elem = words_dict[key]
                    if diry:
                        if diry not in result_data:
                            dir_type = 'directory' if index == 0 else 'subdirectory'
                            result_data[diry] = {'type': dir_type, 'elements': [current_elem]}
                        else:
                            result_data[diry]['elements'].append(current_elem)

        columns = {'position': [], 'traffic_index': [], 'search_volume': [],
                   'trend': [], 'cpc': [], 'competition': [], 'hrk': [], 'integration': []}
        for key in result_data:
            keywords = [elem['keyword'] for elem in result_data[key]['elements']]
            parameters = {'position': [], 'traffic_index': [], 'search_volume': [],
                          'trend': [], 'cpc': [], 'competition': [], 'integration': []}
            for elem in result_data[key]['elements']:
                for parameter in parameters:
                    if parameter is not 'integration':
                        parameters[parameter].append(elem[parameter])
                parameters['integration'] += elem['integration'].split(',')
            for parameter in parameters:
                if parameter is not 'integration':
                    columns[parameter].append(round(sum(parameters[parameter]) / len(parameters[parameter]), 2))
            columns['hrk'].append(keywords[parameters['trend'].index(max(parameters['trend']))])
            if all(parameters['integration']):
                integ_counter = Counter(parameters['integration'])
                integ_keys = integ_counter.keys()
                columns['integration'].append(",".join(integ_keys))
            else:
                columns['integration'].append(None)

        all_integration = [integ for integration in columns['integration'] if integration
                           for integ in integration.split(',')]
        integ_counter = Counter(all_integration)
        integ_keys = integ_counter.keys()
        integ_columns = {}
        for integ_key in integ_keys:
            integ_columns[integ_key] = []
            for integ in columns['integration']:
                if integ:
                    integrations = integ.split(",")
                    integration_percent = round(integrations.count(integ_key) / len(integrations) * 100, 2)
                    integ_columns[integ_key].append(integration_percent)
                else:
                    integ_columns[integ_key].append(None)

        columns["keywords_num"] = []
        for key in result_data:
            columns["keywords_num"].append(len(result_data[key]['elements']))

        columns['elements'] = [key for key in result_data]
        columns['types'] = [result_data[key]['type'] for key in result_data]

        numerated_elems = [(index, num) for index, num in enumerate(columns["keywords_num"])]
        sorted_keys = [key for key, _ in sorted(numerated_elems, key=itemgetter(1), reverse=True)]

        for key in columns:
            temp = [columns[key][num] for num in sorted_keys]
            columns[key] = temp

        writer = pd.ExcelWriter(response, engine='xlsxwriter')
        data = {'Elements': columns['elements'], 'Type': columns['types'], 'Avg. Position': columns['position'],
                'Avg. Traffic Index': columns['traffic_index'], 'Avg. Search Volume': columns['search_volume'],
                'Avg. Trend': columns['trend'], 'Avg. Competition': columns['competition'],
                'Highest ranking keyword': columns['hrk'], 'Integration': columns['integration'],
                'Avg. CPC': columns['cpc'], 'Number of keywords': columns["keywords_num"]}

        df = pd.DataFrame(data=data)
        df.to_excel(writer, sheet_name='results', index=False)

        data = {'Elements': columns['elements'], 'Type': columns['types'], **integ_columns}
        df = pd.DataFrame(data=data)
        df.to_excel(writer, sheet_name='integration', index=False)
        writer.save()

        return response

    export_as_searchmetrics_csv.short_description = "Export Selected Domain with URL grouping"