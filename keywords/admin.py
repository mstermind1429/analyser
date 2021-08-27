from django.contrib import admin
from django.db.models import Avg

from admin_totals.admin import ModelAdminTotals

from core.actions import ExportCsvMixin, ExportAsURLGroups, Round
from core.filters import *
from .models import DomainData


@admin.register(DomainData)
class DomainDataAdmin(ExportCsvMixin, ExportAsURLGroups, ModelAdminTotals):
    search_fields = ['keyword', 'url']
    list_filter = ('domain', PositionFilter, TrafficIndexFilter, SearchVolumeFilter,
                   TrendFilter, CpcFilter, CompetitionFilter, IntegrationFilter)
    list_totals = [('position', lambda field: Round(Avg(field))), ('affected', lambda field: Round(Avg(field))),
                   ('traffic_index', lambda field: Round(Avg(field))),
                   ('search_volume', lambda field: Round(Avg(field))),
                   ('trend', lambda field: Round(Avg(field))), ('female', lambda field: Round(Avg(field))),
                   ('cpc', lambda field: Round(Avg(field))),
                   ('competition', lambda field: Round(Avg(field)))]
    actions = ["export_as_csv", "export_as_searchmetrics_csv"]

    list_display = ('url', 'keyword', 'domain', 'position', 'title', 'traffic_index', 'search_volume', 'trend',
                    'integration', 'cpc', 'competition')


