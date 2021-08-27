from django.shortcuts import render


def casual_impact(request):
    return render(request, "ml/casual_impact.html")
