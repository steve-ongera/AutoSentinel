"""
AutoSentinel Django Views
Complete view functions for vehicle history and monitoring system
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q, Count, Avg, Max, Min
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import json

from main_application.models import (
    User, Vehicle, VehicleRegistration, TitleEvent, AccidentRecord,
    MileageRecord, OwnershipRecord, TheftRecord, TelemetryTrace,
    CrowdsourcedReport, VehicleReport, ReportPurchase, DataProvider,
    ProviderDataFeed, AuditLog, SearchQuery
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_admin(user):
    return user.is_authenticated and user.role in ['system_admin', 'auditor']

def is_dealer(user):
    return user.is_authenticated and user.role in ['dealer', 'system_admin']

def is_fleet_admin(user):
    return user.is_authenticated and user.role in ['fleet_admin', 'system_admin']

def log_audit(user, action, resource_type, resource_id=None, vehicle=None, request=None):
    """Helper function to create audit logs"""
    AuditLog.objects.create(
        user=user if user.is_authenticated else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        vehicle=vehicle,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT') if request else None
    )


# ============================================================================
# PUBLIC VIEWS
# ============================================================================

def home(request):
    """Homepage"""
    stats = {
        'total_vehicles': Vehicle.objects.count(),
        'total_reports': VehicleReport.objects.filter(status='completed').count(),
        'stolen_vehicles': Vehicle.objects.filter(is_stolen=True).count(),
        'tracked_vehicles': Vehicle.objects.filter(consenting_for_tracking=True).count(),
    }
    recent_searches = SearchQuery.objects.order_by('-created_at')[:5]
    
    return render(request, 'main_application/home.html', {
        'stats': stats,
        'recent_searches': recent_searches
    })

def about(request):
    """About page"""
    return render(request, 'main_application/about.html')

def pricing(request):
    """Pricing page"""
    return render(request, 'main_application/pricing.html')


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

def register_view(request):
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'guest')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')
    
    return render(request, 'main_application/register.html')

def login_view(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'main_application/login.html')

def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')


# ============================================================================
# SEARCH VIEWS
# ============================================================================

def search(request):
    """Main search page"""
    return render(request, 'main_application/search.html')

def search_results(request):
    """Search results"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'vin')
    
    vehicles = []
    
    if query:
        start_time = timezone.now()
        
        if search_type == 'vin':
            vehicles = Vehicle.objects.filter(vin__icontains=query)
        elif search_type == 'plate':
            registrations = VehicleRegistration.objects.filter(
                plate_number__icontains=query
            ).select_related('vehicle')
            vehicles = [reg.vehicle for reg in registrations]
        elif search_type == 'make_model':
            vehicles = Vehicle.objects.filter(
                Q(make__icontains=query) | Q(model__icontains=query)
            )
        
        # Log search
        end_time = timezone.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        SearchQuery.objects.create(
            user=request.user if request.user.is_authenticated else None,
            search_type=search_type,
            query_text=query,
            vehicle_found=vehicles[0] if vehicles else None,
            results_count=len(vehicles),
            response_time_ms=int(response_time),
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    paginator = Paginator(vehicles, 20)
    page = request.GET.get('page', 1)
    vehicles_page = paginator.get_page(page)
    
    return render(request, 'main_application/search_results.html', {
        'query': query,
        'search_type': search_type,
        'vehicles': vehicles_page,
        'total_results': len(vehicles)
    })


# ============================================================================
# VEHICLE VIEWS
# ============================================================================

def vehicle_list(request):
    """List all vehicles"""
    vehicles = Vehicle.objects.all().order_by('-created_at')
    
    # Filters
    make = request.GET.get('make')
    year = request.GET.get('year')
    status = request.GET.get('status')
    
    if make:
        vehicles = vehicles.filter(make=make)
    if year:
        vehicles = vehicles.filter(year=year)
    if status:
        vehicles = vehicles.filter(current_title_status=status)
    
    paginator = Paginator(vehicles, 24)
    page = request.GET.get('page', 1)
    vehicles_page = paginator.get_page(page)
    
    # Get filter options
    makes = Vehicle.objects.values_list('make', flat=True).distinct().order_by('make')
    years = Vehicle.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    return render(request, 'main_application/vehicle_list.html', {
        'vehicles': vehicles_page,
        'makes': makes,
        'years': years
    })

def vehicle_detail(request, vin):
    """Vehicle detail page"""
    vehicle = get_object_or_404(Vehicle, vin=vin)
    
    # Log view
    log_audit(request.user, 'view', 'Vehicle', vehicle.id, vehicle, request)
    
    # Get related data
    registrations = vehicle.registrations.all().order_by('-issued_date')
    title_events = vehicle.title_events.all()[:10]
    accidents = vehicle.accidents.all()[:10]
    mileage_records = vehicle.mileage_records.all()[:20]
    ownership_records = vehicle.ownership_records.all()
    theft_records = vehicle.theft_records.all()
    
    context = {
        'vehicle': vehicle,
        'registrations': registrations,
        'title_events': title_events,
        'accidents': accidents,
        'mileage_records': mileage_records,
        'ownership_records': ownership_records,
        'theft_records': theft_records,
        'has_accidents': accidents.exists(),
        'has_theft': theft_records.exists(),
    }
    
    return render(request, 'main_application/vehicle_detail.html', context)

def vehicle_history(request, vin):
    """Complete vehicle history"""
    vehicle = get_object_or_404(Vehicle, vin=vin)
    
    return render(request, 'main_application/vehicle_history.html', {
        'vehicle': vehicle,
        'title_events': vehicle.title_events.all(),
        'accidents': vehicle.accidents.all(),
        'mileage_records': vehicle.mileage_records.all(),
    })

@login_required
def vehicle_tracking(request, vin):
    """Vehicle GPS tracking (consent required)"""
    vehicle = get_object_or_404(Vehicle, vin=vin)
    
    if not vehicle.consenting_for_tracking:
        messages.warning(request, 'This vehicle does not have tracking enabled')
        return redirect('vehicle_detail', vin=vin)
    
    # Get recent telemetry
    telemetry = vehicle.telemetry_traces.all()[:100]
    
    return render(request, 'main_application/vehicle_tracking.html', {
        'vehicle': vehicle,
        'telemetry': telemetry
    })


# ============================================================================
# REPORT VIEWS
# ============================================================================

@login_required
def generate_report(request, vin):
    """Generate vehicle report"""
    vehicle = get_object_or_404(Vehicle, vin=vin)
    
    if request.method == 'POST':
        include_telemetry = request.POST.get('include_telemetry') == 'on'
        
        # Create report
        report = VehicleReport.objects.create(
            vehicle=vehicle,
            requested_by=request.user,
            status='processing',
            price=29.99,
            include_telemetry=include_telemetry and vehicle.consenting_for_tracking,
            include_owner_history=True
        )
        
        messages.success(request, 'Report generation started!')
        return redirect('report_detail', report_id=report.id)
    
    return render(request, 'main_application/generate_report.html', {
        'vehicle': vehicle
    })

@login_required
def report_list(request):
    """List user's reports"""
    reports = VehicleReport.objects.filter(
        requested_by=request.user
    ).select_related('vehicle').order_by('-created_at')
    
    paginator = Paginator(reports, 20)
    page = request.GET.get('page', 1)
    reports_page = paginator.get_page(page)
    
    return render(request, 'main_application/report_list.html', {
        'reports': reports_page
    })

@login_required
def report_detail(request, report_id):
    """View report details"""
    report = get_object_or_404(VehicleReport, id=report_id)
    
    # Check access
    if report.requested_by != request.user and not is_admin(request.user):
        messages.error(request, 'You do not have access to this report')
        return redirect('report_list')
    
    return render(request, 'main_application/report_detail.html', {
        'report': report
    })

@login_required
def purchase_report(request, report_id):
    """Purchase a report"""
    report = get_object_or_404(VehicleReport, id=report_id)
    
    if request.method == 'POST':
        # Simulate payment
        ReportPurchase.objects.create(
            report=report,
            user=request.user,
            amount=report.price,
            payment_status='completed',
            payment_method='credit_card',
            transaction_id=f'TXN{timezone.now().timestamp()}',
            completed_at=timezone.now()
        )
        
        report.is_paid = True
        report.status = 'completed'
        report.save()
        
        messages.success(request, 'Report purchased successfully!')
        return redirect('report_detail', report_id=report.id)
    
    return render(request, 'main_application/purchase_report.html', {
        'report': report
    })


# ============================================================================
# DASHBOARD VIEWS
# ============================================================================

@login_required
def dashboard(request):
    """User dashboard"""
    user = request.user
    
    recent_searches = SearchQuery.objects.filter(user=user).order_by('-created_at')[:10]
    recent_reports = VehicleReport.objects.filter(requested_by=user).order_by('-created_at')[:5]
    
    stats = {
        'total_searches': SearchQuery.objects.filter(user=user).count(),
        'total_reports': VehicleReport.objects.filter(requested_by=user).count(),
        'total_purchases': ReportPurchase.objects.filter(user=user).count(),
    }
    
    return render(request, 'main_application/dashboard.html', {
        'recent_searches': recent_searches,
        'recent_reports': recent_reports,
        'stats': stats
    })

@login_required
def profile(request):
    """User profile"""
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.phone_number = request.POST.get('phone_number', '')
        request.user.company_name = request.POST.get('company_name', '')
        request.user.save()
        
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')
    
    return render(request, 'main_application/profile.html')


# ============================================================================
# CROWDSOURCED CONTENT VIEWS
# ============================================================================

@login_required
def submit_report(request, vin):
    """Submit crowdsourced report"""
    vehicle = get_object_or_404(Vehicle, vin=vin)
    
    if request.method == 'POST':
        CrowdsourcedReport.objects.create(
            vehicle=vehicle,
            submitted_by=request.user,
            report_type=request.POST.get('report_type'),
            report_date=request.POST.get('report_date'),
            description=request.POST.get('description'),
            location_city=request.POST.get('location_city'),
            location_state=request.POST.get('location_state'),
            status='pending'
        )
        
        messages.success(request, 'Report submitted successfully!')
        return redirect('vehicle_detail', vin=vin)
    
    return render(request, 'main_application/submit_report.html', {
        'vehicle': vehicle
    })

@login_required
def crowdsourced_reports(request):
    """List crowdsourced reports"""
    reports = CrowdsourcedReport.objects.all().select_related(
        'vehicle', 'submitted_by'
    ).order_by('-created_at')
    
    status = request.GET.get('status')
    if status:
        reports = reports.filter(status=status)
    
    paginator = Paginator(reports, 20)
    page = request.GET.get('page', 1)
    reports_page = paginator.get_page(page)
    
    return render(request, 'main_application/crowdsourced_reports.html', {
        'reports': reports_page
    })


# ============================================================================
# ADMIN VIEWS
# ============================================================================

@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard"""
    stats = {
        'total_vehicles': Vehicle.objects.count(),
        'total_users': User.objects.count(),
        'total_reports': VehicleReport.objects.count(),
        'stolen_vehicles': Vehicle.objects.filter(is_stolen=True).count(),
        'pending_crowdsourced': CrowdsourcedReport.objects.filter(status='pending').count(),
    }
    
    recent_activity = AuditLog.objects.select_related('user', 'vehicle').order_by('-timestamp')[:20]
    
    return render(request, 'main_application/admin_dashboard.html', {
        'stats': stats,
        'recent_activity': recent_activity
    })

@user_passes_test(is_admin)
def audit_logs(request):
    """View audit logs"""
    logs = AuditLog.objects.select_related('user', 'vehicle').order_by('-timestamp')
    
    # Filters
    action = request.GET.get('action')
    user_id = request.GET.get('user')
    
    if action:
        logs = logs.filter(action=action)
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs_page = paginator.get_page(page)
    
    return render(request, 'main_application/audit_logs.html', {
        'logs': logs_page
    })

@user_passes_test(is_admin)
def stolen_vehicles(request):
    """Manage stolen vehicles"""
    vehicles = Vehicle.objects.filter(is_stolen=True).select_related().order_by('-updated_at')
    
    return render(request, 'main_application/stolen_vehicles.html', {
        'vehicles': vehicles
    })

@user_passes_test(is_admin)
def verify_report(request, report_id):
    """Verify crowdsourced report"""
    report = get_object_or_404(CrowdsourcedReport, id=report_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            report.status = 'verified'
            report.verified_by = request.user
            report.verified_at = timezone.now()
            messages.success(request, 'Report verified')
        elif action == 'reject':
            report.status = 'rejected'
            messages.success(request, 'Report rejected')
        
        report.save()
        return redirect('crowdsourced_reports')
    
    return render(request, 'main_application/verify_report.html', {
        'report': report
    })


# ============================================================================
# STATISTICS & ANALYTICS VIEWS
# ============================================================================

@login_required
def statistics(request):
    """Statistics and analytics"""
    # Vehicle stats
    vehicle_stats = {
        'by_make': Vehicle.objects.values('make').annotate(count=Count('id')).order_by('-count')[:10],
        'by_year': Vehicle.objects.values('year').annotate(count=Count('id')).order_by('-year')[:10],
        'by_status': Vehicle.objects.values('current_title_status').annotate(count=Count('id')),
    }
    
    # Accident stats
    accident_stats = {
        'total': AccidentRecord.objects.count(),
        'by_severity': AccidentRecord.objects.values('severity').annotate(count=Count('id')),
    }
    
    # Search stats
    search_stats = {
        'total': SearchQuery.objects.count(),
        'by_type': SearchQuery.objects.values('search_type').annotate(count=Count('id')),
    }
    
    return render(request, 'main_application/statistics.html', {
        'vehicle_stats': vehicle_stats,
        'accident_stats': accident_stats,
        'search_stats': search_stats
    })


# ============================================================================
# API VIEWS (JSON)
# ============================================================================

def api_vehicle_lookup(request, vin):
    """API endpoint for vehicle lookup"""
    try:
        vehicle = Vehicle.objects.get(vin=vin)
        data = {
            'vin': vehicle.vin,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'title_status': vehicle.current_title_status,
            'mileage': vehicle.current_mileage,
            'is_stolen': vehicle.is_stolen,
        }
        return JsonResponse(data)
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)

@login_required
def api_telemetry_data(request, vin):
    """API endpoint for telemetry data"""
    vehicle = get_object_or_404(Vehicle, vin=vin)
    
    if not vehicle.consenting_for_tracking:
        return JsonResponse({'error': 'Tracking not enabled'}, status=403)
    
    traces = vehicle.telemetry_traces.all()[:100]
    data = [{
        'timestamp': trace.timestamp.isoformat(),
        'latitude': float(trace.latitude),
        'longitude': float(trace.longitude),
        'speed': trace.speed,
    } for trace in traces]
    
    return JsonResponse({'data': data})