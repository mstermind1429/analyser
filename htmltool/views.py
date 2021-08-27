import time

from django.shortcuts import render


def scraping_tool(request):
    return render(request, 'html/scraping_tool.html')


def lcp_page(request):
    return render(request, "html/lcp_page.html")


def fid_page(request):
    return render(request, "html/fid_page.html")


def cls_page(request):
    time.sleep(5)
    return render(request, "html/cls.html")


def cls(request):
    return render(request, "html/cls_page.html")


def html_tool(request):
    return render(request, 'html/html_tool.html')

