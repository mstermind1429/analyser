from operator import itemgetter
import pandas as pd

from django.http import HttpResponse

from core.helpers import generate_directories, log_to_telegram_bot
from .core import create_lighthouse_ppt
from .models import LighthouseReport


class ExportAsPPT:
    def export_as_ppt(self, request, queryset):
        meta = self.model._meta
        domain_filter = request.GET.get('domain')

        if not domain_filter:
            return

        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.pptx'.format(meta)

        data = {}
        for obj in queryset:
            for field in field_names:
                if field in data:
                    data[field].append(getattr(obj, field))
                else:
                    data[field] = [getattr(obj, field)]

        df = pd.DataFrame(data=data)

        create_lighthouse_ppt(df, response, domain_filter)

        return response

    export_as_ppt.short_description = "Export as PPT"


class ComparingExport:
    def comparing_export(self, request, queryset):
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

        domain = data['domain'][0]
        fields = [field.name for field in LighthouseReport._meta.fields]
        fields_remove = ['id', 'domain', 'keyword', 'url', 'type', 'content_type',
                         'largest_cp_element', 'created_at', 'updated_at']
        for field_remove in fields_remove:
            fields.remove(field_remove)

        reports = LighthouseReport.objects.filter(domain=domain)
        directories_dict = {}
        for report in reports:
            if report.url.find(domain) != -1:
                directories = generate_directories(report.url)
                date = report.created_at.strftime('%Y-%m-%d')

                for dir_index, directory in enumerate(directories):
                    directory = '.' if not directory else directory

                    if directory not in directories_dict:
                        directories_dict[directory] = {}

                    if 'count' in directories_dict[directory]:
                        directories_dict[directory]['count'] += 1
                    else:
                        directories_dict[directory]['count'] = 1

                    if date not in directories_dict[directory]:
                        directories_dict[directory][date] = {}

                    if 'count' in directories_dict[directory][date]:
                        directories_dict[directory][date]['count'] += 1
                    else:
                        directories_dict[directory][date]['count'] = 1

                    for field in fields:
                        if field in directories_dict[directory][date]:
                            if type(getattr(report, field)) in [float, int]:
                                directories_dict[directory][date][field] += getattr(report, field) \
                                    if getattr(report, field) else 0
                        else:
                            directories_dict[directory][date][field] = getattr(report, field) \
                                if getattr(report, field) else 0

        for directory in directories_dict:
            for date in directories_dict[directory]:
                if date is not 'count':
                    for field in directories_dict[directory][date]:
                        if field is not 'count':
                            directories_dict[directory][date][field] = round(directories_dict[directory][date][field] /
                                                                             directories_dict[directory][date]['count'],
                                                                             2) \
                                if directories_dict[directory][date]['count'] != 0 else 0

        directories = [(directory, directories_dict[directory]['count']) for directory in directories_dict]
        sorted_directories = [key for key, _ in sorted(directories, key=itemgetter(1), reverse=True)]

        writer = pd.ExcelWriter(response, engine='xlsxwriter')
        for page_type in sorted_directories[:20]:
            data = {}
            dates = []
            if len(directories_dict[page_type].keys()) > 2:
                for date in directories_dict[page_type]:
                    if date is not 'count':
                        dates.append(date)
                        for field in directories_dict[page_type][date]:
                            if field in data:
                                data[field].append(directories_dict[page_type][date][field])
                            else:
                                data[field] = [directories_dict[page_type][date][field]]

                for field in data:
                    change_percent = round((data[field][-1] - data[field][0]) / data[field][0] * 100, 2) \
                        if data[field][0] else 0
                    data[field].append(change_percent)

                dates.append('Change % (first - last)')
                if data:
                    log_to_telegram_bot(f"{data}, {dates}")
                    df = pd.DataFrame(data=data, index=dates)
                    df.to_excel(writer, sheet_name=page_type, index=True)

        writer.save()

        return response

    comparing_export.short_description = "Comparing Export"
