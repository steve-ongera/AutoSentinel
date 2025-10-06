"""
AutoSentinel Django Models
Complete model structure for vehicle history and monitoring system
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex
import uuid


# ============================================================================
# USER & AUTHENTICATION MODELS
# ============================================================================

class User(AbstractUser):
    """Extended user model with role-based access control"""
    
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('verified_buyer', 'Verified Buyer'),
        ('dealer', 'Dealer'),
        ('fleet_admin', 'Fleet Administrator'),
        ('auditor', 'Auditor'),
        ('system_admin', 'System Administrator'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    consent_to_data_usage = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
        ]


# ============================================================================
# VEHICLE CORE MODELS
# ============================================================================

class Vehicle(models.Model):
    """Main vehicle entity"""
    
    TITLE_STATUS_CHOICES = [
        ('clean', 'Clean'),
        ('salvage', 'Salvage'),
        ('rebuilt', 'Rebuilt'),
        ('junk', 'Junk'),
        ('flood', 'Flood Damage'),
        ('hail', 'Hail Damage'),
        ('lemon', 'Lemon Law Buyback'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vin = models.CharField(
        max_length=17, 
        unique=True, 
        db_index=True,
        validators=[RegexValidator(r'^[A-HJ-NPR-Z0-9]{17}$', 'Invalid VIN format')]
    )
    
    # Basic vehicle info
    make = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=100, db_index=True)
    year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    trim = models.CharField(max_length=100, blank=True, null=True)
    body_style = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    
    # Engine & technical specs
    engine = models.CharField(max_length=100, blank=True, null=True)
    transmission = models.CharField(max_length=100, blank=True, null=True)
    drivetrain = models.CharField(max_length=50, blank=True, null=True)
    fuel_type = models.CharField(max_length=50, blank=True, null=True)
    displacement = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    cylinders = models.IntegerField(null=True, blank=True)
    
    # Manufacturing info
    manufacture_country = models.CharField(max_length=100, blank=True, null=True)
    manufacture_plant = models.CharField(max_length=100, blank=True, null=True)
    manufacture_date = models.DateField(null=True, blank=True)
    
    # Current status
    current_mileage = models.IntegerField(validators=[MinValueValidator(0)])
    current_title_status = models.CharField(max_length=20, choices=TITLE_STATUS_CHOICES, default='clean')
    is_stolen = models.BooleanField(default=False, db_index=True)
    
    # Owner & consent info
    current_owner_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    consenting_for_tracking = models.BooleanField(default=False, db_index=True)
    tracking_consent_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_reported_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'vehicles'
        indexes = [
            models.Index(fields=['make', 'model', 'year']),
            models.Index(fields=['current_title_status']),
            models.Index(fields=['is_stolen']),
            models.Index(fields=['consenting_for_tracking']),
        ]
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.vin}"


class VehicleRegistration(models.Model):
    """Vehicle registration numbers (license plates) with history"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='registrations')
    
    plate_number = models.CharField(max_length=20, db_index=True)
    state = models.CharField(max_length=2)
    country = models.CharField(max_length=2, default='US')
    
    issued_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vehicle_registrations'
        unique_together = [['plate_number', 'state', 'country']]
        indexes = [
            models.Index(fields=['plate_number', 'state']),
            models.Index(fields=['is_current']),
        ]
    
    def __str__(self):
        return f"{self.plate_number} ({self.state})"


# ============================================================================
# VEHICLE HISTORY MODELS
# ============================================================================

class TitleEvent(models.Model):
    """Title history and brand changes"""
    
    EVENT_TYPES = [
        ('initial', 'Initial Title'),
        ('transfer', 'Ownership Transfer'),
        ('brand_change', 'Title Brand Change'),
        ('duplicate', 'Duplicate Title Issued'),
        ('lien_add', 'Lien Added'),
        ('lien_release', 'Lien Released'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='title_events')
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_date = models.DateField(db_index=True)
    title_status = models.CharField(max_length=20, choices=Vehicle.TITLE_STATUS_CHOICES)
    
    state = models.CharField(max_length=2)
    title_number = models.CharField(max_length=50, blank=True, null=True)
    
    odometer_reading = models.IntegerField(null=True, blank=True)
    odometer_unit = models.CharField(max_length=10, default='miles')
    
    notes = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'title_events'
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['vehicle', '-event_date']),
            models.Index(fields=['title_status']),
        ]


class AccidentRecord(models.Model):
    """Accident and damage history"""
    
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('total_loss', 'Total Loss'),
    ]
    
    SOURCE_CHOICES = [
        ('insurance', 'Insurance Claim'),
        ('police', 'Police Report'),
        ('repair_shop', 'Repair Shop'),
        ('crowdsourced', 'User Reported'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='accidents')
    
    accident_date = models.DateField(db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    
    damage_description = models.TextField(blank=True, null=True)
    estimated_damage_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    location_city = models.CharField(max_length=100, blank=True, null=True)
    location_state = models.CharField(max_length=2, blank=True, null=True)
    
    airbag_deployed = models.BooleanField(default=False)
    is_structural_damage = models.BooleanField(default=False)
    
    report_number = models.CharField(max_length=100, blank=True, null=True)
    verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accident_records'
        ordering = ['-accident_date']
        indexes = [
            models.Index(fields=['vehicle', '-accident_date']),
            models.Index(fields=['severity']),
            models.Index(fields=['verified']),
        ]


class MileageRecord(models.Model):
    """Odometer/mileage history"""
    
    SOURCE_CHOICES = [
        ('dmv', 'DMV Registration'),
        ('inspection', 'State Inspection'),
        ('service', 'Service Record'),
        ('dealer', 'Dealer Service'),
        ('insurance', 'Insurance'),
        ('sale', 'Sale Transaction'),
        ('crowdsourced', 'User Reported'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='mileage_records')
    
    recorded_date = models.DateField(db_index=True)
    mileage = models.IntegerField(validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=10, default='miles')
    
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_detail = models.CharField(max_length=255, blank=True, null=True)
    
    is_rollback_suspected = models.BooleanField(default=False)
    verified = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mileage_records'
        ordering = ['recorded_date']
        indexes = [
            models.Index(fields=['vehicle', 'recorded_date']),
            models.Index(fields=['is_rollback_suspected']),
        ]


class OwnershipRecord(models.Model):
    """Anonymized owner history"""
    
    OWNER_TYPES = [
        ('individual', 'Individual'),
        ('fleet', 'Fleet'),
        ('rental', 'Rental Company'),
        ('lease', 'Lease Company'),
        ('government', 'Government'),
        ('dealer', 'Dealer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='ownership_records')
    
    owner_sequence = models.IntegerField()
    owner_type = models.CharField(max_length=20, choices=OWNER_TYPES)
    
    ownership_start = models.DateField(db_index=True)
    ownership_end = models.DateField(null=True, blank=True, db_index=True)
    is_current = models.BooleanField(default=False)
    
    state = models.CharField(max_length=2, blank=True, null=True)
    ownership_duration_days = models.IntegerField(null=True, blank=True)
    
    # Anonymized/hashed owner identifier (for consent matching)
    owner_hash = models.CharField(max_length=64, blank=True, null=True)
    consented_to_tracking = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ownership_records'
        ordering = ['owner_sequence']
        unique_together = [['vehicle', 'owner_sequence']]
        indexes = [
            models.Index(fields=['vehicle', 'owner_sequence']),
            models.Index(fields=['is_current']),
        ]


class TheftRecord(models.Model):
    """Theft reports and recoveries"""
    
    STATUS_CHOICES = [
        ('reported', 'Reported Stolen'),
        ('recovered', 'Recovered'),
        ('closed', 'Case Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='theft_records')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    reported_date = models.DateField(db_index=True)
    recovered_date = models.DateField(null=True, blank=True)
    
    reporting_agency = models.CharField(max_length=255)
    case_number = models.CharField(max_length=100, blank=True, null=True)
    
    theft_location_city = models.CharField(max_length=100, blank=True, null=True)
    theft_location_state = models.CharField(max_length=2, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'theft_records'
        ordering = ['-reported_date']
        indexes = [
            models.Index(fields=['vehicle', 'status']),
            models.Index(fields=['reported_date']),
        ]


# ============================================================================
# TELEMATICS & TRACKING MODELS
# ============================================================================

class TelemetryTrace(models.Model):
    """GPS and telemetry data points (consent-required)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='telemetry_traces')
    
    timestamp = models.DateTimeField(db_index=True)
    
    # Location data
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)
    
    # Additional telemetry
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True)
    odometer = models.IntegerField(null=True, blank=True)
    
    # Device info
    device_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'telemetry_traces'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vehicle', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]


# ============================================================================
# CROWDSOURCED & USER-GENERATED CONTENT
# ============================================================================

class CrowdsourcedReport(models.Model):
    """User-submitted vehicle reports"""
    
    REPORT_TYPES = [
        ('sighting', 'Vehicle Sighting'),
        ('condition', 'Condition Report'),
        ('maintenance', 'Maintenance Record'),
        ('accident', 'Accident Report'),
        ('theft', 'Theft Report'),
        ('for_sale', 'For Sale Listing'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('duplicate', 'Duplicate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='crowdsourced_reports')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_reports')
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    report_date = models.DateField()
    description = models.TextField()
    
    location_city = models.CharField(max_length=100, blank=True, null=True)
    location_state = models.CharField(max_length=2, blank=True, null=True)
    
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_reports')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crowdsourced_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', 'status']),
            models.Index(fields=['report_type']),
            models.Index(fields=['status']),
        ]


# ============================================================================
# REPORT & TRANSACTION MODELS
# ============================================================================

class VehicleReport(models.Model):
    """Generated vehicle reports"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Generation'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reports')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_reports')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Report access control
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Report content flags
    include_telemetry = models.BooleanField(default=False)
    include_owner_history = models.BooleanField(default=True)
    
    # File storage
    pdf_file = models.FileField(upload_to='reports/pdf/', null=True, blank=True)
    json_data = models.JSONField(null=True, blank=True)
    
    generation_started_at = models.DateTimeField(null=True, blank=True)
    generation_completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicle_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vehicle', '-created_at']),
            models.Index(fields=['requested_by', '-created_at']),
            models.Index(fields=['status']),
        ]


class ReportPurchase(models.Model):
    """Report purchase transactions"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.OneToOneField(VehicleReport, on_delete=models.CASCADE, related_name='purchase')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchases')
    
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Simulated payment details
    payment_method = models.CharField(max_length=50, default='credit_card')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'report_purchases'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['payment_status']),
        ]


# ============================================================================
# EXTERNAL DATA PROVIDER MODELS
# ============================================================================

class DataProvider(models.Model):
    """External data source providers"""
    
    PROVIDER_TYPES = [
        ('vin_decoder', 'VIN Decoder'),
        ('dmv', 'DMV'),
        ('insurance', 'Insurance Company'),
        ('ncib', 'NCIB (Theft Database)'),
        ('police', 'Police Department'),
        ('service', 'Service Records'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    
    api_endpoint = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # API credentials (encrypted in production)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    
    rate_limit_per_hour = models.IntegerField(default=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_providers'


class ProviderDataFeed(models.Model):
    """Data ingestion from external providers"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(DataProvider, on_delete=models.CASCADE, related_name='feeds')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='provider_feeds', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    request_payload = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'provider_data_feeds'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['provider', '-requested_at']),
            models.Index(fields=['status']),
        ]


# ============================================================================
# AUDIT & SECURITY MODELS
# ============================================================================

class AuditLog(models.Model):
    """Comprehensive audit logging for restricted data access"""
    
    ACTION_TYPES = [
        ('view', 'View'),
        ('search', 'Search'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('access_restricted', 'Access Restricted Data'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50)
    resource_id = models.UUIDField(null=True, blank=True)
    
    # What was accessed
    field_accessed = models.CharField(max_length=100, blank=True, null=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Additional metadata
    metadata = models.JSONField(null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['vehicle', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]


class SearchQuery(models.Model):
    """Track all search queries for analytics and caching"""
    
    SEARCH_TYPES = [
        ('vin', 'VIN'),
        ('plate', 'License Plate'),
        ('make_model', 'Make/Model'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='searches')
    
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    query_text = models.CharField(max_length=255, db_index=True)
    
    vehicle_found = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='searches')
    results_count = models.IntegerField(default=0)
    
    # Performance metrics
    response_time_ms = models.IntegerField(null=True, blank=True)
    cache_hit = models.BooleanField(default=False)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query_text']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
        ]