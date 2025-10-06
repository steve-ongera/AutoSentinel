"""
AutoSentinel Django Admin Configuration
Complete admin interface for vehicle history and monitoring system
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from main_application.models import (
    User, Vehicle, VehicleRegistration, TitleEvent, AccidentRecord,
    MileageRecord, OwnershipRecord, TheftRecord, TelemetryTrace,
    CrowdsourcedReport, VehicleReport, ReportPurchase, DataProvider,
    ProviderDataFeed, AuditLog, SearchQuery
)


# ============================================================================
# USER ADMIN
# ============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'company_name', 'verified_status', 'consent_status', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active', 'verified_at', 'consent_to_data_usage']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'company_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Permissions', {
            'fields': ('role', 'verified_at', 'phone_number', 'company_name')
        }),
        ('Data Consent', {
            'fields': ('consent_to_data_usage', 'consent_date')
        }),
    )
    
    def verified_status(self, obj):
        if obj.verified_at:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: gray;">Not Verified</span>')
    verified_status.short_description = 'Verified'
    
    def consent_status(self, obj):
        if obj.consent_to_data_usage:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    consent_status.short_description = 'Consent'


# ============================================================================
# VEHICLE ADMIN
# ============================================================================

class VehicleRegistrationInline(admin.TabularInline):
    model = VehicleRegistration
    extra = 0
    fields = ['plate_number', 'state', 'country', 'issued_date', 'expiry_date', 'is_current']
    readonly_fields = ['created_at']


class TitleEventInline(admin.TabularInline):
    model = TitleEvent
    extra = 0
    fields = ['event_type', 'event_date', 'title_status', 'state', 'odometer_reading', 'source']
    readonly_fields = ['created_at']
    ordering = ['-event_date']


class AccidentRecordInline(admin.TabularInline):
    model = AccidentRecord
    extra = 0
    fields = ['accident_date', 'severity', 'source', 'estimated_damage_cost', 'airbag_deployed', 'verified']
    readonly_fields = ['created_at']
    ordering = ['-accident_date']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vin', 'year', 'make', 'model', 'current_title_status', 'current_mileage', 
                    'owner_count', 'stolen_badge', 'tracking_status', 'last_reported']
    list_filter = ['current_title_status', 'is_stolen', 'consenting_for_tracking', 'make', 'year']
    search_fields = ['vin', 'make', 'model']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_reported_at']
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'vin')
        }),
        ('Basic Information', {
            'fields': ('make', 'model', 'year', 'trim', 'body_style', 'color')
        }),
        ('Technical Specifications', {
            'fields': ('engine', 'transmission', 'drivetrain', 'fuel_type', 'displacement', 'cylinders'),
            'classes': ('collapse',)
        }),
        ('Manufacturing', {
            'fields': ('manufacture_country', 'manufacture_plant', 'manufacture_date'),
            'classes': ('collapse',)
        }),
        ('Current Status', {
            'fields': ('current_mileage', 'current_title_status', 'is_stolen', 'current_owner_count')
        }),
        ('Tracking & Consent', {
            'fields': ('consenting_for_tracking', 'tracking_consent_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_reported_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [VehicleRegistrationInline, TitleEventInline, AccidentRecordInline]
    
    def stolen_badge(self, obj):
        if obj.is_stolen:
            return format_html('<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">STOLEN</span>')
        return '-'
    stolen_badge.short_description = 'Theft Status'
    
    def tracking_status(self, obj):
        if obj.consenting_for_tracking:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: gray;">Inactive</span>')
    tracking_status.short_description = 'Tracking'
    
    def owner_count(self, obj):
        return obj.current_owner_count
    owner_count.short_description = 'Owners'
    
    def last_reported(self, obj):
        return obj.last_reported_at.strftime('%Y-%m-%d %H:%M') if obj.last_reported_at else '-'
    last_reported.short_description = 'Last Report'
    
    actions = ['mark_as_stolen', 'mark_as_not_stolen', 'enable_tracking', 'disable_tracking']
    
    def mark_as_stolen(self, request, queryset):
        updated = queryset.update(is_stolen=True)
        self.message_user(request, f'{updated} vehicle(s) marked as stolen.')
    mark_as_stolen.short_description = 'Mark selected vehicles as stolen'
    
    def mark_as_not_stolen(self, request, queryset):
        updated = queryset.update(is_stolen=False)
        self.message_user(request, f'{updated} vehicle(s) marked as not stolen.')
    mark_as_not_stolen.short_description = 'Mark selected vehicles as not stolen'
    
    def enable_tracking(self, request, queryset):
        updated = queryset.update(consenting_for_tracking=True)
        self.message_user(request, f'Tracking enabled for {updated} vehicle(s).')
    enable_tracking.short_description = 'Enable tracking for selected vehicles'
    
    def disable_tracking(self, request, queryset):
        updated = queryset.update(consenting_for_tracking=False)
        self.message_user(request, f'Tracking disabled for {updated} vehicle(s).')
    disable_tracking.short_description = 'Disable tracking for selected vehicles'


@admin.register(VehicleRegistration)
class VehicleRegistrationAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'state', 'country', 'vehicle_link', 'issued_date', 'expiry_date', 'is_current']
    list_filter = ['state', 'country', 'is_current']
    search_fields = ['plate_number', 'vehicle__vin']
    readonly_fields = ['id', 'created_at']
    
    def vehicle_link(self, obj):
        url = reverse('admin:main_application_vehicle_change', args=[obj.vehicle.id])
        return format_html('<a href="{}">{}</a>', url, obj.vehicle.vin)
    vehicle_link.short_description = 'Vehicle'


# ============================================================================
# HISTORY RECORDS ADMIN
# ============================================================================

@admin.register(TitleEvent)
class TitleEventAdmin(admin.ModelAdmin):
    list_display = ['vehicle_vin', 'event_type', 'event_date', 'title_status', 'state', 'odometer_reading', 'source']
    list_filter = ['event_type', 'title_status', 'state', 'event_date']
    search_fields = ['vehicle__vin', 'title_number']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'event_date'
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'


@admin.register(AccidentRecord)
class AccidentRecordAdmin(admin.ModelAdmin):
    list_display = ['vehicle_vin', 'accident_date', 'severity', 'source', 'damage_cost', 
                    'airbag_deployed', 'structural_damage', 'verified_badge']
    list_filter = ['severity', 'source', 'verified', 'airbag_deployed', 'is_structural_damage', 'accident_date']
    search_fields = ['vehicle__vin', 'report_number', 'damage_description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'accident_date'
    
    fieldsets = (
        ('Identification', {
            'fields': ('id', 'vehicle', 'accident_date')
        }),
        ('Accident Details', {
            'fields': ('severity', 'source', 'damage_description', 'estimated_damage_cost')
        }),
        ('Damage Assessment', {
            'fields': ('airbag_deployed', 'is_structural_damage')
        }),
        ('Location', {
            'fields': ('location_city', 'location_state')
        }),
        ('Verification', {
            'fields': ('report_number', 'verified')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'
    
    def damage_cost(self, obj):
        if obj.estimated_damage_cost:
            return f'${obj.estimated_damage_cost:,.2f}'
        return '-'
    damage_cost.short_description = 'Damage Cost'
    
    def structural_damage(self, obj):
        return '✓' if obj.is_structural_damage else '-'
    structural_damage.short_description = 'Structural'
    
    def verified_badge(self, obj):
        if obj.verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: orange;">Pending</span>')
    verified_badge.short_description = 'Status'


@admin.register(MileageRecord)
class MileageRecordAdmin(admin.ModelAdmin):
    list_display = ['vehicle_vin', 'recorded_date', 'mileage', 'unit', 'source', 'rollback_flag', 'verified']
    list_filter = ['source', 'is_rollback_suspected', 'verified', 'recorded_date']
    search_fields = ['vehicle__vin']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'recorded_date'
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'
    
    def rollback_flag(self, obj):
        if obj.is_rollback_suspected:
            return format_html('<span style="color: red; font-weight: bold;">⚠ SUSPECTED</span>')
        return '-'
    rollback_flag.short_description = 'Rollback'


@admin.register(OwnershipRecord)
class OwnershipRecordAdmin(admin.ModelAdmin):
    list_display = ['vehicle_vin', 'owner_sequence', 'owner_type', 'ownership_start', 
                    'ownership_end', 'duration_days', 'is_current', 'tracking_consent']
    list_filter = ['owner_type', 'is_current', 'consented_to_tracking', 'state']
    search_fields = ['vehicle__vin', 'owner_hash']
    readonly_fields = ['id', 'created_at']
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'
    
    def duration_days(self, obj):
        return obj.ownership_duration_days or '-'
    duration_days.short_description = 'Duration (days)'
    
    def tracking_consent(self, obj):
        return '✓' if obj.consented_to_tracking else '-'
    tracking_consent.short_description = 'Consent'


@admin.register(TheftRecord)
class TheftRecordAdmin(admin.ModelAdmin):
    list_display = ['vehicle_vin', 'status', 'reported_date', 'recovered_date', 
                    'reporting_agency', 'case_number', 'location']
    list_filter = ['status', 'reported_date', 'theft_location_state']
    search_fields = ['vehicle__vin', 'case_number', 'reporting_agency']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'reported_date'
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'
    
    def location(self, obj):
        parts = [obj.theft_location_city, obj.theft_location_state]
        return ', '.join(filter(None, parts)) or '-'


# ============================================================================
# TELEMATICS ADMIN
# ============================================================================

@admin.register(TelemetryTrace)
class TelemetryTraceAdmin(admin.ModelAdmin):
    list_display = ['vehicle_vin', 'timestamp', 'location', 'speed', 'odometer', 'device_id']
    list_filter = ['timestamp']
    search_fields = ['vehicle__vin', 'device_id']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'timestamp'
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'
    
    def location(self, obj):
        return f'{obj.latitude}, {obj.longitude}'


# ============================================================================
# CROWDSOURCED CONTENT ADMIN
# ============================================================================

@admin.register(CrowdsourcedReport)
class CrowdsourcedReportAdmin(admin.ModelAdmin):
    list_display = ['vehicle_vin', 'report_type', 'status', 'report_date', 
                    'submitted_by', 'location', 'verified_by_user']
    list_filter = ['report_type', 'status', 'report_date']
    search_fields = ['vehicle__vin', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'report_date'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('id', 'vehicle', 'submitted_by', 'report_type', 'status')
        }),
        ('Details', {
            'fields': ('report_date', 'description', 'location_city', 'location_state')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_reports', 'reject_reports']
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'
    
    def location(self, obj):
        parts = [obj.location_city, obj.location_state]
        return ', '.join(filter(None, parts)) or '-'
    
    def verified_by_user(self, obj):
        return obj.verified_by.username if obj.verified_by else '-'
    verified_by_user.short_description = 'Verified By'
    
    def verify_reports(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='verified', verified_by=request.user, verified_at=timezone.now())
        self.message_user(request, f'{updated} report(s) verified.')
    verify_reports.short_description = 'Verify selected reports'
    
    def reject_reports(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} report(s) rejected.')
    reject_reports.short_description = 'Reject selected reports'


# ============================================================================
# REPORT & TRANSACTION ADMIN
# ============================================================================

class ReportPurchaseInline(admin.StackedInline):
    model = ReportPurchase
    extra = 0
    readonly_fields = ['id', 'created_at', 'completed_at']


@admin.register(VehicleReport)
class VehicleReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'vehicle_vin', 'requested_by', 'status', 
                    'is_paid', 'price', 'created_date', 'generation_time']
    list_filter = ['status', 'is_paid', 'include_telemetry', 'created_at']
    search_fields = ['id', 'vehicle__vin', 'requested_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'generation_started_at', 'generation_completed_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('id', 'vehicle', 'requested_by', 'status')
        }),
        ('Pricing & Access', {
            'fields': ('is_paid', 'price')
        }),
        ('Content Options', {
            'fields': ('include_telemetry', 'include_owner_history')
        }),
        ('Generated Files', {
            'fields': ('pdf_file', 'json_data')
        }),
        ('Generation Timestamps', {
            'fields': ('generation_started_at', 'generation_completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ReportPurchaseInline]
    
    def report_id(self, obj):
        return str(obj.id)[:8]
    report_id.short_description = 'Report ID'
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin
    vehicle_vin.short_description = 'VIN'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Created'
    
    def generation_time(self, obj):
        if obj.generation_started_at and obj.generation_completed_at:
            delta = obj.generation_completed_at - obj.generation_started_at
            return f'{delta.total_seconds():.2f}s'
        return '-'
    generation_time.short_description = 'Gen Time'


@admin.register(ReportPurchase)
class ReportPurchaseAdmin(admin.ModelAdmin):
    list_display = ['purchase_id', 'report_link', 'user', 'amount', 
                    'payment_status', 'payment_method', 'created_date']
    list_filter = ['payment_status', 'payment_method', 'created_at']
    search_fields = ['id', 'user__username', 'transaction_id']
    readonly_fields = ['id', 'created_at', 'completed_at']
    
    def purchase_id(self, obj):
        return str(obj.id)[:8]
    purchase_id.short_description = 'Purchase ID'
    
    def report_link(self, obj):
        url = reverse('admin:main_application_vehiclereport_change', args=[obj.report.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.report.id)[:8])
    report_link.short_description = 'Report'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_date.short_description = 'Created'


# ============================================================================
# DATA PROVIDER ADMIN
# ============================================================================

@admin.register(DataProvider)
class DataProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_active', 'rate_limit', 'api_status']
    list_filter = ['provider_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('id', 'name', 'provider_type', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_endpoint', 'api_key', 'api_secret', 'rate_limit_per_hour')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rate_limit(self, obj):
        return f'{obj.rate_limit_per_hour}/hr'
    rate_limit.short_description = 'Rate Limit'
    
    def api_status(self, obj):
        if obj.api_endpoint:
            return format_html('<span style="color: green;">✓ Configured</span>')
        return format_html('<span style="color: gray;">Not Configured</span>')
    api_status.short_description = 'API Status'


@admin.register(ProviderDataFeed)
class ProviderDataFeedAdmin(admin.ModelAdmin):
    list_display = ['feed_id', 'provider', 'vehicle_vin', 'status', 'requested_date', 'completed_date']
    list_filter = ['status', 'provider', 'requested_at']
    search_fields = ['id', 'vehicle__vin', 'provider__name']
    readonly_fields = ['id', 'requested_at', 'completed_at']
    date_hierarchy = 'requested_at'
    
    def feed_id(self, obj):
        return str(obj.id)[:8]
    feed_id.short_description = 'Feed ID'
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin if obj.vehicle else '-'
    vehicle_vin.short_description = 'VIN'
    
    def requested_date(self, obj):
        return obj.requested_at.strftime('%Y-%m-%d %H:%M')
    requested_date.short_description = 'Requested'
    
    def completed_date(self, obj):
        return obj.completed_at.strftime('%Y-%m-%d %H:%M') if obj.completed_at else '-'
    completed_date.short_description = 'Completed'


# ============================================================================
# AUDIT & SECURITY ADMIN
# ============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'resource_type', 'vehicle_vin', 'ip_address']
    list_filter = ['action', 'resource_type', 'timestamp']
    search_fields = ['user__username', 'resource_type', 'vehicle__vin', 'ip_address']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'timestamp', 'user', 'action')
        }),
        ('Resource', {
            'fields': ('resource_type', 'resource_id', 'field_accessed', 'vehicle')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def vehicle_vin(self, obj):
        return obj.vehicle.vin if obj.vehicle else '-'
    vehicle_vin.short_description = 'VIN'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'search_type', 'query_text', 
                    'results_count', 'response_time', 'cache_status']
    list_filter = ['search_type', 'cache_hit', 'created_at']
    search_fields = ['query_text', 'user__username']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    
    def timestamp(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    
    def response_time(self, obj):
        return f'{obj.response_time_ms}ms' if obj.response_time_ms else '-'
    response_time.short_description = 'Response Time'
    
    def cache_status(self, obj):
        if obj.cache_hit:
            return format_html('<span style="color: green;">✓ Hit</span>')
        return format_html('<span style="color: gray;">Miss</span>')
    cache_status.short_description = 'Cache'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

admin.site.site_header = 'AutoSentinel Administration'
admin.site.site_title = 'AutoSentinel Admin'
admin.site.index_title = 'Vehicle History & Monitoring System'