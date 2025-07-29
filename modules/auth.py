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
        return False
    
    return True

def show_welcome_page():
    """Show welcome page for unauthenticated users"""
    st.warning('🔐 Please enter your username and password to continue')
    
    # Enhanced welcome message
    # st.title("Layla Conversation Analyzer")
    st.markdown("""
    ### Welcome to the Layla Conversation Analyzer Dashboard
    
    ### 🔑 **Need Access?**
    If you need access to this dashboard, please reach out to anyone from the **Corporate Innovation team**.
    
    ### Issues or Bugs?
    If you're experiencing any issues or come across bugs, please contact: **Adam Ahsan** - adam.ahsan@chalhoub.com
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
