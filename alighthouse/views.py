from django.shortcuts import render


def lighthouse(request):
    return render(request, "lighthouse/lighthouse.html")


def domain_lighthouse(request):
    return render(request, "lighthouse/lighthouse_domain.html")
