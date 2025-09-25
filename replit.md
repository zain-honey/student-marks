# Student Marks Management System

## Overview
A Flask-based web application for managing student marks and records. Features separate admin and student portals with role-based authentication, mark management, and data export capabilities.

## Architecture
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development fallback)
- **Frontend**: HTML templates with Jinja2, CSS styling, and vanilla JavaScript
- **Authentication**: Session-based with password hashing
- **File Uploads**: Image upload support for student photos

## Key Features
- **Admin Portal**: Add/remove students, manage subjects, input marks, export data to CSV
- **Student Portal**: View personal marks, change password, calculate percentage
- **Role-based Authentication**: Separate login flows for admin and students
- **Data Management**: CRUD operations for students, subjects, and marks
- **File Management**: Image upload and storage for student photos

## Project Structure
```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/
│   ├── style.css         # Main stylesheet
│   ├── script.js         # Frontend JavaScript
│   └── uploads/          # Directory for uploaded images
├── templates/
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login form
│   ├── admin.html        # Admin dashboard
│   ├── student.html      # Student dashboard
│   └── components/       # Reusable components
└── .gitignore           # Git ignore rules

```

## Database Models
- **Admin**: Admin user accounts with hashed passwords
- **Student**: Student records with personal info and credentials
- **Subject**: Academic subjects for mark tracking
- **Mark**: Student marks for specific subjects

## Environment Configuration
- `SECRET_KEY`: Flask session encryption key
- `DATABASE_URL`: PostgreSQL connection string (auto-configured in Replit)
- `ADMIN_USER`: Default admin username (default: "admin")
- `ADMIN_PASS`: Default admin password (default: "admin123")

## Default Credentials
- **Admin**: username = "admin", password = "admin123"
- **Students**: Created by admin with custom passwords

## Recent Changes
- **2024-09-25**: Successfully imported from GitHub and configured for Replit environment
  - Installed Python 3.11 and all dependencies
  - Configured PostgreSQL database integration
  - Set up Flask workflow on port 5000
  - Added placeholder image for homepage
  - Configured deployment with gunicorn for production
  - Verified all functionality working correctly

## Deployment
- **Development**: `python app.py` (Flask dev server)
- **Production**: `gunicorn --bind=0.0.0.0:5000 --reuse-port app:app`
- **Target**: Autoscale deployment for stateless web application