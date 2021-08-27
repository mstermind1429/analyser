from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
from django.db.models import Avg

from admin_totals.admin import ModelAdminTotals

from core.actions import ExportCsvMixin, CorrelationExport, Round
from core.filters import *
from .models import *
from .actions import ExportAsPPT, ComparingExport
from .core import run_domain_lighthouse


class ItemInline(admin.TabularInline):
    model = LighthouseReportItem
    extra = 0
    classes = ['collapse']


class BootupTimeInline(admin.TabularInline):
    model = LighthouseReportBootupItems
    extra = 0
    classes = ['collapse']


class DiagnosticsInline(admin.TabularInline):
    model = LighthouseReportDiagnosticsItems
    extra = 0
    classes = ['collapse']


class NetworkReqInline(admin.TabularInline):
    model = LighthouseReportNetworkReqItems
    extra = 0
    classes = ['collapse']


class NetworkRttInline(admin.TabularInline):
    model = LighthouseReportNetworkRttItems
    extra = 0
    classes = ['collapse']


class NetworkSLInline(admin.TabularInline):
    model = LighthouseReportNetworkSLItems
    extra = 0
    classes = ['collapse']


class LongTasksInline(admin.TabularInline):
    model = LighthouseReportLongTaskItem
    extra = 0
    classes = ['collapse']


class OffscreenImagesInline(admin.TabularInline):
    model = LighthouseReportOffscreenImagesItem
    extra = 0
    classes = ['collapse']


class LayoutElementsInline(admin.TabularInline):
    model = LighthouseReportLayoutElementsItem
    extra = 0
    classes = ['collapse']


class UnminifiedJSInline(admin.TabularInline):
    model = LighthouseReportUnminifiedJS
    extra = 0
    classes = ['collapse']


class UnminifiedCSSInline(admin.TabularInline):
    model = LighthouseReportUnminifiedCSS
    extra = 0
    classes = ['collapse']


class UnusedCSSRuleInline(admin.TabularInline):
    model = LighthouseReportUnusedCSSRule
    extra = 0
    classes = ['collapse']


@admin.register(LighthouseReport)
class LighthouseReportAdmin(ExportCsvMixin, ModelAdminTotals, CorrelationExport, ExportAsPPT):
    inlines = [
        ItemInline,
        BootupTimeInline,
        DiagnosticsInline,
        NetworkReqInline,
        NetworkRttInline,
        NetworkSLInline,
        LongTasksInline,
        OffscreenImagesInline,
        LayoutElementsInline,
        UnminifiedCSSInline,
        UnminifiedJSInline,
        UnusedCSSRuleInline,
    ]
    search_fields = ['domain', 'keyword', 'url']
    list_filter = ('domain', 'type', 'content_type', LighthouseDateFilter)
    list_totals = [('position', lambda field: Round(Avg(field))), ('largest_cp', lambda field: Round(Avg(field))),
                   ('first_cp', lambda field: Round(Avg(field))),
                   ('first_mp', lambda field: Round(Avg(field))),
                   ('speed_index', lambda field: Round(Avg(field))), ('female', lambda field: Round(Avg(field))),
                   ('estimated_il', lambda field: Round(Avg(field))),
                   ('total_blocking_time', lambda field: Round(Avg(field)))]
    actions = ["export_as_csv", "export_correlation", "export_as_ppt"]

    list_display = ('url', 'keyword', 'domain', 'type', 'position', 'first_cp', 'largest_cp', 'first_mp',
                    'speed_index', 'estimated_il', 'total_blocking_time', 'max_potential_fid', 'cumulative_ls',
                    'server_response_time', 'first_cpu_idle', 'interactive', 'redirects', 'mainthread_work_breakdown',
                    'bootup_time', 'uses_rel_preload', 'network_rtt', 'network_sl', 'content_type',
                    'long_cache_ttl', 'lcp_score', 'fid_score', 'cls_score', 'created_at', 'updated_at')

    def show_file_url(self, obj):
        return format_html(obj.largest_cp_element)

    show_file_url.short_description = 'Largest CP Element'


@admin.register(MonthlyDomain)
class MonthlyDomainAdmin(admin.ModelAdmin, ComparingExport):
    list_display = ('domain', 'country_code', 'keywords_amount')

    actions = ['comparing_export']
    form = MonthlyDomainForm

    def save_model(self, request, obj, form, change):
        run_domain_lighthouse(settings.SEARCH_METRICS_KEY, settings.SEARCH_METRICS_SECRET,
                              obj.keywords_amount, obj.country_code, obj.domain,
                              schedule=0, repeat=604800)
        super().save_model(request, obj, form, change)
