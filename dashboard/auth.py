"""
SENTINEL-KE Authentication Module
Implements role-based access control with session management and password hashing.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
import pytz

# ============================================
# TIMEZONE CONFIGURATION
# ============================================

# East Africa Time (EAT) timezone
EAT = pytz.timezone('Africa/Nairobi')

def get_eat_time() -> datetime:
    """Get current time in East Africa Time (EAT)."""
    return datetime.now(EAT)

def format_eat_datetime(dt: datetime = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime in EAT timezone."""
    if dt is None:
        dt = get_eat_time()
    elif isinstance(dt, str):
        # If it's a string in ISO format, parse it
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return dt
    
    # Convert to EAT if not already
    if dt.tzinfo is None:
        dt = EAT.localize(dt)
    else:
        dt = dt.astimezone(EAT)
    
    return dt.strftime(format_str)

# ============================================
# USER DATABASE & CONFIGURATION
# ============================================

# Default user credentials (SHA-256 hashed)
# In production, these MUST be updated immediately
DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin".encode()).hexdigest(),
        "role": "Administrator",
        "role_level": 3,
        "permissions": ["view", "export", "user_management", "system_admin"],
        "active": True,
        "created_at": format_eat_datetime(get_eat_time())
    },
    "health_officer": {
        "password_hash": hashlib.sha256("password".encode()).hexdigest(),
        "role": "Health Officer",
        "role_level": 2,
        "permissions": ["view", "export", "report_generation"],
        "active": True,
        "created_at": format_eat_datetime(get_eat_time())
    },
    "viewer": {
        "password_hash": hashlib.sha256("viewer".encode()).hexdigest(),
        "role": "Viewer",
        "role_level": 1,
        "permissions": ["view"],
        "active": True,
        "created_at": format_eat_datetime(get_eat_time())
    }
}

# Session configuration
SESSION_TIMEOUT_MINUTES = 60
USERS_DB_PATH = "users.json"

# ============================================
# UTILITY FUNCTIONS
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == password_hash

def load_users() -> Dict:
    """Load users from database file or return default users."""
    if os.path.exists(USERS_DB_PATH):
        try:
            with open(USERS_DB_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return DEFAULT_USERS.copy()
    return DEFAULT_USERS.copy()

def save_users(users: Dict) -> bool:
    """Save users to database file."""
    try:
        with open(USERS_DB_PATH, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False

def hash_update_password(username: str, new_password: str) -> bool:
    """Update a user's password (admin only in future)."""
    users = load_users()
    if username in users:
        users[username]["password_hash"] = hash_password(new_password)
        users[username]["updated_at"] = format_eat_datetime(get_eat_time())
        return save_users(users)
    return False

# ============================================
# AUTHENTICATION FUNCTIONS
# ============================================

def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Authenticate a user and return their role information.
    Returns: (success, user_info, message)
    """
    users = load_users()
    
    if username not in users:
        return False, None, "❌ Invalid username or password"
    
    user = users[username]
    
    if not verify_password(password, user["password_hash"]):
        return False, None, "✗ Invalid username or password"
    
    # Check if user is active
    if not user.get("active", True):
        return False, None, "✗ Account is deactivated. Contact administrator."
    
    return True, user, "✅ Login successful"

def create_session(username: str, user_info: Dict) -> Dict:
    """Create a new session for an authenticated user."""
    now = get_eat_time()
    return {
        "username": username,
        "role": user_info["role"],
        "role_level": user_info["role_level"],
        "permissions": user_info["permissions"],
        "login_time": now,
        "last_activity": now,
        "authenticated": True
    }

def is_session_valid(session: Optional[Dict]) -> bool:
    """Check if a session is still valid (not expired)."""
    if not session or not session.get("authenticated"):
        return False
    
    last_activity = session.get("last_activity")
    if not last_activity:
        return False
    
    timeout = get_eat_time() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    return last_activity > timeout

def update_session_activity(session: Dict) -> Dict:
    """Update the last activity timestamp of a session."""
    if session:
        session["last_activity"] = get_eat_time()
    return session

def get_session_time_remaining(session: Dict) -> int:
    """Get remaining session time in minutes."""
    if not session:
        return 0
    
    last_activity = session.get("last_activity")
    if not last_activity:
        return 0
    
    elapsed = (get_eat_time() - last_activity).total_seconds() / 60
    remaining = SESSION_TIMEOUT_MINUTES - elapsed
    return max(0, int(remaining))

def has_permission(session: Dict, permission: str) -> bool:
    """Check if a session has a specific permission."""
    if not is_session_valid(session):
        return False
    
    return permission in session.get("permissions", [])

# ============================================
# ROLE-BASED RENDERING
# ============================================

def get_role_badge(role_level: int, role_name: str) -> str:
    """Get a visual badge for the user's role."""
    badges = {
        3: "👑",
        2: "📊",
        1: "👁️"
    }
    return f"{badges.get(role_level, '🔒')} {role_name}"

def can_export_data(session: Dict) -> bool:
    """Check if user can export data."""
    return has_permission(session, "export")

def can_generate_reports(session: Dict) -> bool:
    """Check if user can generate reports."""
    return has_permission(session, "report_generation")

def can_manage_users(session: Dict) -> bool:
    """Check if user can manage users (admin only)."""
    return has_permission(session, "user_management")

def can_access_system_admin(session: Dict) -> bool:
    """Check if user can access system admin panel."""
    return has_permission(session, "system_admin")

# ============================================
# USER MANAGEMENT (ADMIN ONLY)
# ============================================

def create_user(username: str, password: str, role: str, role_level: int, 
                permissions: list, admin_session: Dict) -> Tuple[bool, str]:
    """Create a new user (admin only)."""
    if not can_manage_users(admin_session):
        return False, "✗ Unauthorized: Only administrators can create users"
    
    users = load_users()
    
    if username in users:
        return False, f"✗ User '{username}' already exists"
    
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "role_level": role_level,
        "permissions": permissions,
        "active": True,
        "created_at": format_eat_datetime(get_eat_time()),
        "created_by": admin_session["username"]
    }
    
    if save_users(users):
        return True, f"✓ User '{username}' created successfully"
    return False, "✗ Error saving user to database"

def update_user_role(username: str, new_role: str, new_role_level: int, 
                     new_permissions: list, admin_session: Dict) -> Tuple[bool, str]:
    """Update a user's role and permissions (admin only)."""
    if not can_manage_users(admin_session):
        return False, "✗ Unauthorized: Only administrators can update users"
    
    users = load_users()
    
    if username not in users:
        return False, f"✗ User '{username}' not found"
    
    users[username]["role"] = new_role
    users[username]["role_level"] = new_role_level
    users[username]["permissions"] = new_permissions
    users[username]["updated_at"] = format_eat_datetime(get_eat_time())
    users[username]["updated_by"] = admin_session["username"]
    
    if save_users(users):
        return True, f"✓ User '{username}' updated successfully"
    return False, "✗ Error updating user in database"

def delete_user(username: str, admin_session: Dict) -> Tuple[bool, str]:
    """Delete a user (admin only)."""
    if not can_manage_users(admin_session):
        return False, "✗ Unauthorized: Only administrators can delete users"
    
    if username == admin_session["username"]:
        return False, "✗ Cannot delete your own account"
    
    users = load_users()
    
    if username not in users:
        return False, f"✗ User '{username}' not found"
    
    del users[username]
    
    if save_users(users):
        return True, f"✓ User '{username}' deleted successfully"
    return False, "✗ Error deleting user from database"

def list_users(admin_session: Dict) -> Tuple[bool, list]:
    """List all users (admin only)."""
    if not can_manage_users(admin_session):
        return False, []
    
    users = load_users()
    user_list = []
    
    for username, user_info in users.items():
        user_list.append({
            "Username": username,
            "Role": user_info["role"],
            "Level": user_info["role_level"],
            "Status": "✓ Active" if user_info.get("active", True) else "✗ Inactive",
            "Permissions": ", ".join(user_info["permissions"]),
            "Created": user_info.get("created_at", "N/A")[:10]
        })
    
    return True, user_list


def deactivate_user(username: str, admin_session: Dict) -> Tuple[bool, str]:
    """Deactivate a user account (admin only)."""
    if not can_manage_users(admin_session):
        return False, "✗ Unauthorized: Only administrators can deactivate users"
    
    if username == admin_session["username"]:
        return False, "✗ Cannot deactivate your own account"
    
    users = load_users()
    
    if username not in users:
        return False, f"❌ User '{username}' not found"
    
    users[username]["active"] = False
    users[username]["deactivated_at"] = format_eat_datetime(get_eat_time())
    users[username]["deactivated_by"] = admin_session["username"]
    
    if save_users(users):
        return True, f"✓ User '{username}' has been deactivated"
    return False, "✗ Error deactivating user"

def activate_user(username: str, admin_session: Dict) -> Tuple[bool, str]:
    """Activate a deactivated user account (admin only)."""
    if not can_manage_users(admin_session):
        return False, "✗ Unauthorized: Only administrators can activate users"
    
    users = load_users()
    
    if username not in users:
        return False, f"✗ User '{username}' not found"
    
    users[username]["active"] = True
    users[username]["reactivated_at"] = format_eat_datetime(get_eat_time())
    users[username]["reactivated_by"] = admin_session["username"]
    
    if save_users(users):
        return True, f"✓ User '{username}' has been activated"
    return False, "✗ Error activating user"


def get_role_badge(role_level: int, role_name: str) -> str:
    """Return icon badge for role display."""
    badges = {
        3: f"★ {role_name}",
        2: f"◆ {role_name}",
        1: f"● {role_name}"
    }
    return badges.get(role_level, f"◯ {role_name}")
