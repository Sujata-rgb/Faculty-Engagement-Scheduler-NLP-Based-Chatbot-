#  Teacher Timetable Hub

A comprehensive web-based platform for teachers to manage timetables, interact with AI-powered chatbot, and access smart schedule lookup features.

![Django](https://img.shields.io/badge/Django-5.2.5-green)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)
![Groq](https://img.shields.io/badge/Groq-AI-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple)

---

##  Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [API Integration](#api-integration)
- [License](#license)

---

##  Overview

**Teacher Timetable Hub** ek modern web application hai jo teachers ko apne timetable ko efficiently manage karne mein help karta hai. Yeh project AI-powered chatbot, automated PDF parsing, aur smart schedule management features provide karta hai.

### Key Highlights:
-  **Automated PDF Parsing** - Upload PDF, system automatically extracts data
-  **AI Chatbot** - Natural language queries with Groq LLM integration (accurate PDF-based responses)
- **Smart Schedule Lookup** - Day-wise instant schedule access with filtering
- **Smart Notification Center** - Next class alerts, weekly summary, free slots, tomorrow's preview
- **Department Timetables** - Organized by branch/department and semester
- **Admin Dashboard** - Complete management system with analytics
- **Modern UI** - Professional dark theme with responsive design

---

##  Features

###  User Authentication
- Secure registration and login system
- Login type selection (User/Admin) with dropdown
- Password hashing and validation
- Session management
- Role-based access control (User/Admin)
- Profile management

###  PDF Timetable Upload
- Upload timetable PDF files
- Automatic data extraction using pdfplumber
- Smart parsing of teacher names, time slots, subjects, and rooms
- Structured data storage in database

###  AI-Powered Chatbot
- Natural language query processing
- Groq LLM API integration (llama-3.1-8b-instant model)
- **Accurate PDF-based responses** - Uses complete timetable data
- Context-aware responses with date/time awareness
- Multi-language support (English + Hindi)
- Smart filtering for day-specific queries (today, tomorrow, yesterday)
- Real-time timetable data integration

**Supported Queries:**
- "What are my classes today?"
- "When is my next class?"
- "Show me free slots"
- "Monday ki classes kya hain?"
- "Aaj kitni classes hain?"

###  Schedule Lookup
- Day-wise timetable view with dropdown selection
- Quick schedule access
- Filter by specific days (Monday-Saturday)
- Complete schedule with time, subject, and room details
- Empty state handling
- Responsive card-based layout

###  Smart Notification Center
- **Next Class Alert** - Upcoming class with countdown timer
- **Today's Overview** - Complete schedule for current day
- **Tomorrow's Preview** - Preview of next day's classes
- **Free Slots** - Available time gaps for meetings/breaks
- **Weekly Summary** - Total classes and day-wise breakdown
- **AI Query Shortcuts** - Quick action buttons for common queries

###  Admin Dashboard
- Teacher management (View, Add, Activate/Deactivate, Delete)
- Timetable oversight
- Statistics and analytics
- Interactive charts (Chart.js)
- Upload tracking
- Recent activity monitoring
- **Department Timetable Upload** - Upload timetables for specific departments and semesters

###  Department Timetables Module
- Organized by Department/Branch
- Semester-wise organization
- PDF upload and management
- View and download timetables
- Breadcrumb navigation
- User-friendly access for students/teachers

---

##  Technologies Used

### Backend
- **Django 4.2.25** - Web framework
- **Python 3.x** - Programming language
- **SQLite3** - Database
- **pdfplumber** - PDF processing
- **Groq** - AI/LLM integration
- **python-dotenv** - Environment variables

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling 
- **JavaScript** - Interactivity
- **Chart.js** - Data visualization
- **Google Fonts (Poppins)** - Typography

### Key Libraries
```python
Django==4.2.25
pdfplumber          # PDF text extraction
groq                # LLM API client
python-dotenv       # Environment management
```

---

##  Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd LLM_CHATBOT
```

### Step 2: Create Virtual Environment
```bash
python -m venv myenv

# Windows
myenv\Scripts\activate

# Linux/Mac
source myenv/bin/activate
```

### Step 3: Install Dependencies
```bash
cd chatbot
pip install django pdfplumber groq python-dotenv
```

### Step 4: Environment Setup
Create a `.env` file in the `chatbot` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Step 5: Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### Step 7: Run Server
```bash
python manage.py runserver
```

Server will start at `http://127.0.0.1:8000/`

---

##  Usage

### For Teachers

#### 1. Registration
- Visit the welcome page
- Click "Register"
- Fill in username, email, and password
- Login with credentials

#### 2. Upload Timetable
- Go to Dashboard → "Upload Timetable"
- Select your timetable PDF
- Click "Upload"
- System will automatically parse and store data

#### 3. Use AI Chatbot
- Navigate to "AI Assistant"
- Type your query in natural language
- Get instant AI-powered responses

**Example Queries:**
```
"What are my classes today?"
"When is my next class?"
"Show me free slots for Monday"
"Kitni classes hain aaj?"
```

#### 4. Schedule Lookup
- Go to "Schedule Lookup"
- Select a day from dropdown
- View complete schedule for that day

#### 5. Notifications
- Check "Smart Notification Center"
- See next class alerts
- View today's and tomorrow's schedule
- Identify free time slots

### For Administrators

#### 1. Admin Login
- Login with admin credentials
- Access Admin Dashboard

#### 2. Manage Teachers
- View all registered teachers
- Add new teachers manually
- Activate/Deactivate teachers
- View teacher statistics

#### 3. Timetable Management
- View all uploaded timetables
- Upload timetables for teachers
- Monitor upload activity

#### 4. Analytics
- View teacher status charts
- See total teachers, active/inactive counts
- Monitor recent uploads

---

##  Project Structure

```
LLM_CHATBOT/
├── chatbot/                    # Django Project Root
│   ├── app/                    # Main Django Application
│   │   ├── models.py           # Database models (User, TimetableEntry, etc.)
│   │   ├── views.py            # Business logic & view functions
│   │   ├── forms.py            # Django forms
│   │   ├── admin.py            # Admin panel configuration
│   │   ├── templates/          # HTML Templates (18 files)
│   │   │   ├── welcome.html           # Landing page
│   │   │   ├── login.html             # User/Admin login
│   │   │   ├── register.html          # User registration
│   │   │   ├── dashboard.html         # Main user dashboard
│   │   │   ├── assistant.html         # AI Chatbot interface
│   │   │   ├── schedule_lookup.html   # Day-wise schedule viewer
│   │   │   ├── profile.html           # User profile
│   │   │   ├── notifications.html     # Smart notification center
│   │   │   ├── upload.html            # Timetable upload
│   │   │   ├── departments.html       # Department list
│   │   │   ├── semesters.html         # Semester list
│   │   │   ├── timetable_pdfs.html    # PDF timetables
│   │   │   ├── admin_dashboard.html   # Admin control panel
│   │   │   ├── admin_teachers.html    # Teacher management
│   │   │   ├── admin_add_teacher.html # Add teacher form
│   │   │   ├── admin_timetables.html  # Timetable management
│   │   │   ├── admin_upload_timetable.html # Admin upload
│   │   │   └── admin_upload_department_timetable.html # Dept upload
│   │   ├── migrations/         # Database migrations
│   │   └── __pycache__/        # Python cache (auto-generated)
│   ├── chatbot/                # Django Project Settings
│   │   ├── settings.py         # Django configuration
│   │   ├── urls.py             # URL routing (20+ endpoints)
│   │   ├── wsgi.py             # WSGI deployment config
│   │   ├── asgi.py             # ASGI deployment config
│   │   └── __init__.py         # Python package marker
│   ├── media/                  # User uploaded files
│   │   ├── timetables/         # Personal timetable PDFs
│   │   └── department_timetables/ # Department timetable PDFs
│   ├── db.sqlite3              # SQLite database file
│   └── manage.py               # Django management CLI
├── .env                        # Environment variables (API keys)
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── populate_departments.py     # Database setup script (optional)
└── README.md                   # Project documentation
```

---

##  Screenshots

### Welcome Page
- Modern hero section with "TEACHER PORTAL" badge
- Feature highlights
- Login/Register buttons

### Dashboard
- Welcome message
- Statistics cards (Total slots, Teaching days)
- Feature modules (Smart Center, AI Assistant, Schedule Lookup, Profile)

### AI Chatbot
- Natural language input
- Context-aware responses
- Real-time timetable integration

### Admin Dashboard
- Summary cards with statistics
- Interactive charts
- Teacher management interface

---

##  API Integration

### Groq API
The project uses Groq API for AI-powered chatbot responses.

**Setup:**
1. Get API key from [Groq Console](https://console.groq.com/)
2. Add to `.env` file:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

**Usage:**
```python
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
```

---

##  Database Models

### User (Django Built-in)
- `username` - Unique username
- `email` - Email address
- `password` - Hashed password
- `is_staff` - Admin access flag
- `is_superuser` - Superuser flag

### TeacherProfile
- `user` - OneToOne relationship with User
- `contact` - Contact information
- `department` - Department name
- `is_active` - Active status
- `total_queries` - Query count
- `last_active` - Last activity timestamp

### TimetableUpload
- `uploader` - ForeignKey to User
- `uploaded_file` - PDF file
- `uploaded_at` - Upload timestamp

### TimetableEntry
- `upload` - ForeignKey to TimetableUpload
- `teacher_name` - Teacher name
- `day` - Day abbreviation (Mo, Tu, We, Th, Fr, Sa)
- `start_time` - Class start time
- `end_time` - Class end time
- `subject` - Subject name
- `room` - Room number

### Department (New)
- `name` - Department/Branch name (unique)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Semester (New)
- `department` - ForeignKey to Department
- `number` - Semester number (1-8)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### TimetablePDF (New)
- `semester` - ForeignKey to Semester
- `title` - Timetable title/description
- `pdf_file` - PDF file (uploaded to department_timetables/)
- `uploaded_by` - ForeignKey to User (nullable)
- `uploaded_at` - Upload timestamp
- `updated_at` - Last update timestamp

---

##  Security Features

- **Password Hashing** - Django's built-in password hashing
- **CSRF Protection** - Cross-site request forgery protection
- **Session Management** - Secure session handling
- **Authentication** - Login required for protected routes
- **Authorization** - Role-based access control
- **Input Validation** - Form and data validation
- **SQL Injection Prevention** - Django ORM protection

---

##  URL Routes

### Public Routes
- `/` - Welcome page
- `/register/` - User registration
- `/login/` - User login

### Protected Routes (Login Required)
- `/dashboard/` - Main user dashboard
- `/upload/` - Upload personal timetable
- `/assistant/` - AI chatbot interface
- `/schedule/` - Schedule lookup with day filtering
- `/profile/` - User profile management
- `/notifications/` - Smart Notification Center
- `/departments/` - Department list (CSE, AI&DS, etc.)
- `/departments/<id>/` - Semester list for department
- `/departments/<dept_id>/<semester_id>/` - Timetable PDFs for semester

### Admin Routes (Staff Only)
- `/admin-dashboard/` - Admin control panel with analytics
- `/admin/teachers/` - Teacher management (CRUD operations)
- `/admin/teachers/add/` - Add new teacher form
- `/admin/teachers/<id>/toggle/` - Toggle teacher active/inactive status
- `/admin/teachers/<id>/delete/` - Delete teacher account
- `/admin/timetables/` - View all uploaded timetables
- `/admin/timetables/upload/` - Admin timetable upload
- `/admin/departments/upload/` - Upload department timetables
- `/admin/chart-data/` - Analytics API endpoint (JSON)

### AJAX API Endpoints
- `/api/get-semesters/` - Get semesters for selected department (JSON)

---

##  Key Workflows

### PDF Upload & Parsing
```
1. User uploads PDF
2. pdfplumber extracts text
3. Regex patterns parse data
4. Teacher names, times, subjects extracted
5. Data cleaned and validated
6. TimetableEntry objects created
7. Stored in database
```

### AI Chatbot Query
```
1. User submits query
2. System analyzes query type
3. Filters relevant timetable entries
4. Builds context string
5. Sends to Groq API
6. Receives AI response
7. Displays formatted answer
```

### Schedule Lookup
```
1. User selects day
2. System queries database
3. Filters entries by day and teacher
4. Organizes by time
5. Displays complete schedule
```

---

##  Troubleshooting

### Common Issues

**1. PDF not parsing correctly**
- Ensure PDF has proper table structure
- Check if teacher names are clearly visible
- Verify time format in PDF

**2. AI Chatbot not responding**
- Check Groq API key in `.env` file
- Verify internet connection
- Check API quota/limits

**3. Database errors**
- Run migrations: `python manage.py migrate`
- Check database file permissions
- Verify model relationships

**4. Static files not loading**
- Check `STATIC_URL` in settings.py
- Verify file paths

---

##  Development Notes

### Adding New Features
1. Create model in `models.py`
2. Run migrations
3. Create view in `views.py`
4. Add URL route in `urls.py`
5. Create template in `templates/`

### Code Style
- Follow PEP 8 Python style guide
- Use meaningful variable names
- Add comments for complex logic
- Keep functions modular

---

##  License

This project is open source and available for educational purposes.

---

##  Author

Developed as a full-stack web application project.

---

##  Support

For issues or questions:
- Check the documentation
- Review code comments
- Check Django and library documentation

---

##  Learning Resources

### Django
- [Django Documentation](https://docs.djangoproject.com/)
- [Django Tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/)

### PDF Processing
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)

### AI/LLM
- [Groq API Documentation](https://console.groq.com/docs)

### Frontend
- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)

---

##  Future Enhancements

- [ ] Mobile responsive improvements
- [ ] Email notifications for class reminders
- [ ] Calendar integration (Google Calendar sync)
- [ ] Advanced analytics dashboard
- [ ] Export timetables to PDF/Excel
- [ ] Real-time notifications
- [ ] Multi-language support (Hindi/English)
- [ ] Voice commands for AI chatbot
- [ ] Dark/Light theme toggle
- [ ] Bulk timetable operations

---

##  Project Statistics

- **Total Lines of Code:** 2800+ (optimized)
- **Templates:** 18 HTML files (active)
- **Models:** 6 database models
- **Views:** 18 view functions
- **URL Routes:** 19 endpoints
- **Features:** 8 major modules
- **Dependencies:** 5 core packages

---

##  Features Checklist

- [x] User Authentication (User/Admin login selection)
- [x] PDF Upload & Parsing (pdfplumber integration)
- [x] AI Chatbot Integration (Groq LLM with accurate responses)
- [x] Schedule Lookup (day-wise filtering)
- [x] Smart Notification Center (Next class, Weekly, Free slots, Tomorrow)
- [x] Admin Dashboard (with charts and analytics)
- [x] Teacher Management (Complete CRUD operations)
- [x] Statistics & Analytics (Chart.js integration)
- [x] Department Timetables Module (Branch/Semester organization)
- [x] Responsive Design (Bootstrap 5)
- [x] Profile Management
- [x] Code Optimization (Clean, maintainable codebase)

---

**Made with  using Django, Python, and Modern Web Technologies**

---

