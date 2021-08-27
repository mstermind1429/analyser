import datetime

from django.contrib.admin import SimpleListFilter


class InformationalIntentFilter(SimpleListFilter):
    title = 'Informational Intent'
    parameter_name = 'informational_intent'

    def lookups(self, request, model_admin):
        return [
            ('lte_0.4', 'LESS THAN 0.4'),
            ('gt_0.4', 'MORE THAN 0.4')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_0.4':
            return queryset.filter(informational_intent__lte=0.4)
        if self.value():
            return queryset.filter(informational_intent__gt=0.4)


class NavigationalIntentFilter(SimpleListFilter):
    title = 'Navigational Intent'
    parameter_name = 'navigational_intent'

    def lookups(self, request, model_admin):
        return [
            ('lte_0.4', 'LESS THAN 0.4'),
            ('gt_0.4', 'MORE THAN 0.4')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_0.4':
            return queryset.filter(navigational_intent__lte=0.4)
        if self.value():
            return queryset.filter(navigational_intent__gt=0.4)


class TransactionalIntentFilter(SimpleListFilter):
    title = 'Transactional Intent'
    parameter_name = 'transactional_intent'

    def lookups(self, request, model_admin):
        return [
            ('lte_0.4', 'LESS THAN 0.4'),
            ('gt_0.4', 'MORE THAN 0.4')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_0.4':
            return queryset.filter(transactional_intent__lte=0.4)
        if self.value():
            return queryset.filter(transactional_intent__gt=0.4)


class ControlledFilter(SimpleListFilter):
    title = 'Controlled'
    parameter_name = 'controlled'

    def lookups(self, request, model_admin):
        return [
            ('lte_30', 'LESS THAN 30%'),
            ('gt_30', 'MORE THAN 30%')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_30':
            return queryset.filter(controlled__lte=30)
        if self.value():
            return queryset.filter(controlled__gt=30)


class NeitherFilter(SimpleListFilter):
    title = 'Neither'
    parameter_name = 'neither'

    def lookups(self, request, model_admin):
        return [
            ('lte_30', 'LESS THAN 30%'),
            ('gt_30', 'MORE THAN 30%')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_30':
            return queryset.filter(neither__lte=30)
        if self.value():
            return queryset.filter(neither__gt=30)


class AffectedFilter(SimpleListFilter):
    title = 'Affected'
    parameter_name = 'affected'

    def lookups(self, request, model_admin):
        return [
            ('lte_30', 'LESS THAN 30%'),
            ('gt_30', 'MORE THAN 30%')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_30':
            return queryset.filter(affected__lte=30)
        if self.value():
            return queryset.filter(affected__gt=30)


class MaleFilter(SimpleListFilter):
    title = 'Male'
    parameter_name = 'male'

    def lookups(self, request, model_admin):
        return [
            ('lte_10', 'LESS THAN 10%'),
            ('gt_10', 'MORE THAN 10%')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_10':
            return queryset.filter(male__lte=10)
        if self.value():
            return queryset.filter(male__gt=10)


class FemaleFilter(SimpleListFilter):
    title = 'Female'
    parameter_name = 'female'

    def lookups(self, request, model_admin):
        return [
            ('lte_10', 'LESS THAN 10%'),
            ('gt_10', 'MORE THAN 10%')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_10':
            return queryset.filter(female__lte=10)
        if self.value():
            return queryset.filter(female__gt=10)


class RelatedFilter(SimpleListFilter):
    title = 'Related'
    parameter_name = 'related'

    def lookups(self, request, model_admin):
        return [
            ('lte_3', 'LESS THAN 3'),
            ('gt_3', 'MORE THAN 3')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_3':
            return queryset.filter(related__lte=3)
        if self.value():
            return queryset.filter(related__gt=3)


class StackedFilter(SimpleListFilter):
    title = 'Stacked'
    parameter_name = 'stacked'

    def lookups(self, request, model_admin):
        return [
            ('lte_3', 'LESS THAN 3'),
            ('gt_3', 'MORE THAN 3')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_3':
            return queryset.filter(stacked__lte=3)
        if self.value():
            return queryset.filter(stacked__gt=3)


class AdsFilter(SimpleListFilter):
    title = 'Ads'
    parameter_name = 'ads'

    def lookups(self, request, model_admin):
        return [
            ('lte_2', 'LESS THAN 2'),
            ('gt_2', 'MORE THAN 2')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_2':
            return queryset.filter(ads__lte=2)
        if self.value():
            return queryset.filter(sads__gt=2)


class Pos1Filter(SimpleListFilter):
    title = 'Pos 1'
    parameter_name = 'pos_1'

    def lookups(self, request, model_admin):
        return [
            ('lte_2', 'LESS THAN 2'),
            ('gt_2', 'MORE THAN 2')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_2':
            return queryset.filter(pos_1__lte=2)
        if self.value():
            return queryset.filter(pos_1__gt=2)


class Pos2Filter(SimpleListFilter):
    title = 'Pos 2'
    parameter_name = 'pos_2'

    def lookups(self, request, model_admin):
        return [
            ('lte_4', 'LESS THAN 4'),
            ('gt_4', 'MORE THAN 4')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_4':
            return queryset.filter(pos_2__lte=4)
        if self.value():
            return queryset.filter(pos_2__gt=4)


class Pos3Filter(SimpleListFilter):
    title = 'Pos 3'
    parameter_name = 'pos_3'

    def lookups(self, request, model_admin):
        return [
            ('lte_6', 'LESS THAN 6'),
            ('gt_6', 'MORE THAN 6')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'lte_6':
            return queryset.filter(pos_3__lte=6)
        if self.value():
            return queryset.filter(pos_3__gt=6)


class ReportFilter(SimpleListFilter):
    title = 'Report'
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return [
            ('202022_report', '202022 report'),
            ('202034_report', '202034 report')
        ]

    def queryset(self, request, queryset):
        if self.value() == '202022_report':
            query = queryset.filter(date='202034')
            keywords = [item.keyword for item in query]

            return queryset.exclude(keyword__in=keywords).filter(date='202022').distinct()
        if self.value():
            query = queryset.filter(date='202022')
            keywords = [item.keyword for item in query]

            return queryset.exclude(keyword__in=keywords).filter(date='202034').distinct()


class PositionFilter(SimpleListFilter):
    title = 'Position'
    parameter_name = 'position'

    def lookups(self, request, model_admin):
        return [
            ('i_lte_5', 'INCLUDE LESS THAN 5'),
            ('i_gt_5', 'INCLUDE MORE THAN 5'),
            ('e_lte_5', 'EXCLUDE LESS THAN 5'),
            ('e_gt_5', 'EXCLUDE MORE THAN 5'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'i_lte_5':
            return queryset.filter(position__lte=5)
        if self.value() == 'i_gt_5':
            return queryset.filter(position__gt=5)
        if self.value() == 'e_lte_5':
            return queryset.exclude(position__lte=5)
        if self.value() == 'e_gt_5':
            return queryset.exclude(position__gt=5)


class TrafficIndexFilter(SimpleListFilter):
    title = 'Traffic Index'
    parameter_name = 'traffic_index'

    def lookups(self, request, model_admin):
        return [
            ('i_lte_8000', 'INCLUDE LESS THAN 8000'),
            ('i_gt_8000', 'INCLUDE MORE THAN 8000'),
            ('e_lte_8000', 'EXCLUDE LESS THAN 8000'),
            ('e_gt_8000', 'EXCLUDE MORE THAN 8000'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'i_lte_8000':
            return queryset.filter(traffic_index__lte=8000)
        if self.value() == 'i_gt_8000':
            return queryset.filter(traffic_index__gt=8000)
        if self.value() == 'e_lte_8000':
            return queryset.exclude(traffic_index__lte=8000)
        if self.value() == 'e_gt_8000':
            return queryset.exclude(traffic_index__gt=8000)


class SearchVolumeFilter(SimpleListFilter):
    title = 'Search Volume'
    parameter_name = 'search_volume'

    def lookups(self, request, model_admin):
        return [
            ('i_lte_15000', 'INCLUDE LESS THAN 15000'),
            ('i_gt_15000', 'INCLUDE MORE THAN 15000'),
            ('e_lte_15000', 'EXCLUDE LESS THAN 15000'),
            ('e_gt_15000', 'EXCLUDE MORE THAN 15000'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'i_lte_15000':
            return queryset.filter(search_volume_lte=15000)
        if self.value() == 'i_gt_15000':
            return queryset.filter(search_volume__gt=15000)
        if self.value() == 'e_lte_15000':
            return queryset.exclude(search_volume__lte=15000)
        if self.value() == 'e_gt_15000':
            return queryset.exclude(search_volume__gt=15000)


class TrendFilter(SimpleListFilter):
    title = 'Trend'
    parameter_name = 'trend'

    def lookups(self, request, model_admin):
        return [
            ('i_lte_3', 'INCLUDE LESS THAN 3'),
            ('i_gt_3', 'INCLUDE MORE THAN 3'),
            ('e_lte_3', 'EXCLUDE LESS THAN 3'),
            ('e_gt_3', 'EXCLUDE MORE THAN 3'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'i_lte_3':
            return queryset.filter(trend_lte=3)
        if self.value() == 'i_gt_3':
            return queryset.filter(trend__gt=3)
        if self.value() == 'e_lte_3':
            return queryset.exclude(trend__lte=3)
        if self.value() == 'e_gt_3':
            return queryset.exclude(trend__gt=3)


class CpcFilter(SimpleListFilter):
    title = 'Cpc'
    parameter_name = 'cpc'

    def lookups(self, request, model_admin):
        return [
            ('i_lte_0.5', 'INCLUDE LESS THAN 0.5'),
            ('i_gt_0.5', 'INCLUDE MORE THAN 0.5'),
            ('e_lte_0.5', 'EXCLUDE LESS THAN 0.5'),
            ('e_gt_0.5', 'EXCLUDE MORE THAN 0.5'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'i_lte_0.5':
            return queryset.filter(cpc_lte=0.5)
        if self.value() == 'i_gt_0.5':
            return queryset.filter(cpc__gt=0.5)
        if self.value() == 'e_lte_0.5':
            return queryset.exclude(cpc__lte=0.5)
        if self.value() == 'e_gt_0.5':
            return queryset.exclude(cpc__gt=0.5)


class CompetitionFilter(SimpleListFilter):
    title = 'Competition'
    parameter_name = 'competition'

    def lookups(self, request, model_admin):
        return [
            ('i_lte_3', 'INCLUDE LESS THAN 3'),
            ('i_gt_3', 'INCLUDE MORE THAN 3'),
            ('e_lte_3', 'EXCLUDE LESS THAN 3'),
            ('e_gt_3', 'EXCLUDE MORE THAN 3'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'i_lte_3':
            return queryset.filter(competition_lte=3)
        if self.value() == 'i_gt_3':
            return queryset.filter(competition__gt=3)
        if self.value() == 'e_lte_3':
            return queryset.exclude(competition__lte=3)
        if self.value() == 'e_gt_3':
            return queryset.exclude(competition__gt=3)


class IntegrationFilter(SimpleListFilter):
    title = 'Integration'
    parameter_name = 'integration'

    def lookups(self, request, model_admin):
        integration_tags = set([tag for c in model_admin.model.objects.all() for tag in c.integration.split(",")])
        return [(tag, tag) for tag in integration_tags]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(integration__contains=self.value())
        else:
            return queryset


class LighthouseDateFilter(SimpleListFilter):
    title = 'Date'
    parameter_name = 'created_at'

    def lookups(self, request, model_admin):
        dates = [c.created_at.strftime('%Y-%m-%d') for c in model_admin.model.objects.all()]
        dates.sort(key=lambda date: datetime.datetime.strptime(date, '%Y-%m-%d'))
        dates = set(dates)
        return [(date, date) for date in dates]

    def queryset(self, request, queryset):
        if self.value():
            date = datetime.datetime.strptime(self.value(), '%Y-%m-%d')
            return queryset.filter(created_at__year=str(date.year),
                                   created_at__month=str(date.month),
                                   created_at__day=str(date.day))
        else:
            return queryset
