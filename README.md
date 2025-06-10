# Employee Management System

A modern web application built with FastAPI for managing employee information, user authentication, and HR operations.

## 🚀 Features

- **👥 Employee Management**
  - Create, read, update, and delete employee records
  - Track employee details (personal info, employment status, salary)
  - Automatic employee code generation
  - Document employee status changes

- **🔐 User Authentication & Authorization**
  - Secure login and registration
  - Role-based access control (Admin, HR, Regular users)
  - Profile management

- **💼 HR Operations**
  - Employee status tracking
  - Employment type management
  - Salary information handling

- **🎨 Modern UI/UX**
  - Responsive design with Tailwind CSS
  - Interactive web interface
  - Mobile-friendly layout
 
  ## 📸 Screenshots

<div align="center">
  <img src="https://raw.githubusercontent.com/Posuza/FastJinja2-Employee_Management_System-/main/project_image/image1.png" alt="main Screen" width="45%">
  <img src="https://raw.githubusercontent.com/Posuza/FastJinja2-Employee_Management_System-/main/screenshots/dashboard.png" alt="Dashboard" width="45%">
</div>

<div align="center">
  <img src="https://raw.githubusercontent.com/Posuza/FastJinja2-Employee_Management_System-/main/screenshots/employee-list.png" alt="Employee List" width="45%">
  <img src="https://raw.githubusercontent.com/Posuza/FastJinja2-Employee_Management_System-/main/screenshots/employee-add.png" alt="Add Employee Form" width="45%">
</div>


## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Database**: SQLite (with async support)
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Authentication**: JWT-based auth
- **Template Engine**: Jinja2

## 📋 Prerequisites

- Python 3.7+
- pip (Python package manager)
- Virtual environment (recommended)
- Docker (optional for containerized deployment)

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
    https://github.com/Posuza/FastJinja2-Employee_Management_System-.git
   cd employee-management-system
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the root directory with the following content:
   ```env
   # JWT Configuration
   SECRET_KEY=your_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # Employee Code Configuration
   EMPLOYEE_CODE_PREFIX=EMP
   EMPLOYEE_CODE_DIGITS=6
   ```

## 🚀 Running the Application Locally

1. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the application:**
   - Web Interface: [http://localhost:8000](http://localhost:8000)
   - API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🐳 Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t employee-management-system .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 8000:8000 --name employee-system employee-management-system
   ```

3. **Access the application:**
   - Web Interface: [http://localhost:8000](http://localhost:8000)
   - API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

4. **View container logs:**
   ```bash
   docker logs employee-system
   ```

5. **Stop the container:**
   ```bash
   docker stop employee-system
   ```

## 📁 Project Structure

```
demo/
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── db.py            # Database configuration and models
│   ├── auth.py          # Authentication functions
│   ├── schemas.py       # Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py      # Authentication routes
│   │   ├── employees.py # Employee management routes
│   │   ├── profile.py   # User profile routes
│   │   └── users.py     # User management routes
│   ├── templates/       # Jinja2 HTML templates
│   │   ├── index.html   # Base template with navigation
│   │   ├── home.html    # Employee listing page
│   │   ├── login.html
│   │   ├── profile.html
│   │   └── register.html
│   └── statics/         # Static assets
│       ├── styles.css
│       └── images/
├── myEnv/               # Virtual environment (not in repo)
├── requirements.txt     # Project dependencies
├── .env                 # Environment variables (not in repo)
├── Dockerfile           # Docker configuration
└── README.md            # Project documentation
```

## 🔑 API Endpoints

| Method   | Endpoint                | Description           | Access         |
|----------|-------------------------|-----------------------|---------------|
| GET      | /                       | Home page             | All           |
| GET/POST | /login                  | User login            | Public        |
| GET/POST | /register               | User registration     | Public        |
| GET      | /employees              | List employees        | Authenticated |
| POST     | /employees              | Create employee       | Admin/HR      |
| POST     | /employees/{id}/update  | Update employee       | Admin/HR      |
| POST     | /employees/{id}/delete  | Delete employee       | Admin         |
| GET      | /profile                | User profile          | Authenticated |
| POST     | /profile/update         | Update profile        | Authenticated |

## 👥 User Roles

- **Admin:** Full system access including user management and employee deletion
- **HR:** Employee management access (create, read, update)
- **User:** Basic view access to employee information

## 🔒 Security Features

- Password hashing with bcrypt
- JWT authentication with expiration
- Role-based access control
- Form validation (client and server-side)
- CORS middleware
- Input sanitization

## 📋 Employee Form Fields

- `emp_code`: Employee code (auto-generated)
- `prefix`: Name prefix (Mr., Ms., etc.)
- `first_name`: First name (required)
- `last_name`: Last name
- `email`: Email address
- `phone`: Phone number
- `thai_id_or_passport`: National ID or passport number
- `employment`: Employment type (Full-time, Part-time, Contract, Intern)
- `status`: Personal status (Single, Married, Divorced)
- `salary`: Salary amount
- `address`: Physical address
- `start_date`: Employment start date (required)
- `leave_date`: Employment end date (optional)

## 📦 Implementation Details

### Database Schema

The application uses two main tables:

**User Table:**
- user_id (PK)
- username (unique)
- email (unique)
- hashed_password
- role (admin, hr, user)
- created_at
- updated_at

**Employee Table:**
- employee_id (PK)
- emp_code (unique)
- prefix
- first_name
- last_name
- email (unique, nullable)
- phone (nullable)
- thai_id_or_passport (nullable)
- employment (nullable)
- status (nullable)
- salary (nullable)
- address (nullable)
- start_date (nullable)
- leave_date (nullable)
- created_at
- updated_at

### Key Functions
- **Authentication:** JWT token generation and validation
- **Password Handling:** Bcrypt hashing for secure password storage
- **Employee Code Generation:** Automatic sequential code generation with configurable prefix
- **Date Handling:** Proper parsing and validation of date fields

## 🛠️ Troubleshooting

**Common Issues:**

- **Database Connection Errors:**
  - Ensure SQLite database file has correct permissions
  - Check the database path in `db.py`
- **Date Handling Issues:**
  - Dates should be in `YYYY-MM-DD` format
  - Start date must be before leave date
- **Template Not Found Error:**
  - Verify template file exists in `templates`
  - Check for typos in template names
- **JWT Authentication Issues:**
  - Verify `SECRET_KEY` is set in `.env` file
  - Check token expiration settings
- **Docker Issues:**
  - Ensure Docker daemon is running
  - Check for port conflicts with `docker ps`
  - Inspect logs with `docker logs employee-system`

## 📦 Requirements

```
fastapi==0.104.1
uvicorn==0.23.2
python-multipart==0.0.6
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.0.1
jinja2==3.1.2
python-dotenv==1.0.0
databases==0.8.0
aiosqlite==0.19.0
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please open an issue in the GitHub repository or contact the development team.

# Fast API Project

## Overview
This is a FastAPI application with custom error handling middleware.

## Features
- Custom 404 error handler
- Custom 500 error handler
- Template-based error responses

## Project Structure
```
fast1/
├── app/
│   ├── middleware.py - Custom error handling middleware
│   └── templates/
│       └── error.html - Error template
├── main.py - Application entry point
└── README.md - This file
```

## Setup and Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `uvicorn main:app --reload`

## Development
This project uses FastAPI framework with Jinja2 templates for rendering error pages.
