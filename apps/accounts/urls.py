from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # User Management & Governance (Admin role required)
    path('users/', views.user_list, name='user_list'),
    path('users/new/', views.user_create, name='user_create'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/setup-link/', views.user_generate_setup_link, name='user_generate_setup_link'),
    path('users/setup-password/<str:uidb64>/<str:token>/', views.password_setup_view, name='password_setup'),

    # System & Security Audit Trail
    path('audit-log/', views.audit_log_list, name='audit_log_list'),
]

