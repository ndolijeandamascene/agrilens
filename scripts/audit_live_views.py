"""
Audit of Django Views, URLs, and Status Codes against active PostgreSQL database.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from django.db import connection

print(f"DATABASE ENGINE: {connection.vendor}")

c = Client(SERVER_NAME='localhost')

endpoints = [
    ('/', 200, 'Public Home'),
    ('/dashboard/', 200, 'Dashboard Overview'),
    ('/dashboard/?year=2024&season=A', 200, 'Dashboard 2024A'),
    ('/dashboard/?year=9999&season=X', 200, 'Dashboard Malformed Params'),
    ('/indicators/productivity/', 200, 'Productivity Intelligence'),
    ('/indicators/productivity/?crop=Maize&source=official', 200, 'Productivity Maize Official'),
    ('/indicators/productivity/?crop=Maize&source=manual', 200, 'Productivity Maize Manual'),
    ('/indicators/productivity/?crop=Maize&source=combined', 200, 'Productivity Maize Combined'),
    ('/indicators/api/summary/?year=2025&season=A', 200, 'API Summary'),
    ('/indicators/api/districts/?year=2025&season=A&crop=Maize', 200, 'API Districts'),
    ('/indicators/api/productivity-gap/?crop=Maize&year=2025&season=A', 200, 'API Productivity Gap'),
    ('/agriculture/', 200, 'Crops Catalog'),
    ('/geography/', 200, 'Districts Catalog'),
    ('/markets/', 200, 'Markets Surveillance'),
    ('/surveys/', 200, 'Surveys Framework'),
    ('/farmers/', 200, 'Farmers Registry'),
    ('/inputs/', 200, 'Inputs Catalog'),
    ('/accounts/login/', 200, 'Login View'),
    ('/accounts/profile/', 302, 'Profile (Auth required)'),
    ('/data-management/', 200, 'Data Management Hub'),
    ('/data-management/manual/', 200, 'Manual Entry List'),
    ('/data-management/manual/new/', 302, 'Manual Entry Create (Auth required)'),
    ('/data-management/manual/1/review/', 302, 'Manual Entry Review (Auth required)'),
    ('/api/provinces/', 200, 'DRF Provinces API'),
    ('/api/districts/', 200, 'DRF Districts API'),
    ('/api/crops/', 200, 'DRF Crops API'),
    ('/api/prices/', 200, 'DRF Commodity Prices API'),
]

for url, expected_status, label in endpoints:
    resp = c.get(url)
    status_match = "PASS" if resp.status_code == expected_status else "FAIL"
    print(f"[{status_match}] {label:32} {url:55} -> Status: {resp.status_code} (Expected: {expected_status})")
    if resp.status_code >= 400:
        print(f"       ERROR CONTENT: {resp.content[:200]}")
