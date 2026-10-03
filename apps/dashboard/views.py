"""
AgriLens Dashboard & Public Presentation Views.
2026 NISR Big Data Hackathon – Track 1: Agricultural Productivity.
"""
from django.shortcuts import render


def public_home(request):
    """
    Public-facing landing page for AgriLens.
    Showcases Hackathon Track 1 context, national overview metrics,
    interactive Productivity Gap Intelligence simulator, interactive Rwanda map,
    and official NISR data lineage principles.
    """
    context = {
        'page_title': 'AgriLens • See Agriculture Through Data | Rwanda',
        'is_public_page': True,
    }
    return render(request, 'home.html', context)


def dashboard_overview(request):
    """
    Internal National Agricultural Insights Dashboard.
    Provides detailed district indicators, filter tools, and analytical aggregates.
    """
    context = {
        'page_title': 'National Agricultural Analytics & Indicator Hub',
        'is_public_page': False,
    }
    return render(request, 'dashboard/index.html', context)
