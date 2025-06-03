import databases
import sqlalchemy
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./employee_management.db")
DATABASE_URL_ASYNC = DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///')

# Create database instance (async)
database = databases.Database(DATABASE_URL_ASYNC)

# Create SQLAlchemy engine for table creation (sync)
engine = create_engine(DATABASE_URL)

# Database tables metadata
metadata = sqlalchemy.MetaData()

# User table
users_table = sqlalchemy.Table(
    "User",
    metadata,
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("username", sqlalchemy.String(50), unique=True, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String(100), unique=True, nullable=False),
    sqlalchemy.Column("password_hash", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("role", sqlalchemy.String(20), default="user"),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, nullable=False),
)

# Employee table
employees_table = sqlalchemy.Table(
    "Employee",
    metadata,
    sqlalchemy.Column("employee_id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("emp_code", sqlalchemy.String(20), unique=True, nullable=False),
    sqlalchemy.Column("prefix", sqlalchemy.String(10)),
    sqlalchemy.Column("first_name", sqlalchemy.String(50), nullable=False),
    sqlalchemy.Column("last_name", sqlalchemy.String(50), nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String(100)),
    sqlalchemy.Column("phone", sqlalchemy.String(20)),  # Changed to String
    sqlalchemy.Column("thai_id_or_passport", sqlalchemy.String(20)),
    sqlalchemy.Column("employment", sqlalchemy.String(50)),
    sqlalchemy.Column("status", sqlalchemy.String(20)),
    sqlalchemy.Column("salary", sqlalchemy.Float),
    sqlalchemy.Column("address", sqlalchemy.Text),
    sqlalchemy.Column("start_date", sqlalchemy.Date),
    sqlalchemy.Column("leave_date", sqlalchemy.Date),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column("updated_at", sqlalchemy.DateTime, nullable=False),
)

# Log table
logs_table = sqlalchemy.Table(
    "Log",
    metadata,
    sqlalchemy.Column("log_id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("User.user_id")),
    sqlalchemy.Column("action", sqlalchemy.String(50), nullable=False),
    sqlalchemy.Column("details", sqlalchemy.Text),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime, nullable=False, server_default=sqlalchemy.func.now()),
)

# Connect to database
async def connect_db():
    """Connect to the database and ensure tables exist"""
    if not database.is_connected:
        await database.connect()
        print("Database connected successfully")
    
    # After connecting, check if tables exist and create them if needed
    try:
        # Try to query the User table - if it fails, tables likely don't exist
        await database.fetch_one("SELECT 1 FROM User LIMIT 1")
        print("Database tables already exist")
    except Exception as e:
        if "no such table" in str(e).lower():
            print("Tables don't exist. Creating now...")
            # Create tables synchronously
            create_tables()
            print("Tables created successfully")
            
            # Create default admin user
            await create_default_admin()

async def create_default_admin():
    """Create a default admin user if none exists"""
    try:
        # Check if any admin user exists
        admin_count = await database.fetch_val(
            "SELECT COUNT(*) FROM User WHERE role = 'admin'"
        )
        
        if not admin_count:
            from app.auth import get_password_hash
            from datetime import datetime
            
            now = datetime.utcnow()
            await database.execute(
                """
                INSERT INTO User (username, email, password_hash, role, created_at, updated_at)
                VALUES (:username, :email, :password_hash, :role, :created_at, :updated_at)
                """,
                {
                    "username": "admin",
                    "email": "admin@example.com",
                    "password_hash": get_password_hash("admin123"),  # Change in production
                    "role": "admin",
                    "created_at": now,
                    "updated_at": now
                }
            )
            print("Created default admin user (username: admin, password: admin123)")
    except Exception as e:
        print(f"Warning: Could not create admin user: {str(e)}")

def create_tables():
    """Create all tables defined in metadata"""
    try:
        metadata.create_all(engine)
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        raise

# Disconnect from database
async def disconnect_db():
    """Disconnect from the database"""
    if database.is_connected:
        await database.disconnect()
        print("Database disconnected")