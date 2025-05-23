# DarkFov - Sistema de Vendas

## Overview

DarkFov is a web-based sales platform for gaming software (specifically aimbot for BloodStrike), built with FastAPI backend and vanilla HTML/CSS/JavaScript frontend. The system provides user authentication, license management, payment processing, and administrative controls.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI with Python 3.11
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Template Engine**: Jinja2 for server-side rendering
- **Static Files**: Served directly through FastAPI

### Frontend Architecture
- **Technology**: Vanilla HTML, CSS, and JavaScript
- **Styling**: Custom CSS with CSS variables for theming
- **UI Components**: Gaming-focused dark theme with neon accents
- **Responsiveness**: Mobile-first responsive design

### Database Design
The application uses a PostgreSQL database with three main entities:
- **Users**: Authentication and license management
- **Payments**: Transaction records and billing history
- **AdminLog**: Administrative action tracking

## Key Components

### Authentication System
- JWT-based authentication with configurable expiration
- bcrypt password hashing for security
- Role-based access control (admin vs regular users)
- Middleware for protecting routes

### License Management
- Time-based license expiration system
- License verification for software access
- Payment integration for license renewal
- Status tracking and validation

### Admin Panel
- User management and statistics
- Payment monitoring and reporting
- System administration controls
- Activity logging and audit trails

### Payment Processing
- Payment record creation and tracking
- Multiple plan support (monthly, quarterly, annual)
- Integration ready for payment gateways
- License extension upon successful payment

## Data Flow

1. **User Registration**: Users create accounts with email/password
2. **Authentication**: JWT tokens issued upon successful login
3. **License Purchase**: Users select plans and make payments
4. **License Activation**: Successful payments extend user licenses
5. **Software Access**: Valid licenses allow software downloads
6. **Admin Oversight**: Administrators monitor and manage the system

## External Dependencies

### Python Packages
- `fastapi`: Web framework and API development
- `uvicorn`: ASGI server for FastAPI
- `sqlalchemy`: Database ORM and connection management
- `psycopg2-binary`: PostgreSQL database adapter
- `python-jose[cryptography]`: JWT token handling
- `passlib[bcrypt]`: Password hashing and verification
- `python-multipart`: Form data handling
- `jinja2`: Template rendering
- `aiofiles`: Asynchronous file operations

### Frontend Dependencies
- Font Awesome 6.4.0 (CDN): Icon library
- Google Fonts (CDN): Orbitron and Roboto fonts

## Deployment Strategy

### Environment Configuration
- Database URL configured via environment variables
- Secret key for JWT tokens (environment variable)
- Production-ready with connection pooling

### Server Setup
- Uses uvicorn ASGI server on port 5000
- Automatic dependency installation on startup
- Static file serving for CSS/JS assets
- Template directory for HTML rendering

### Database Initialization
- Automatic table creation on startup
- SQLAlchemy models define schema
- Migration-ready structure for future updates

### Security Considerations
- Environment-based secret management
- Password hashing with bcrypt
- JWT token expiration handling
- Role-based access controls
- SQL injection prevention through ORM

The application is designed for easy deployment on platforms like Replit, with automatic dependency management and database initialization.