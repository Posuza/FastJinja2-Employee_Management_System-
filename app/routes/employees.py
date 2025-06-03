from fastapi import APIRouter, Depends, Request, Form, HTTPException, status  # Properly import status here
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import app.db as db
from app.auth import get_current_user
from app.schemas import Employee, EmployeeCreate, EmployeeUpdate
from datetime import datetime, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from .env
EMPLOYEE_CODE_PREFIX = os.getenv("EMPLOYEE_CODE_PREFIX", "EMP")
EMPLOYEE_CODE_DIGITS = int(os.getenv("EMPLOYEE_CODE_DIGITS", "6"))

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def generate_employee_code():
    """Generate automatic employee code using .env configuration"""
    try:
        prefix_pattern = f"{EMPLOYEE_CODE_PREFIX}%"
        expected_length = len(EMPLOYEE_CODE_PREFIX) + EMPLOYEE_CODE_DIGITS
        prefix_length = len(EMPLOYEE_CODE_PREFIX)
        
        # Get all existing employee codes with the correct format, sorted by number
        existing_codes_query = """
        SELECT emp_code FROM Employee 
        WHERE emp_code LIKE :prefix_pattern 
        AND LENGTH(emp_code) = :expected_length
        ORDER BY CAST(SUBSTR(emp_code, :prefix_length + 1) AS INTEGER) ASC
        """
        
        existing_codes = await db.database.fetch_all(
            existing_codes_query,
            {
                "prefix_pattern": prefix_pattern,
                "expected_length": expected_length,
                "prefix_length": prefix_length
            }
        )
        
        # Extract just the numbers from existing codes
        existing_numbers = set()
        for row in existing_codes:
            code = row["emp_code"]
            if code.startswith(EMPLOYEE_CODE_PREFIX) and len(code) == expected_length:
                try:
                    number = int(code[prefix_length:])
                    existing_numbers.add(number)
                except ValueError:
                    continue
        
        # Find the first gap starting from 1
        current_number = 1
        max_number = 10 ** EMPLOYEE_CODE_DIGITS - 1
        
        while current_number <= max_number:
            if current_number not in existing_numbers:
                # Found an available number
                return f"{EMPLOYEE_CODE_PREFIX}{current_number:0{EMPLOYEE_CODE_DIGITS}d}"
            current_number += 1
        
        # If all numbers are taken (very unlikely), use timestamp fallback
        import time
        timestamp = int(time.time()) % max_number
        return f"{EMPLOYEE_CODE_PREFIX}{timestamp:0{EMPLOYEE_CODE_DIGITS}d}"
        
    except Exception as e:
        print(f"Error generating employee code: {e}")
        # Emergency fallback
        import time
        timestamp = int(time.time()) % (10 ** EMPLOYEE_CODE_DIGITS)
        return f"{EMPLOYEE_CODE_PREFIX}{timestamp:0{EMPLOYEE_CODE_DIGITS}d}"


_employee_code_cache = {"code": None, "expires": 0}

async def get_cached_employee_code():
    """Get a cached employee code or generate a new one"""
    import time
    
    current_time = time.time()
    if _employee_code_cache["code"] is None or current_time > _employee_code_cache["expires"]:
        # Cache expired or doesn't exist, generate new code
        _employee_code_cache["code"] = await generate_employee_code()
        _employee_code_cache["expires"] = current_time + 300  # Cache for 5 minutes
    
    return _employee_code_cache["code"]
# Employee routes (employee.html)
@router.get("/employees", response_class=HTMLResponse)
async def employees_page(
    request: Request, 
    message: Optional[str] = None,
    error: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Display employees page"""
    # Get employees
    query = "SELECT * FROM Employee ORDER BY created_at DESC"
    employees = await db.database.fetch_all(query=query)
    
    # Get users if current user is admin
    users = []
    if current_user["role"] == "admin":
        users_query = "SELECT * FROM User ORDER BY created_at DESC"
        users = await db.database.fetch_all(query=users_query)
    
    # Generate auto employee code
    auto_gen_employee_code = await generate_employee_code()
    
    # Change "employee.html" to "home.html" here
    return templates.TemplateResponse("home.html", {
        "request": request,
        "current_user": current_user,
        "employees": employees,
        "users": users,
        "auto_gen_employee_code": auto_gen_employee_code,
        "message": message,
        "error": error
    })

# Add the rest of your employee routes (create, update, delete) here
@router.post("/employees")
async def create_employee(
    request: Request,
    emp_code: str = Form(...),
    prefix: Optional[str] = Form(None),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    thai_id_or_passport: Optional[str] = Form(None),
    employment: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    salary: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),  # Changed from date to str
    leave_date: Optional[str] = Form(None),  # Changed from date to str
    current_user: dict = Depends(get_current_user)
):
    """Create new employee"""
    # Check if user has admin or HR role
    if current_user["role"] not in ["admin", "hr"]:
        return RedirectResponse(url="/", status_code=303)  # Use numeric code instead
    
    try:
        # Process dates properly
        start_date_value = None
        leave_date_value = None
        
        # Check if start_date is provided
        if not start_date or not start_date.strip():
            return RedirectResponse(
                url="/employees?error=Start+date+is+required",
                status_code=303
            )
        
        # Convert start_date string to date object
        try:
            start_date_value = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            return RedirectResponse(
                url="/employees?error=Invalid+start+date+format",
                status_code=303
            )
        
        # Convert leave_date string to date object if not empty
        if leave_date and leave_date.strip():
            try:
                leave_date_value = datetime.strptime(leave_date, "%Y-%m-%d").date()
            except ValueError:
                return RedirectResponse(
                    url="/employees?error=Invalid+leave+date+format",
                    status_code=303
                )
        
        # Check date logic if both are provided
        if start_date_value and leave_date_value and start_date_value > leave_date_value:
            return RedirectResponse(
                url="/employees?error=Leave+date+cannot+be+earlier+than+start+date",
                status_code=303  # Use numeric code
            )
            
        # Validate required fields
        if not first_name.strip():
            return RedirectResponse(
                url="/employees?error=First+name+is+required",
                status_code=status.HTTP_303_SEE_OTHER
            )
            
        # Validate email format if provided
        if email and "@" not in email:
            return RedirectResponse(
                url="/employees?error=Invalid+email+format",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Check if employee code exists
        existing_employee = await db.database.fetch_one(
            query="SELECT employee_id FROM Employee WHERE emp_code = :emp_code",
            values={"emp_code": emp_code.strip()}
        )
        
        if existing_employee:
            # Return to employee page with error
            return RedirectResponse(
                url=f"/employees?error=Employee+code+'{emp_code}'+already+exists",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        # Create employee record
        now = datetime.utcnow()
        
        # Fix employment value to be lowercase if provided
        employment_value = employment.lower() if employment else None
        
        # Check table structure to handle missing columns
        table_info = await db.database.fetch_all(
            "PRAGMA table_info(Employee)"
        )
        columns = [row["name"] for row in table_info]
        
        # Build SQL query based on existing columns
        insert_columns = [
            "emp_code", "prefix", "first_name", "last_name", "email", "phone", 
            "thai_id_or_passport", "employment", "status", "salary", "address",
            "start_date", "leave_date", "created_at", "updated_at"
        ]
        
        insert_values = [
            ":emp_code", ":prefix", ":first_name", ":last_name", ":email", ":phone",
            ":thai_id_or_passport", ":employment", ":status", ":salary", ":address",
            ":start_date", ":leave_date", ":created_at", ":updated_at"
        ]
        
        # Only include created_by and updated_by if they exist in the table
        if "created_by" in columns:
            insert_columns.append("created_by")
            insert_values.append(":created_by")
            
        if "updated_by" in columns:
            insert_columns.append("updated_by")
            insert_values.append(":updated_by")
        
        # Construct the dynamic query
        query = f"""
        INSERT INTO Employee (
            {', '.join(insert_columns)}
        ) VALUES (
            {', '.join(insert_values)}
        )
        """
        
        # Create base values dict
        values = {
            "emp_code": emp_code.strip(),
            "prefix": prefix,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip() if email else None,
            "phone": phone.strip() if phone else None,
            "thai_id_or_passport": thai_id_or_passport.strip() if thai_id_or_passport else None,
            "employment": employment_value,
            "status": status.lower() if status else None,  # Convert to lowercase if not None
            "salary": salary,
            "address": address.strip() if address else None,
            "start_date": start_date_value,  # Use processed date value
            "leave_date": leave_date_value,  # Use processed date value
            "created_at": now,
            "updated_at": now
        }
        
        # Add tracking columns only if they exist
        if "created_by" in columns:
            values["created_by"] = current_user["user_id"]
        if "updated_by" in columns:
            values["updated_by"] = current_user["user_id"]
        
        await db.database.execute(query=query, values=values)
        
        # Log employee creation
        await db.database.execute(
            query="INSERT INTO Log (user_id, action, details) VALUES (:user_id, :action, :details)",
            values={
                "user_id": current_user["user_id"],
                "action": "EMPLOYEE_CREATED",
                "details": f"Employee {emp_code} ({first_name} {last_name}) created"
            }
        )
        
        # Redirect back to employee page with success message
        return RedirectResponse(
            url="/employees?message=Employee+created+successfully", 
            status_code=303
        )
        
    except Exception as e:
        print(f"Create employee error: {e}")
        return RedirectResponse(
            url=f"/employees?error=Failed+to+create+employee:+{str(e)}",
            status_code=303  # Use numeric code
        )

@router.post("/employees/{employee_id}/update")
async def update_employee(
    request: Request,
    employee_id: int,
    emp_code: str = Form(...),
    prefix: Optional[str] = Form(None),
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    thai_id_or_passport: Optional[str] = Form(None),
    employment: Optional[str] = Form(None),
    status: Optional[str] = Form(None), 
    salary: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),  # Changed from date to str
    leave_date: Optional[str] = Form(None),  # Changed from date to str
    current_user: dict = Depends(get_current_user)
):
    """Update existing employee"""
    # Check if user has admin or HR role
    if current_user["role"] not in ["admin", "hr"]:
        return RedirectResponse(url="/", status_code=303)  # Use numeric code
    
    try:
        # Process dates properly
        start_date_value = None
        leave_date_value = None
        
        # Convert start_date string to date object if not empty
        if start_date and start_date.strip():
            try:
                start_date_value = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                return RedirectResponse(
                    url="/employees?error=Invalid+start+date+format",
                    status_code=303  # Use numeric code
                )
        
        # Convert leave_date string to date object if not empty
        if leave_date and leave_date.strip():
            try:
                leave_date_value = datetime.strptime(leave_date, "%Y-%m-%d").date()
            except ValueError:
                return RedirectResponse(
                    url="/employees?error=Invalid+leave+date+format",
                    status_code=303  # Use numeric code
                )
        
        # Check date logic if both are provided
        if start_date_value and leave_date_value and start_date_value > leave_date_value:
            return RedirectResponse(
                url="/employees?error=Leave+date+cannot+be+earlier+than+start+date",
                status_code=303  # Use numeric code
            )
            
        # Validate required fields
        if not first_name.strip():
            return RedirectResponse(
                url="/employees?error=First+name+is+required",
                status_code=status.HTTP_303_SEE_OTHER
            )
            
        # Validate email format if provided
        if email and "@" not in email:
            return RedirectResponse(
                url="/employees?error=Invalid+email+format",
                status_code=status.HTTP_303_SEE_OTHER
            )
            
        # Check if employee exists
        employee = await db.database.fetch_one(
            query="SELECT * FROM Employee WHERE employee_id = :employee_id",
            values={"employee_id": employee_id}
        )
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Check if employee code is unique (if changed)
        if emp_code != employee["emp_code"]:
            existing_employee = await db.database.fetch_one(
                query="SELECT employee_id FROM Employee WHERE emp_code = :emp_code AND employee_id != :employee_id",
                values={"emp_code": emp_code.strip(), "employee_id": employee_id}
            )
            
            if existing_employee:
                return RedirectResponse(
                    url=f"/employees?error=Employee+code+'{emp_code}'+already+exists",
                    status_code=status.HTTP_303_SEE_OTHER
                )
        
        # Check table structure to handle missing columns
        table_info = await db.database.fetch_all(
            "PRAGMA table_info(Employee)"
        )
        columns = [row["name"] for row in table_info]
        
        # Build SQL update values
        update_parts = [
            "emp_code = :emp_code",
            "prefix = :prefix",
            "first_name = :first_name", 
            "last_name = :last_name",
            "email = :email",
            "phone = :phone",
            "thai_id_or_passport = :thai_id_or_passport", 
            "employment = :employment",
            "status = :status",
            "salary = :salary",
            "address = :address",
            "start_date = :start_date",
            "leave_date = :leave_date",
            "updated_at = :updated_at"
        ]
        
        # Only include updated_by if it exists in the table
        if "updated_by" in columns:
            update_parts.append("updated_by = :updated_by")
        
        # Construct the dynamic query
        query = f"""
        UPDATE Employee SET
            {', '.join(update_parts)}
        WHERE employee_id = :employee_id
        """
        
        # Create values dict with processed dates
        values = {
            "employee_id": employee_id,
            "emp_code": emp_code.strip(),
            "prefix": prefix,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip() if email else None,
            "phone": phone.strip() if phone else None,
            "thai_id_or_passport": thai_id_or_passport.strip() if thai_id_or_passport else None,
            "employment": employment.lower() if employment else None,
            "status": status.lower() if status else None,
            "salary": salary,
            "address": address.strip() if address else None,
            "start_date": start_date_value,  # Use processed date value
            "leave_date": leave_date_value,  # Use processed date value
            "updated_at": datetime.utcnow()
        }
        
        # Add tracking column only if it exists
        if "updated_by" in columns:
            values["updated_by"] = current_user["user_id"]
        
        await db.database.execute(query=query, values=values)
        
        # Log employee update
        await db.database.execute(
            query="INSERT INTO Log (user_id, action, details) VALUES (:user_id, :action, :details)",
            values={
                "user_id": current_user["user_id"],
                "action": "EMPLOYEE_UPDATED",
                "details": f"Employee {emp_code} ({first_name} {last_name}) updated"
            }
        )
        
        # Redirect back to employee page with success message
        return RedirectResponse(
            url="/employees?message=Employee+updated+successfully",
            status_code=303  # Use numeric code
        )
        
    except Exception as e:
        print(f"Update employee error: {e}")
        return RedirectResponse(
            url=f"/employees?error=Failed+to+update+employee:+{str(e)}",
            status_code=303  # Use numeric code
        )

@router.post("/employees/{employee_id}/delete")
async def delete_employee(
    request: Request,
    employee_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete existing employee"""
    # Check if user has admin role (only admin can delete)
    if current_user["role"] != "admin":
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    try:
        # Check if employee exists
        employee = await db.database.fetch_one(
            query="SELECT * FROM Employee WHERE employee_id = :employee_id",
            values={"employee_id": employee_id}
        )
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Delete employee record
        await db.database.execute(
            query="DELETE FROM Employee WHERE employee_id = :employee_id",
            values={"employee_id": employee_id}
        )
        
        # Log employee deletion
        await db.database.execute(
            query="INSERT INTO Log (user_id, action, details) VALUES (:user_id, :action, :details)",
            values={
                "user_id": current_user["user_id"],
                "action": "EMPLOYEE_DELETED",
                "details": f"Employee {employee['emp_code']} ({employee['first_name']} {employee['last_name']}) deleted"
            }
        )
        
        # Redirect back to employee page with success message
        return RedirectResponse(
            url="/employees?message=Employee+deleted+successfully",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Delete employee error: {e}")
        return RedirectResponse(
            url=f"/employees?error=Failed+to+delete+employee:+{str(e)}",
            status_code=status.HTTP_303_SEE_OTHER
        )

