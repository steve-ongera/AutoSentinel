"""
Django management command to seed AutoSentinel database with realistic test data
Usage: python manage.py seed_data [--clear]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from decimal import Decimal
from datetime import datetime, timedelta, date
import random
import hashlib
import uuid

from main_application.models import (
    User, Vehicle, VehicleRegistration, TitleEvent, AccidentRecord,
    MileageRecord, OwnershipRecord, TheftRecord, TelemetryTrace,
    CrowdsourcedReport, VehicleReport, ReportPurchase, DataProvider,
    ProviderDataFeed, AuditLog, SearchQuery
)


class Command(BaseCommand):
    help = 'Seeds the database with realistic test data for AutoSentinel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        with transaction.atomic():
            # Seed in order of dependencies
            users = self.seed_users()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))
            
            data_providers = self.seed_data_providers()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(data_providers)} data providers'))
            
            vehicles = self.seed_vehicles()
            self.stdout.write(self.style.SUCCESS(f'✓ Created {len(vehicles)} vehicles'))
            
            self.seed_vehicle_registrations(vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created vehicle registrations'))
            
            self.seed_title_events(vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created title events'))
            
            self.seed_accident_records(vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created accident records'))
            
            self.seed_mileage_records(vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created mileage records'))
            
            self.seed_ownership_records(vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created ownership records'))
            
            self.seed_theft_records(vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created theft records'))
            
            self.seed_telemetry_traces(vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created telemetry traces'))
            
            self.seed_crowdsourced_reports(vehicles, users)
            self.stdout.write(self.style.SUCCESS('✓ Created crowdsourced reports'))
            
            self.seed_vehicle_reports(vehicles, users)
            self.stdout.write(self.style.SUCCESS('✓ Created vehicle reports'))
            
            self.seed_provider_data_feeds(data_providers, vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created provider data feeds'))
            
            self.seed_audit_logs(users, vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created audit logs'))
            
            self.seed_search_queries(users, vehicles)
            self.stdout.write(self.style.SUCCESS('✓ Created search queries'))

        self.stdout.write(self.style.SUCCESS('\n========================================'))
        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('========================================\n'))

    def clear_data(self):
        """Clear all existing data"""
        models = [
            SearchQuery, AuditLog, ProviderDataFeed, ReportPurchase, 
            VehicleReport, CrowdsourcedReport, TelemetryTrace, TheftRecord,
            OwnershipRecord, MileageRecord, AccidentRecord, TitleEvent,
            VehicleRegistration, Vehicle, DataProvider, User
        ]
        
        for model in models:
            count = model.objects.all().delete()[0]
            if count > 0:
                self.stdout.write(f'  - Deleted {count} {model.__name__} records')

    def seed_users(self):
        """Create diverse user accounts"""
        users = []
        
        # Admin user
        admin = User.objects.create(
            username='steve_admin',
            email='admin@autosentinel.com',
            password=make_password('cp7kvt'),
            first_name='Admin',
            last_name='User',
            role='system_admin',
            is_staff=True,
            is_superuser=True,
            verified_at=timezone.now(),
            consent_to_data_usage=True,
            consent_date=timezone.now()
        )
        users.append(admin)
        
        # Guest users
        for i in range(5):
            user = User.objects.create(
                username=f'guest{i+1}',
                email=f'guest{i+1}@example.com',
                password=make_password('password123'),
                first_name=random.choice(['John', 'Jane', 'Michael', 'Sarah', 'David']),
                last_name=random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']),
                role='guest'
            )
            users.append(user)
        
        # Verified buyers
        for i in range(10):
            user = User.objects.create(
                username=f'buyer{i+1}',
                email=f'buyer{i+1}@example.com',
                password=make_password('password123'),
                first_name=random.choice(['Robert', 'Jennifer', 'William', 'Linda', 'Richard']),
                last_name=random.choice(['Davis', 'Miller', 'Wilson', 'Moore', 'Taylor']),
                role='verified_buyer',
                phone_number=f'+1-555-{random.randint(1000, 9999)}',
                verified_at=timezone.now() - timedelta(days=random.randint(1, 365)),
                consent_to_data_usage=True,
                consent_date=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            users.append(user)
        
        # Dealers
        dealer_companies = ['Premium Auto Sales', 'Elite Motors', 'Valley Car Dealers', 
                           'City Auto Group', 'Prestige Vehicles']
        for i, company in enumerate(dealer_companies):
            user = User.objects.create(
                username=f'dealer{i+1}',
                email=f'dealer{i+1}@{company.lower().replace(" ", "")}.com',
                password=make_password('password123'),
                first_name=random.choice(['Tom', 'Lisa', 'Mark', 'Emily', 'Steve']),
                last_name=random.choice(['Anderson', 'Thomas', 'Jackson', 'White', 'Harris']),
                role='dealer',
                company_name=company,
                phone_number=f'+1-555-{random.randint(1000, 9999)}',
                verified_at=timezone.now() - timedelta(days=random.randint(30, 365)),
                consent_to_data_usage=True,
                consent_date=timezone.now() - timedelta(days=random.randint(30, 365))
            )
            users.append(user)
        
        # Fleet administrators
        fleet_companies = ['National Fleet Services', 'Enterprise Fleet', 'Corporate Auto Fleet']
        for i, company in enumerate(fleet_companies):
            user = User.objects.create(
                username=f'fleet_admin{i+1}',
                email=f'fleet{i+1}@{company.lower().replace(" ", "")}.com',
                password=make_password('password123'),
                first_name=random.choice(['James', 'Patricia', 'Christopher', 'Barbara', 'Daniel']),
                last_name=random.choice(['Martin', 'Thompson', 'Garcia', 'Martinez', 'Robinson']),
                role='fleet_admin',
                company_name=company,
                phone_number=f'+1-555-{random.randint(1000, 9999)}',
                verified_at=timezone.now() - timedelta(days=random.randint(60, 365)),
                consent_to_data_usage=True,
                consent_date=timezone.now() - timedelta(days=random.randint(60, 365))
            )
            users.append(user)
        
        # Auditors
        for i in range(2):
            user = User.objects.create(
                username=f'auditor{i+1}',
                email=f'auditor{i+1}@autosentinel.com',
                password=make_password('password123'),
                first_name=random.choice(['Kevin', 'Nancy', 'Brian', 'Sandra', 'George']),
                last_name=random.choice(['Clark', 'Rodriguez', 'Lewis', 'Lee', 'Walker']),
                role='auditor',
                company_name='AutoSentinel Inc.',
                verified_at=timezone.now() - timedelta(days=random.randint(90, 365)),
                consent_to_data_usage=True,
                consent_date=timezone.now() - timedelta(days=random.randint(90, 365))
            )
            users.append(user)
        
        return users

    def seed_data_providers(self):
        """Create external data providers"""
        providers = []
        
        provider_data = [
            ('NHTSA VIN Decoder', 'vin_decoder', 'https://vpic.nhtsa.dot.gov/api/', 10000),
            ('California DMV', 'dmv', 'https://api.dmv.ca.gov/v1/', 5000),
            ('Texas DMV', 'dmv', 'https://api.txdmv.gov/v1/', 5000),
            ('State Farm Insurance', 'insurance', 'https://api.statefarm.com/claims/', 2000),
            ('Geico Insurance', 'insurance', 'https://api.geico.com/claims/', 2000),
            ('NCIC Stolen Vehicle Database', 'ncib', 'https://api.ncic.fbi.gov/stolen/', 1000),
            ('Los Angeles Police Department', 'police', 'https://api.lapd.gov/reports/', 500),
            ('Jiffy Lube Service Records', 'service', 'https://api.jiffylube.com/records/', 3000),
        ]
        
        for name, provider_type, endpoint, rate_limit in provider_data:
            provider = DataProvider.objects.create(
                name=name,
                provider_type=provider_type,
                api_endpoint=endpoint,
                is_active=True,
                api_key=f'key_{uuid.uuid4().hex[:16]}',
                api_secret=f'secret_{uuid.uuid4().hex[:32]}',
                rate_limit_per_hour=rate_limit
            )
            providers.append(provider)
        
        return providers

    def seed_vehicles(self):
        """Create realistic vehicle records"""
        vehicles = []
        
        # Vehicle data templates
        makes_models = [
            ('Toyota', ['Camry', 'Corolla', 'RAV4', 'Highlander', 'Tacoma']),
            ('Honda', ['Civic', 'Accord', 'CR-V', 'Pilot', 'Odyssey']),
            ('Ford', ['F-150', 'Mustang', 'Explorer', 'Escape', 'Fusion']),
            ('Chevrolet', ['Silverado', 'Equinox', 'Malibu', 'Traverse', 'Tahoe']),
            ('Nissan', ['Altima', 'Rogue', 'Sentra', 'Pathfinder', 'Frontier']),
            ('BMW', ['3 Series', '5 Series', 'X3', 'X5', 'X7']),
            ('Mercedes-Benz', ['C-Class', 'E-Class', 'GLC', 'GLE', 'S-Class']),
            ('Tesla', ['Model 3', 'Model Y', 'Model S', 'Model X']),
            ('Jeep', ['Wrangler', 'Grand Cherokee', 'Cherokee', 'Compass', 'Gladiator']),
            ('RAM', ['1500', '2500', '3500', 'ProMaster']),
        ]
        
        colors = ['White', 'Black', 'Silver', 'Gray', 'Red', 'Blue', 'Green', 'Beige', 'Brown']
        body_styles = ['Sedan', 'SUV', 'Truck', 'Coupe', 'Hatchback', 'Wagon', 'Van']
        transmissions = ['Automatic', 'Manual', '8-Speed Automatic', 'CVT', '10-Speed Automatic']
        drivetrains = ['FWD', 'RWD', 'AWD', '4WD']
        fuel_types = ['Gasoline', 'Diesel', 'Hybrid', 'Electric', 'Plug-in Hybrid']
        
        for i in range(100):
            make, models = random.choice(makes_models)
            model = random.choice(models)
            year = random.randint(2010, 2024)
            
            # Generate realistic VIN
            vin = self.generate_vin(make, year)
            
            # Determine if stolen (2% chance)
            is_stolen = random.random() < 0.02
            
            # Title status based on age and random factors
            if year < 2015:
                title_choices = ['clean', 'clean', 'clean', 'rebuilt', 'salvage']
            else:
                title_choices = ['clean', 'clean', 'clean', 'clean', 'flood']
            
            title_status = random.choice(title_choices)
            
            # Mileage based on year
            years_old = 2024 - year
            base_mileage = years_old * 12000
            current_mileage = base_mileage + random.randint(-5000, 5000)
            current_mileage = max(0, current_mileage)
            
            # Consent for tracking (30% chance)
            consenting = random.random() < 0.3
            
            vehicle = Vehicle.objects.create(
                vin=vin,
                make=make,
                model=model,
                year=year,
                trim=random.choice(['Base', 'LX', 'EX', 'Limited', 'Premium', 'Sport']) if random.random() > 0.3 else None,
                body_style=random.choice(body_styles),
                color=random.choice(colors),
                engine=f'{random.choice([1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0])}L V{random.choice([4, 6, 8])}',
                transmission=random.choice(transmissions),
                drivetrain=random.choice(drivetrains),
                fuel_type=random.choice(fuel_types) if make != 'Tesla' else 'Electric',
                displacement=Decimal(str(random.choice([1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]))),
                cylinders=random.choice([4, 6, 8]),
                manufacture_country=random.choice(['USA', 'Japan', 'Germany', 'South Korea', 'Mexico']),
                manufacture_plant=f'Plant {random.randint(1, 5)}',
                manufacture_date=date(year, random.randint(1, 12), random.randint(1, 28)),
                current_mileage=current_mileage,
                current_title_status=title_status,
                is_stolen=is_stolen,
                current_owner_count=random.randint(1, 5),
                consenting_for_tracking=consenting,
                tracking_consent_date=timezone.now() - timedelta(days=random.randint(1, 365)) if consenting else None,
                last_reported_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            vehicles.append(vehicle)
        
        return vehicles

    def generate_vin(self, make, year):
        """Generate a realistic-looking VIN"""
        # WMI (World Manufacturer Identifier) - first 3 characters
        wmi_map = {
            'Toyota': ['JTD', '5TD', '4T1'],
            'Honda': ['1HG', '2HG', '19X'],
            'Ford': ['1FA', '1FT', '3FA'],
            'Chevrolet': ['1GC', '1G1', '2G1'],
            'Nissan': ['1N4', '3N1', 'JN8'],
            'BMW': ['WBA', 'WBS', '5UX'],
            'Mercedes-Benz': ['WDD', 'WDC', '4JG'],
            'Tesla': ['5YJ', '7SA'],
            'Jeep': ['1C4', '1J4'],
            'RAM': ['1C6', '3C6'],
        }
        
        wmi = random.choice(wmi_map.get(make, ['1XX']))
        
        # VDS (Vehicle Descriptor Section) - next 6 characters
        vds = ''.join(random.choices('ABCDEFGHJKLMNPRSTUVWXYZ0123456789', k=6))
        
        # Year code (10th position)
        year_code = {
            2010: 'A', 2011: 'B', 2012: 'C', 2013: 'D', 2014: 'E',
            2015: 'F', 2016: 'G', 2017: 'H', 2018: 'J', 2019: 'K',
            2020: 'L', 2021: 'M', 2022: 'N', 2023: 'P', 2024: 'R'
        }.get(year, 'X')
        
        # Rest of VIN
        rest = ''.join(random.choices('ABCDEFGHJKLMNPRSTUVWXYZ0123456789', k=7))
        
        return f'{wmi}{vds}{year_code}{rest}'

    def seed_vehicle_registrations(self, vehicles):
        """Create vehicle registration records"""
        states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
        
        for vehicle in vehicles:
            # 1-3 registration records per vehicle
            num_registrations = random.randint(1, 3)
            
            for i in range(num_registrations):
                is_current = (i == num_registrations - 1)
                issued_date = date(vehicle.year, random.randint(1, 12), random.randint(1, 28)) + timedelta(days=i*365)
                
                VehicleRegistration.objects.create(
                    vehicle=vehicle,
                    plate_number=self.generate_plate_number(),
                    state=random.choice(states),
                    country='US',
                    issued_date=issued_date,
                    expiry_date=issued_date + timedelta(days=365) if random.random() > 0.1 else None,
                    is_current=is_current
                )

    def generate_plate_number(self):
        """Generate realistic license plate number"""
        formats = [
            lambda: f'{random.randint(1, 9)}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.randint(100, 999)}',
            lambda: f'{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}-{random.randint(1000, 9999)}',
            lambda: f'{random.randint(100, 999)}-{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}{random.choice("ABCDEFGHJKLMNPRSTUVWXYZ")}',
        ]
        return random.choice(formats)()

    def seed_title_events(self, vehicles):
        """Create title event history"""
        states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
        sources = ['DMV', 'State Title Office', 'Auto Auction', 'Insurance Company']
        
        for vehicle in vehicles:
            # Initial title
            initial_date = date(vehicle.year, random.randint(1, 12), random.randint(1, 28))
            
            TitleEvent.objects.create(
                vehicle=vehicle,
                event_type='initial',
                event_date=initial_date,
                title_status='clean',
                state=random.choice(states),
                title_number=f'T{random.randint(100000, 999999)}',
                odometer_reading=random.randint(5, 50),
                source=random.choice(sources)
            )
            
            # Additional events based on owner count
            for i in range(vehicle.current_owner_count - 1):
                days_offset = 365 * (i + 1) + random.randint(-30, 30)
                event_date = initial_date + timedelta(days=days_offset)
                
                if event_date > date.today():
                    continue
                
                event_type = random.choice(['transfer', 'transfer', 'transfer', 'brand_change', 'lien_add', 'lien_release'])
                
                # Determine title status for this event
                if event_type == 'brand_change':
                    title_status = random.choice(['salvage', 'rebuilt', 'flood'])
                else:
                    title_status = vehicle.current_title_status
                
                TitleEvent.objects.create(
                    vehicle=vehicle,
                    event_type=event_type,
                    event_date=event_date,
                    title_status=title_status,
                    state=random.choice(states),
                    title_number=f'T{random.randint(100000, 999999)}',
                    odometer_reading=int(vehicle.current_mileage * (i + 1) / vehicle.current_owner_count),
                    source=random.choice(sources)
                )

    def seed_accident_records(self, vehicles):
        """Create accident history"""
        cities = [
            ('Los Angeles', 'CA'), ('Houston', 'TX'), ('Miami', 'FL'),
            ('New York', 'NY'), ('Chicago', 'IL'), ('Phoenix', 'AZ'),
            ('Philadelphia', 'PA'), ('San Antonio', 'TX'), ('Dallas', 'TX')
        ]
        
        damage_descriptions = [
            'Front end collision, damage to bumper and hood',
            'Rear-ended at intersection, trunk and bumper damage',
            'Side impact collision, driver door and fender damaged',
            'Minor parking lot incident, scratches and dents',
            'Multi-vehicle accident on highway',
            'Single vehicle accident, hit guardrail',
            'Hail damage to hood, roof, and trunk',
            'Flood damage, water reached interior',
        ]
        
        # 30% of vehicles have accidents
        accident_vehicles = random.sample(vehicles, int(len(vehicles) * 0.3))
        
        for vehicle in accident_vehicles:
            num_accidents = random.randint(1, 3)
            
            for i in range(num_accidents):
                severity = random.choice(['minor', 'minor', 'moderate', 'severe', 'total_loss'])
                source = random.choice(['insurance', 'insurance', 'police', 'repair_shop'])
                city, state = random.choice(cities)
                
                accident_date = date(vehicle.year, 1, 1) + timedelta(days=random.randint(0, (date.today() - date(vehicle.year, 1, 1)).days))
                
                cost_ranges = {
                    'minor': (500, 3000),
                    'moderate': (3000, 8000),
                    'severe': (8000, 20000),
                    'total_loss': (20000, 50000)
                }
                
                min_cost, max_cost = cost_ranges[severity]
                
                AccidentRecord.objects.create(
                    vehicle=vehicle,
                    accident_date=accident_date,
                    severity=severity,
                    source=source,
                    damage_description=random.choice(damage_descriptions),
                    estimated_damage_cost=Decimal(str(random.randint(min_cost, max_cost))),
                    location_city=city,
                    location_state=state,
                    airbag_deployed=severity in ['severe', 'total_loss'] and random.random() > 0.3,
                    is_structural_damage=severity in ['severe', 'total_loss'] and random.random() > 0.5,
                    report_number=f'ACC{random.randint(100000, 999999)}' if source in ['insurance', 'police'] else None,
                    verified=source in ['insurance', 'police']
                )

    def seed_mileage_records(self, vehicles):
        """Create odometer reading history"""
        sources = ['dmv', 'inspection', 'service', 'dealer', 'insurance']
        
        for vehicle in vehicles:
            years_old = 2024 - vehicle.year
            
            # Create 3-8 mileage records per year
            num_records = years_old * random.randint(3, 8)
            
            current_mileage = vehicle.current_mileage
            mileage_per_record = current_mileage // num_records if num_records > 0 else 0
            
            for i in range(num_records):
                days_offset = int((365 * years_old) * (i / num_records))
                recorded_date = date(vehicle.year, 1, 1) + timedelta(days=days_offset)
                
                if recorded_date > date.today():
                    continue
                
                # Calculate progressive mileage with some variance
                mileage = int(mileage_per_record * i + random.randint(-500, 500))
                mileage = max(0, mileage)
                
                # 1% chance of rollback suspicion
                is_rollback = random.random() < 0.01
                
                MileageRecord.objects.create(
                    vehicle=vehicle,
                    recorded_date=recorded_date,
                    mileage=mileage,
                    source=random.choice(sources),
                    source_detail=f'{random.choice(["Annual", "Bi-annual", "Registration"])} {random.choice(["inspection", "service", "renewal"])}',
                    is_rollback_suspected=is_rollback,
                    verified=not is_rollback
                )

    def seed_ownership_records(self, vehicles):
        """Create anonymized ownership history"""
        
        for vehicle in vehicles:
            owner_types_pool = ['individual', 'individual', 'individual', 'fleet', 'rental', 'lease', 'dealer']
            states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
            
            years_old = 2024 - vehicle.year
            ownership_start = date(vehicle.year, random.randint(1, 12), random.randint(1, 28))
            
            for i in range(vehicle.current_owner_count):
                is_current = (i == vehicle.current_owner_count - 1)
                
                # Calculate ownership period
                if is_current:
                    ownership_end = None
                    duration = (date.today() - ownership_start).days
                else:
                    duration = random.randint(180, 1095)  # 6 months to 3 years
                    ownership_end = ownership_start + timedelta(days=duration)
                
                # Generate owner hash
                owner_hash = hashlib.sha256(f'{vehicle.vin}_{i}_{random.random()}'.encode()).hexdigest()
                
                OwnershipRecord.objects.create(
                    vehicle=vehicle,
                    owner_sequence=i + 1,
                    owner_type=random.choice(owner_types_pool),
                    ownership_start=ownership_start,
                    ownership_end=ownership_end,
                    is_current=is_current,
                    state=random.choice(states),
                    ownership_duration_days=duration if not is_current else None,
                    owner_hash=owner_hash,
                    consented_to_tracking=vehicle.consenting_for_tracking and is_current
                )
                
                if not is_current:
                    ownership_start = ownership_end + timedelta(days=random.randint(1, 30))

    def seed_theft_records(self, vehicles):
        """Create theft records for stolen vehicles"""
        cities = [
            ('Los Angeles', 'CA'), ('Houston', 'TX'), ('Miami', 'FL'),
            ('New York', 'NY'), ('Chicago', 'IL'), ('Phoenix', 'AZ')
        ]
        
        agencies = [
            'Los Angeles Police Department',
            'Houston Police Department',
            'Miami-Dade Police',
            'NYPD',
            'Chicago Police Department',
            'Phoenix Police Department'
        ]
        
        stolen_vehicles = [v for v in vehicles if v.is_stolen]
        
        for vehicle in stolen_vehicles:
            city, state = random.choice(cities)
            reported_date = date.today() - timedelta(days=random.randint(1, 180))
            
            # 30% chance vehicle was recovered
            is_recovered = random.random() < 0.3
            
            TheftRecord.objects.create(
                vehicle=vehicle,
                status='recovered' if is_recovered else 'reported',
                reported_date=reported_date,
                recovered_date=reported_date + timedelta(days=random.randint(7, 60)) if is_recovered else None,
                reporting_agency=random.choice(agencies),
                case_number=f'THEFT{random.randint(100000, 999999)}',
                theft_location_city=city,
                theft_location_state=state,
                notes='Vehicle reported stolen by owner' if not is_recovered else 'Vehicle recovered in good condition'
            )

    def seed_telemetry_traces(self, vehicles):
        """Create GPS telemetry data for consenting vehicles"""
        consenting_vehicles = [v for v in vehicles if v.consenting_for_tracking]
        
        # Base coordinates for major cities
        city_coords = [
            (34.0522, -118.2437),  # Los Angeles
            (29.7604, -95.3698),   # Houston
            (40.7128, -74.0060),   # New York
            (41.8781, -87.6298),   # Chicago
            (33.4484, -112.0740),  # Phoenix
        ]
        
        for vehicle in consenting_vehicles[:20]:  # Limit to 20 vehicles for performance
            base_lat, base_lng = random.choice(city_coords)
            
            # Create telemetry traces for the last 30 days
            num_traces = random.randint(50, 200)
            
            for i in range(num_traces):
                timestamp = timezone.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                # Add some randomness to coordinates (within ~50km radius)
                lat_offset = random.uniform(-0.5, 0.5)
                lng_offset = random.uniform(-0.5, 0.5)
                
                TelemetryTrace.objects.create(
                    vehicle=vehicle,
                    timestamp=timestamp,
                    latitude=Decimal(str(base_lat + lat_offset)),
                    longitude=Decimal(str(base_lng + lng_offset)),
                    accuracy=random.uniform(5.0, 50.0),
                    speed=random.uniform(0, 75),
                    heading=random.uniform(0, 360),
                    altitude=random.uniform(0, 500),
                    odometer=vehicle.current_mileage + random.randint(-1000, 0),
                    device_id=f'GPS-{uuid.uuid4().hex[:12]}'
                )

    def seed_crowdsourced_reports(self, vehicles, users):
        """Create user-submitted reports"""
        verified_users = [u for u in users if u.role in ['verified_buyer', 'dealer', 'fleet_admin']]
        
        cities_states = [
            ('Los Angeles', 'CA'), ('Houston', 'TX'), ('Miami', 'FL'),
            ('New York', 'NY'), ('Chicago', 'IL'), ('Phoenix', 'AZ'),
            ('Philadelphia', 'PA'), ('San Antonio', 'TX'), ('Dallas', 'TX')
        ]
        
        descriptions = {
            'sighting': [
                'Saw this vehicle parked at shopping mall',
                'Vehicle spotted in residential area',
                'Observed at gas station on Highway 101',
            ],
            'condition': [
                'Vehicle appears to be in excellent condition, well maintained',
                'Some visible wear and tear, paint fading on hood',
                'Minor dents on passenger side, otherwise good condition',
            ],
            'maintenance': [
                'Just completed oil change and tire rotation',
                'Recent brake service performed',
                'Full service including fluid changes and filter replacement',
            ],
            'accident': [
                'Witnessed minor fender bender in parking lot',
                'Vehicle involved in side-swipe collision',
                'Minor accident at intersection, front bumper damage',
            ],
            'for_sale': [
                'Vehicle listed for sale on local marketplace',
                'Saw for sale sign in vehicle window',
                'Owner advertising vehicle for sale',
            ],
        }
        
        # Create 50-100 crowdsourced reports
        for _ in range(random.randint(50, 100)):
            vehicle = random.choice(vehicles)
            report_type = random.choice(['sighting', 'condition', 'maintenance', 'accident', 'for_sale', 'other'])
            status = random.choice(['pending', 'verified', 'verified', 'rejected', 'duplicate'])
            
            report_date = date.today() - timedelta(days=random.randint(1, 180))
            city, state = random.choice(cities_states)
            
            report = CrowdsourcedReport.objects.create(
                vehicle=vehicle,
                submitted_by=random.choice(verified_users) if verified_users else None,
                report_type=report_type,
                status=status,
                report_date=report_date,
                description=random.choice(descriptions.get(report_type, ['General report about vehicle'])),
                location_city=city,
                location_state=state
            )
            
            # If verified, add verification info
            if status == 'verified':
                auditors = [u for u in users if u.role in ['auditor', 'system_admin']]
                if auditors:
                    report.verified_by = random.choice(auditors)
                    report.verified_at = timezone.now() - timedelta(days=random.randint(1, 30))
                    report.save()

    def seed_vehicle_reports(self, vehicles, users):
        """Create vehicle history reports"""
        buyers = [u for u in users if u.role in ['verified_buyer', 'dealer']]
        
        # Create 30-50 reports
        for _ in range(random.randint(30, 50)):
            vehicle = random.choice(vehicles)
            user = random.choice(buyers) if buyers else None
            
            status = random.choice(['completed', 'completed', 'completed', 'processing', 'pending'])
            is_paid = status == 'completed'
            price = Decimal(str(random.choice([9.99, 19.99, 29.99, 39.99])))
            
            report = VehicleReport.objects.create(
                vehicle=vehicle,
                requested_by=user,
                status=status,
                is_paid=is_paid,
                price=price,
                include_telemetry=vehicle.consenting_for_tracking and random.random() > 0.5,
                include_owner_history=True,
            )
            
            if status == 'completed':
                report.generation_started_at = timezone.now() - timedelta(hours=random.randint(1, 48))
                report.generation_completed_at = report.generation_started_at + timedelta(seconds=random.randint(30, 300))
                report.json_data = {
                    'vin': vehicle.vin,
                    'make': vehicle.make,
                    'model': vehicle.model,
                    'year': vehicle.year,
                    'title_status': vehicle.current_title_status,
                    'mileage': vehicle.current_mileage,
                    'owners': vehicle.current_owner_count
                }
                report.save()
                
                # Create purchase record if paid
                if is_paid:
                    ReportPurchase.objects.create(
                        report=report,
                        user=user,
                        amount=price,
                        payment_status='completed',
                        payment_method=random.choice(['credit_card', 'debit_card', 'paypal']),
                        transaction_id=f'TXN{uuid.uuid4().hex[:16].upper()}',
                        completed_at=report.generation_completed_at
                    )

    def seed_provider_data_feeds(self, providers, vehicles):
        """Create data provider feed records"""
        
        # Create 100-200 feed records
        for _ in range(random.randint(100, 200)):
            provider = random.choice(providers)
            vehicle = random.choice(vehicles) if random.random() > 0.1 else None
            status = random.choice(['completed', 'completed', 'completed', 'processing', 'failed', 'pending'])
            
            feed = ProviderDataFeed.objects.create(
                provider=provider,
                vehicle=vehicle,
                status=status,
                request_payload={
                    'vin': vehicle.vin if vehicle else f'1HGBH41JXMN{random.randint(100000, 999999)}',
                    'request_type': provider.provider_type,
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            if status == 'completed':
                feed.response_data = {
                    'success': True,
                    'data': {
                        'vin': vehicle.vin if vehicle else 'Unknown',
                        'make': vehicle.make if vehicle else 'Unknown',
                        'model': vehicle.model if vehicle else 'Unknown',
                        'year': vehicle.year if vehicle else 0,
                    },
                    'provider': provider.name,
                    'timestamp': timezone.now().isoformat()
                }
                feed.completed_at = timezone.now() - timedelta(seconds=random.randint(1, 300))
                feed.save()
            elif status == 'failed':
                feed.error_message = random.choice([
                    'VIN not found in database',
                    'API rate limit exceeded',
                    'Connection timeout',
                    'Invalid response from provider',
                    'Authentication failed'
                ])
                feed.completed_at = timezone.now() - timedelta(seconds=random.randint(1, 60))
                feed.save()

    def seed_audit_logs(self, users, vehicles):
        """Create audit log entries"""
        actions = ['view', 'search', 'create', 'update', 'export', 'access_restricted']
        resource_types = ['Vehicle', 'VehicleReport', 'AccidentRecord', 'TelemetryTrace', 'User']
        
        ip_addresses = [
            '192.168.1.100', '192.168.1.101', '10.0.0.50',
            '172.16.0.200', '203.0.113.45', '198.51.100.78'
        ]
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
        ]
        
        # Create 200-500 audit logs
        for _ in range(random.randint(200, 500)):
            user = random.choice(users)
            action = random.choice(actions)
            resource_type = random.choice(resource_types)
            vehicle = random.choice(vehicles) if random.random() > 0.3 else None
            
            timestamp = timezone.now() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            AuditLog.objects.create(
                user=user,
                action=action,
                resource_type=resource_type,
                resource_id=uuid.uuid4(),
                field_accessed=random.choice(['vin', 'telemetry', 'owner_history', 'accident_records']) if action == 'access_restricted' else None,
                vehicle=vehicle,
                ip_address=random.choice(ip_addresses),
                user_agent=random.choice(user_agents),
                metadata={
                    'session_id': uuid.uuid4().hex[:16],
                    'duration_ms': random.randint(100, 5000),
                    'success': True
                },
                timestamp=timestamp
            )

    def seed_search_queries(self, users, vehicles):
        """Create search query records"""
        
        # VIN searches
        for _ in range(random.randint(100, 200)):
            user = random.choice(users) if random.random() > 0.2 else None
            vehicle = random.choice(vehicles)
            found = random.random() > 0.1
            
            SearchQuery.objects.create(
                user=user,
                search_type='vin',
                query_text=vehicle.vin if found else self.generate_vin('Unknown', 2020),
                vehicle_found=vehicle if found else None,
                results_count=1 if found else 0,
                response_time_ms=random.randint(50, 500),
                cache_hit=random.random() > 0.6,
                ip_address=f'192.168.1.{random.randint(1, 255)}',
                created_at=timezone.now() - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23)
                )
            )
        
        # License plate searches
        plates = [reg.plate_number for vehicle in vehicles for reg in vehicle.registrations.all()]
        
        for _ in range(random.randint(50, 100)):
            user = random.choice(users) if random.random() > 0.2 else None
            found = random.random() > 0.15
            
            SearchQuery.objects.create(
                user=user,
                search_type='plate',
                query_text=random.choice(plates) if plates and found else self.generate_plate_number(),
                vehicle_found=random.choice(vehicles) if found else None,
                results_count=random.randint(1, 3) if found else 0,
                response_time_ms=random.randint(75, 600),
                cache_hit=random.random() > 0.5,
                ip_address=f'10.0.0.{random.randint(1, 255)}',
                created_at=timezone.now() - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23)
                )
            )
        
        # Make/model searches
        makes = list(set(v.make for v in vehicles))
        
        for _ in range(random.randint(150, 300)):
            user = random.choice(users) if random.random() > 0.3 else None
            make = random.choice(makes)
            matching_vehicles = [v for v in vehicles if v.make == make]
            
            SearchQuery.objects.create(
                user=user,
                search_type='make_model',
                query_text=f'{make} {random.choice(matching_vehicles).model if matching_vehicles else "Unknown"}',
                vehicle_found=random.choice(matching_vehicles) if matching_vehicles else None,
                results_count=len(matching_vehicles) if matching_vehicles else 0,
                response_time_ms=random.randint(100, 800),
                cache_hit=random.random() > 0.4,
                ip_address=f'172.16.0.{random.randint(1, 255)}',
                created_at=timezone.now() - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23)
                )
            )