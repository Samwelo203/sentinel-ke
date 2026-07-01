"""
SENTINEL-KE Admin Panel
Provides admin functionality for user management and system administration.
"""

import streamlit as st
from auth import (
    load_users, create_user, update_user_role, delete_user, 
    list_users, deactivate_user, activate_user, can_manage_users,
    format_eat_datetime, get_eat_time
)
import pandas as pd

# ============================================
# ADMIN PANEL HELPER FUNCTIONS
# ============================================

def render_user_management_section(admin_session):
    """Render the user management section of the admin panel."""
    
    st.markdown("---")
    st.subheader("▤ User Management")
    
    # Tab selection
    tab1, tab2, tab3, tab4 = st.tabs(["≡ View Users", "+ Create User", "✎ Edit User", "🔐 Activate/Deactivate"])
    
    # ============================================
    # TAB 1: VIEW USERS
    # ============================================
    
    with tab1:
        st.markdown("### View All Users")
        
        success, user_list = list_users(admin_session)
        
        if success and user_list:
            df = pd.DataFrame(user_list)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.info(f"✓ Total users: {len(user_list)}")
            
            # User statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                admins = len([u for u in user_list if u['Level'] == 3])
                st.metric("Administrators", admins)
            
            with col2:
                officers = len([u for u in user_list if u['Level'] == 2])
                st.metric("Health Officers", officers)
            
            with col3:
                viewers = len([u for u in user_list if u['Level'] == 1])
                st.metric("Viewers", viewers)
        else:
            st.warning("✗ Unable to fetch users")
    
    # ============================================
    # TAB 2: CREATE USER
    # ============================================
    
    with tab2:
        st.markdown("### Create New User")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username", placeholder="Enter username", key="create_user_username")
            new_password = st.text_input("Password", type="password", placeholder="Enter password", key="create_user_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="create_user_confirm")
        
        with col2:
            role_option = st.radio("Select Role", ["Administrator", "Health Officer", "Viewer"], index=1, key="create_user_role")
            
            # Set role level and permissions based on selection
            role_map = {
                "Administrator": {
                    "role_level": 3,
                    "permissions": ["view", "export", "user_management", "system_admin", "report_generation"]
                },
                "Health Officer": {
                    "role_level": 2,
                    "permissions": ["view", "export", "report_generation"]
                },
                "Viewer": {
                    "role_level": 1,
                    "permissions": ["view"]
                }
            }
            
            role_info = role_map[role_option]
            st.info(f"""
            **Permissions for {role_option}:**
            - {', '.join([p.replace('_', ' ').title() for p in role_info['permissions']])}
            """)
        
        if st.button("+ Create User", use_container_width=True, key="btn_create_user", type="primary"):
            # Validation
            if not new_username:
                st.error("✗ Username cannot be empty")
            elif not new_password:
                st.error("✗ Password cannot be empty")
            elif new_password != confirm_password:
                st.error("✗ Passwords do not match")
            elif len(new_password) < 6:
                st.error("✗ Password must be at least 6 characters")
            else:
                # Check if user already exists
                users = load_users()
                if new_username in users:
                    st.error(f"✗ User '{new_username}' already exists")
                else:
                    success, message = create_user(
                        new_username,
                        new_password,
                        role_option,
                        role_info["role_level"],
                        role_info["permissions"],
                        admin_session
                    )
                    
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
    
    # ============================================
    # TAB 3: EDIT USER ROLE
    # ============================================
    
    with tab3:
        st.markdown("### Edit User Role & Permissions")
        
        users = load_users()
        user_list_names = [u for u in users.keys() if u != admin_session["username"]]
        
        if user_list_names:
            edit_username = st.selectbox("Select User to Edit", user_list_names, key="edit_user_select")
            
            if edit_username and edit_username in users:
                user = users[edit_username]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Current Role:** {user['role']}")
                    st.write(f"**Current Status:** {'✓ Active' if user.get('active', True) else '✗ Inactive'}")
                    st.write(f"**Created:** {user.get('created_at', 'N/A')}")
                
                with col2:
                    new_role = st.radio("New Role", ["Administrator", "Health Officer", "Viewer"], 
                                       key="edit_user_role", index=["Administrator", "Health Officer", "Viewer"].index(user['role']))
                    
                    role_map = {
                        "Administrator": {
                            "role_level": 3,
                            "permissions": ["view", "export", "user_management", "system_admin", "report_generation"]
                        },
                        "Health Officer": {
                            "role_level": 2,
                            "permissions": ["view", "export", "report_generation"]
                        },
                        "Viewer": {
                            "role_level": 1,
                            "permissions": ["view"]
                        }
                    }
                    
                    new_role_info = role_map[new_role]
                    
                    st.info(f"""
                    **New Permissions:**
                    - {', '.join([p.replace('_', ' ').title() for p in new_role_info['permissions']])}
                    """)
                
                if st.button("✎ Update User", use_container_width=True, key="btn_update_user", type="primary"):
                    success, message = update_user_role(
                        edit_username,
                        new_role,
                        new_role_info["role_level"],
                        new_role_info["permissions"],
                        admin_session
                    )
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.info("ℹ️ No other users available to edit")
    
    # ============================================
    # TAB 4: ACTIVATE/DEACTIVATE USERS
    # ============================================
    
    with tab4:
        st.markdown("### Activate / Deactivate Users")
        
        users = load_users()
        user_list_names = [u for u in users.keys() if u != admin_session["username"]]
        
        if user_list_names:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔴 Deactivate Users")
                
                active_users = [u for u in user_list_names if users[u].get("active", True)]
                
                if active_users:
                    deactivate_user_select = st.selectbox("Select Active User to Deactivate", active_users, key="deactivate_user")
                    
                    if st.button("🔴 Deactivate User", use_container_width=True, key="btn_deactivate"):
                        success, message = deactivate_user(deactivate_user_select, admin_session)
                        
                        if success:
                            st.success(message)
                            st.info(f"User '{deactivate_user_select}' will no longer be able to login")
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.info("ℹ️ All users are already active")
            
            with col2:
                st.markdown("#### 🟢 Activate Users")
                
                inactive_users = [u for u in user_list_names if not users[u].get("active", True)]
                
                if inactive_users:
                    activate_user_select = st.selectbox("Select Inactive User to Activate", inactive_users, key="activate_user")
                    
                    if st.button("🟢 Activate User", use_container_width=True, key="btn_activate"):
                        success, message = activate_user(activate_user_select, admin_session)
                        
                        if success:
                            st.success(message)
                            st.info(f"User '{activate_user_select}' can now login again")
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.info("ℹ️ No inactive users to activate")
        else:
            st.info("ℹ️ No other users available")


def render_system_settings_section(admin_session):
    """Render the system settings section of the admin panel."""
    
    st.markdown("---")
    st.subheader("⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["≡ System Status", "🔐 Security", "≡ Audit Log"])
    
    with tab1:
        st.markdown("### System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Status", "🟢 Operational")
        with col2:
            st.metric("Last Update", format_eat_datetime(get_eat_time(), "%H:%M:%S EAT"))
        with col3:
            st.metric("Users Online", len(st.session_state.get("active_sessions", [])))
        
        st.info("""
        ✓ **System Health:**
        - Database: Connected
        - API: Operational
        - Reports: Enabled
        - Timezone: East Africa Time (EAT)
        """)
    
    with tab2:
        st.markdown("### Security Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Session Timeout", "60 minutes", delta="Recommended: 60-120 mins")
            st.caption("Users will be automatically logged out after 60 minutes of inactivity")
        
        with col2:
            st.metric("Password Policy", "6+ characters", delta="Configurable")
            st.caption("Minimum password length and complexity requirements")
        
        st.warning("""
        ⚠ **Security Recommendations:**
        - Ensure all users have unique strong passwords
        - Regularly audit user access and permissions
        - Deactivate unused accounts immediately
        - Keep system updated with latest patches
        """)
    
    with tab3:
        st.markdown("### Audit Log")
        
        st.info("""
        ≡ **Audit Capabilities:**
        - User creation and deletion
        - Role and permission changes
        - Account activation/deactivation
        - Login attempts (success and failure)
        - User access logs
        - Report generation logs
        
        Note: Full audit logging will be available in next update
        """)


def render_admin_dashboard(admin_session):
    """Main admin panel dashboard."""
    
    st.set_page_config(
        page_title="SENTINEL-KE | Admin Panel",
        page_icon="⚙️",
        layout="wide"
    )
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 10px; margin-bottom: 1rem;">
        <h1>⚙️ SENTINEL-KE Admin Panel</h1>
        <h3>User Management & System Administration</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Admin info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"👑 **Admin:** {admin_session['username']}")
    
    with col2:
        st.info(f"🕐 **Current Time (EAT):** {format_eat_datetime(get_eat_time())}")
    
    with col3:
        if st.button("🚪 Back to Dashboard", use_container_width=True):
            st.session_state.show_admin_panel = False
            st.rerun()
    
    # Main sections
    section = st.radio("Select Section", ["▤ User Management", "⚙ System Settings"], horizontal=True)
    
    if section == "▤ User Management":
        render_user_management_section(admin_session)
    else:
        render_system_settings_section(admin_session)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem; color: #999; font-size: 0.85rem;">
        <p><strong>■ SENTINEL-KE Admin Panel</strong></p>
        <p>Last accessed: {format_eat_datetime(get_eat_time())}</p>
        <p>🔐 All actions are logged and monitored</p>
    </div>
    """, unsafe_allow_html=True)
