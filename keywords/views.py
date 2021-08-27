from django.shortcuts import render


def csv(request):
    return render(request, 'keywords/csv.html')


def key_patterns(request):
    return render(request, 'keywords/key_patterns_extractor.html')


def keyword_search(request):
    return render(request, 'keywords/keyword_search.html')


def searchmetrics_tool(request):
    return render(request, 'keywords/searchmetrics_tool.html')


def domain_searchmetrics(request):
    return render(request, "keywords/searchmetrics_domain_tool.html")


def search_volume(request):
    return render(request, "keywords/search_volume.html")


def keyword_domain(request):
    return render(request, "keywords/keyword_domain.html")


def category_domain(request):
    return render(request, "keywords/category_domain.html")
