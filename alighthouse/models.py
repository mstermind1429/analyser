from django.db import models
from django import forms

class LighthouseReport(models.Model):
    domain = models.CharField(max_length=512)
    keyword = models.CharField(max_length=512)
    url = models.CharField(max_length=1024)
    type = models.CharField(max_length=7)
    position = models.IntegerField()
    first_cp = models.FloatField(null=True)
    lcp_score = models.FloatField(
        null=True,
        default=0
    )
    fid_score = models.FloatField(
        null=True,
        default=0
    )
    cls_score = models.FloatField(
        null=True,
        default=0
    )
    largest_cp = models.FloatField(null=True)
    first_mp = models.FloatField(null=True)
    speed_index = models.FloatField(null=True)
    estimated_il = models.FloatField(null=True)
    total_blocking_time = models.FloatField(null=True)
    max_potential_fid = models.FloatField(null=True)
    cumulative_ls = models.FloatField(null=True)
    server_response_time = models.FloatField(null=True)
    first_cpu_idle = models.FloatField(null=True)
    interactive = models.FloatField(null=True)
    redirects = models.FloatField(null=True)
    mainthread_work_breakdown = models.FloatField(null=True)
    bootup_time = models.FloatField(null=True)
    uses_rel_preload = models.FloatField(null=True)
    network_rtt = models.FloatField(null=True)
    network_sl = models.FloatField(null=True)
    content_type = models.CharField(max_length=5)
    largest_cp_element = models.CharField(
        max_length=8192,
        null=True,
        default=None
    )
    long_cache_ttl = models.FloatField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lighthouse Report"
        unique_together = ('domain', 'keyword', 'url')

    def __str__(self):
        return self.domain


class LighthouseReportItem(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    timing = models.IntegerField()
    timestamp = models.CharField(max_length=512)
    content_type = models.CharField(max_length=100)
    data = models.CharField(max_length=8192)

    class Meta:
        verbose_name = "Lighthouse Report Item"

    def __str__(self):
        return self.timestamp


class LighthouseReportBootupItems(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    url = models.CharField(max_length=8192)
    total = models.FloatField()
    scripting = models.FloatField()
    scriptParseCompile = models.FloatField()

    class Meta:
        verbose_name = "Lighthouse Report Bootup Item"

    def __str__(self):
        return self.url


class LighthouseReportDiagnosticsItems(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    numRequests = models.IntegerField()
    numScripts = models.IntegerField()
    numStylesheets = models.IntegerField()
    numFonts = models.IntegerField()
    numTasks = models.IntegerField()
    numTasksOver10ms = models.IntegerField()
    numTasksOver25ms = models.IntegerField()
    numTasksOver50ms = models.IntegerField()
    numTasksOver100ms = models.IntegerField()
    numTasksOver500ms = models.IntegerField()
    rtt = models.FloatField()
    throughput = models.FloatField()
    maxRtt = models.FloatField()
    maxServerLatency = models.FloatField()
    totalByteWeight = models.FloatField()
    totalTaskTime = models.FloatField()
    mainDocumentTransferSize = models.FloatField()

    class Meta:
        verbose_name = "Lighthouse Report Diagnostics Item"

    def __str__(self):
        return str(self.numRequests)


class LighthouseReportNetworkReqItems(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    url = models.CharField(max_length=8192)
    startTime = models.FloatField(null=True)
    endTime = models.FloatField(null=True)
    finished = models.BooleanField(
        default=False,
        null=True
    )
    statusCode = models.IntegerField(null=True)
    transferSize = models.IntegerField(null=True)
    resourceSize = models.IntegerField(null=True)
    mimeType = models.CharField(
        null=True,
        max_length=128
    )
    resourceType = models.CharField(
        null=True,
        max_length=1024
    )
    protocol = models.CharField(
        null=True,
        max_length=1024
    )

    class Meta:
        verbose_name = "Lighthouse Report Network Req Item"

    def __str__(self):
        return self.url


class LighthouseReportNetworkRttItems(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    origin = models.CharField(
        max_length=2048,
        null=True
    )
    rtt = models.FloatField(null=True)

    class Meta:
        verbose_name = "Lighthouse Report Network Rtt Item"

    def __str__(self):
        return self.origin


class LighthouseReportNetworkSLItems(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    origin = models.CharField(max_length=2048)
    serverResponseTime = models.FloatField(null=True)

    class Meta:
        verbose_name = "Lighthouse Report Network Rtt Item"

    def __str__(self):
        return self.origin


class LighthouseReportLongTaskItem(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    url = models.CharField(max_length=8192)
    startTime = models.FloatField(null=True)
    duration = models.FloatField(null=True)

    class Meta:
        verbose_name = "Lighthouse Report Long Task Item"

    def __str__(self):
        return self.url


class LighthouseReportOffscreenImagesItem(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    url = models.CharField(max_length=8192)
    requestStartTime = models.FloatField(null=True)
    wastedPercent = models.FloatField(null=True)
    totalBytes = models.FloatField(null=True)
    wastedBytes = models.FloatField(null=True)

    class Meta:
        verbose_name = "Lighthouse Report Offscreen Images Item"

    def __str__(self):
        return self.url


class LighthouseReportLayoutElementsItem(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    type = models.CharField(
        max_length=10,
        null=True
    )
    path = models.CharField(
        max_length=8192,
        null=True
    )
    selector = models.CharField(
        max_length=8192,
        null=True
    )
    nodeLabel = models.CharField(
        max_length=8192,
        null=True
    )
    snippet = models.CharField(
        max_length=8192,
        null=True
    )

    class Meta:
        verbose_name = "Lighthouse Report Layout Elements Item"

    def __str__(self):
        return self.type


class LighthouseReportUnminifiedCSS(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    url = models.CharField(
        max_length=8192,
        null=True
    )
    totalBytes = models.FloatField()
    wastedBytes = models.FloatField()
    wastedPercent = models.FloatField()

    class Meta:
        verbose_name = "Lighthouse Report Unminified CSS Element"

    def __str__(self):
        return str(self.url)


class LighthouseReportUnminifiedJS(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    url = models.CharField(
        max_length=8192,
        null=True
    )
    totalBytes = models.FloatField()
    wastedBytes = models.FloatField()
    wastedPercent = models.FloatField()

    class Meta:
        verbose_name = "Lighthouse Report Unminified JS Element"

    def __str__(self):
        return str(self.url)


class LighthouseReportUnusedCSSRule(models.Model):
    report = models.ForeignKey(
        LighthouseReport,
        on_delete=models.CASCADE
    )
    url = models.CharField(
        max_length=8192,
        null=True
    )
    totalBytes = models.FloatField()
    wastedBytes = models.FloatField()
    wastedPercent = models.FloatField()

    class Meta:
        verbose_name = "Lighthouse Report Unused CSS Element"

    def __str__(self):
        return str(self.url)


class MonthlyDomain(models.Model):
    domain = models.CharField(
        max_length=512
    )
    country_code = models.CharField(
        max_length=4,
        default='us'
    )
    keywords_amount = models.IntegerField(
        default=0
    )

    def __str__(self):
        return self.domain

    class Meta:
        verbose_name = 'Lighthouse Weekly Domain'


class MonthlyDomainForm(forms.ModelForm):
    AMOUNT_CHOICES = (
        (250, '250'),
        (500, '500'),
        (1000, '1000'),
        (2000, '2000'),
        (5000, '5000'),
        (10000, '10000')
    )

    domain = forms.CharField(
        max_length=512
    )
    country_code = forms.CharField(
        max_length=4
    )
    keywords_amount = forms.ChoiceField(
        choices=AMOUNT_CHOICES
    )
