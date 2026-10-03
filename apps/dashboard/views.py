from django.shortcuts import render

def home(request):
    """AgriLens National Agricultural Insights Dashboard."""
    context = {
        'page_title': 'Rwanda Agricultural Analytics & Decision Platform',
    }
    return render(request, 'dashboard/index.html', context)
