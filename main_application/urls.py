
from django.urls import path
from main_application import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('pricing/', views.pricing, name='pricing'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Search
    path('search/', views.search, name='search'),
    path('search/results/', views.search_results, name='search_results'),
    
    # Vehicles
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/<str:vin>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<str:vin>/history/', views.vehicle_history, name='vehicle_history'),
    path('vehicles/<str:vin>/tracking/', views.vehicle_tracking, name='vehicle_tracking'),
    
    # Reports
    path('vehicles/<str:vin>/generate-report/', views.generate_report, name='generate_report'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<uuid:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<uuid:report_id>/purchase/', views.purchase_report, name='purchase_report'),
    
    # User Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Crowdsourced Content
    path('vehicles/<str:vin>/submit-report/', views.submit_report, name='submit_report'),
    path('crowdsourced-reports/', views.crowdsourced_reports, name='crowdsourced_reports'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/audit-logs/', views.audit_logs, name='audit_logs'),
    path('admin/stolen-vehicles/', views.stolen_vehicles, name='stolen_vehicles'),
    path('admin/verify-report/<uuid:report_id>/', views.verify_report, name='verify_report'),
    
    # Statistics
    path('statistics/', views.statistics, name='statistics'),
    
    # API Endpoints
    path('api/vehicle/<str:vin>/', views.api_vehicle_lookup, name='api_vehicle_lookup'),
    path('api/vehicle/<str:vin>/telemetry/', views.api_telemetry_data, name='api_telemetry_data'),
]