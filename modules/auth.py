"""
Authentication functions for the Layla Conversation Analyzer
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def load_auth_config():
    """Load authentication configuration from config.yaml"""
    with open('config.yaml') as file:
        return yaml.load(file, Loader=SafeLoader)

def create_authenticator(config):
    """Create authenticator object with enhanced security"""
    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

def handle_authentication(authenticator):
    """Handle authentication process and return authentication status"""
    try:
        authenticator.login()
    except Exception as e:
        st.error(f"Authentication error: {e}")
        st.stop()
    
    # Check authentication status
    if st.session_state.get('authentication_status') is False:
        st.error('❌ Username/password is incorrect')
        st.info('💡 **Hint**: Check your credentials and try again')
        return False
    elif st.session_state.get('authentication_status') is None:
        show_welcome_page()
        return False
    
    return True

def show_welcome_page():
    """Show welcome page for unauthenticated users"""
    st.warning('🔐 Please enter your username and password to continue')
    
    # Enhanced welcome message
    st.title("Layla Conversation Analyzer")
    st.markdown("""
    ### Welcome to the Layla Conversation Analyzer Dashboard
    
    This secure dashboard provides comprehensive analytics for beauty AI chat conversations.
    
    **🎯 Features include:**
    - 📊 **Analytics Dashboard**: Key metrics, conversation trends, and insights
    - 💬 **Chat Explorer**: Browse and search individual conversations with translation
    - 🔍 **Keyword Search**: Search across all messages with advanced filtering
    
    **🚀 Demo Accounts:**
    ```
    Username: admin    | Password: admin123  | Role: admin (full access)
    Username: user     | Password: user123   | Role: user (standard access)  
    Username: demo     | Password: demo123   | Role: user (read-only access)
    Username: layla    | Password: r7ZM1y58  | Role: user (standard access)
    ```
    
    Please login above to access the dashboard.
    """)

def show_authentication_ui():
    """Show authentication UI for unauthenticated users"""
    show_welcome_page()

def show_user_info(authenticator):
    """Show user role and logout button"""
    st.title("Layla Conversation Analyzer")
    
    # Simple horizontal layout for role and logout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display user role
        user_roles = st.session_state.get("roles", ["user"])
        if "admin" in user_roles:
            st.markdown("🔑 **Role:** `Admin`")
        else:
            st.markdown("👤 **Role:** `User`")
    
    with col2:
        # Logout button
        authenticator.logout('🚪 Logout', 'main')
