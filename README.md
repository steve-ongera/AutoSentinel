# AutoSentinel 🚗🔍

**Professional vehicle history tracking and monitoring system**

AutoSentinel is a comprehensive Django-based web application that enables users to search vehicles by VIN, license plate, or registration number and receive detailed vehicle history reports including accident records, title history, theft records, mileage tracking, and optional GPS telemetry data.

## 🌟 Features

### Core Functionality
- **VIN/License Plate Search** - Fast vehicle lookup with sub-500ms response time
- **Comprehensive Vehicle Reports** - Decoded VIN specs, title history, accident records, odometer readings
- **Title Brand Tracking** - Salvage, rebuilt, flood damage, lemon law detection
- **Theft Record Database** - Real-time stolen vehicle flags
- **Mileage History** - Odometer rollback detection
- **Owner History** - Anonymized ownership timeline
- **Crowdsourced Reports** - Community-driven vehicle sightings and condition reports
- **GPS Telemetry** - Location tracking for consenting vehicles/fleets

### Security & Compliance
- **Role-Based Access Control** - Guest, Verified Buyer, Dealer, Fleet Admin, Auditor, System Admin
- **Consent Management** - Explicit tracking consent required for telemetry data
- **Comprehensive Audit Logging** - Full access trail for restricted data
- **Data Encryption** - Sensitive fields encrypted at rest

### Professional Features
- **PDF Report Generation** - Professional vehicle history reports
- **Bulk Search** - Enterprise-level batch processing
- **External Data Integration** - VIN decoder, DMV, insurance company APIs
- **Background Tasks** - Asynchronous data refresh via Celery
- **Advanced Caching** - Redis-powered sub-second search results

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Docker & Docker Compose (recommended)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/autosentinel.git
cd autosentinel
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=autosentinel
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# External APIs
VIN_DECODER_API_KEY=your-api-key
VIN_DECODER_API_URL=https://api.vindecoder.example/v1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@autosentinel.com
```

### 3. Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load seed data (generates 50,000+ vehicles)
docker-compose exec web python manage.py seed_data

# Access the application
# Web: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### 4. Manual Setup (Alternative)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load seed data
python manage.py seed_data

# Start Redis (in another terminal)
redis-server

# Start Celery worker (in another terminal)
celery -A autosentinel worker -l info

# Start Celery beat (in another terminal)
celery -A autosentinel beat -l info

# Run development server
python manage.py runserver
```

## 📁 Project Structure

```
autosentinel/
├── autosentinel/          # Project configuration
│   ├── settings.py        # Main settings
│   ├── urls.py
│   └── wsgi.py
├── core/                  # Main application
│   ├── models.py          # Database models
│   ├── views.py           # Django views
│   ├── middleware.py      # Audit logging middleware
│   ├── tasks.py           # Celery tasks
│   └── management/
│       └── commands/
│           └── seed_data.py
├── api/                   # REST API
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── reports/               # Report generation
│   ├── pdf_generator.py
│   └── tasks.py
├── search/                # Search functionality
│   ├── services.py
│   └── views.py
├── templates/             # Django templates
│   ├── base.html
│   ├── search.html
│   └── report.html
├── static/               # Static files (CSS, JS)
├── media/                # User uploads, PDFs
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🎯 API Endpoints

### Search
- `GET /api/search/vin/?q=<VIN>` - Search by VIN
- `GET /api/search/plate/?plate=<PLATE>&state=<STATE>` - Search by license plate

### Vehicle Reports
- `GET /api/vehicles/<uuid>/` - Get vehicle details
- `GET /api/vehicles/<uuid>/report/` - Get full vehicle report
- `POST /api/vehicles/<uuid>/report/purchase/` - Purchase report

### Telemetry (Consent Required)
- `POST /api/telemetry/ingest/` - Ingest GPS trace data
- `GET /api/vehicles/<uuid>/telemetry/` - Get vehicle telemetry history

### Crowdsourced
- `POST /api/reports/crowdsourced/` - Submit user report
- `GET /api/reports/crowdsourced/<uuid>/` - Get report details

## 🔐 User Roles & Permissions

| Role | Permissions |
|------|-------------|
| **Guest** | View basic vehicle info |
| **Verified Buyer** | Purchase and view full reports |
| **Dealer** | Bulk search, full reports |
| **Fleet Admin** | Manage fleet, view telemetry |
| **Auditor** | View all reports and audit logs |
| **System Admin** | Full system access |

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report

# Run specific test module
python manage.py test core.tests.test_models
```

## 📊 Seed Data

The `seed_data` management command generates realistic simulated data:

```bash
python manage.py seed_data --vehicles 50000 --users 100
```

**Generated Data:**
- 50,000+ vehicles with realistic VINs
- Title events, accident records, mileage logs
- Theft flags, owner history
- Crowdsourced reports
- Telemetry traces (for consenting vehicles)

**Example VINs after seeding:**
- `1HGCM82633A004352` - 2003 Honda Accord (clean title)
- `1FTFW1ET5DFC10312` - 2013 Ford F-150 (accident history)
- `5UXWX7C5XBA123456` - 2011 BMW X3 (salvage title)

## 🎨 Frontend Stack (Django Templates + HTMX)

- **Django Templates** - Server-side rendering
- **HTMX** - Dynamic interactions without React
- **Bootstrap 5** - Responsive UI components
- **Alpine.js** - Lightweight reactivity

## 🔄 Background Tasks (Celery)

### Periodic Tasks
- **Refresh Provider Data** - Every 6 hours
- **Check Theft Database** - Every 1 hour
- **Cleanup Old Searches** - Daily

### Async Tasks
- PDF report generation
- External API data fetching
- Bulk data imports

## 📈 Performance Targets

- **Search Response Time:** <500ms (cached VINs)
- **Report Generation:** <10s (cached data)
- **API Rate Limits:** 1000 req/hour (authenticated users)

## 🛡️ Security Features

- HTTPS/SSL enforcement (production)
- CSRF protection
- SQL injection prevention (Django ORM)
- XSS protection
- Rate limiting
- Audit logging for restricted data access
- Encrypted sensitive fields

## 📦 Deployment

### Docker Production Build

```bash
# Build production image
docker build -t autosentinel:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n autosentinel
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues, questions, or contributions:
- **Issues:** [GitHub Issues](https://github.com/yourusername/autosentinel/issues)
- **Docs:** [Full Documentation](https://docs.autosentinel.example)
- **Email:** support@autosentinel.example

## 🙏 Acknowledgments

- VIN decoder APIs
- Django & Django REST Framework
- HTMX for dynamic UX
- Bootstrap 5 for UI components

---

**Built with Steve Ongera using Django**