import streamlit as st
import pandas as pd
from datetime import datetime

# Import custom modules
from modules.auth import (
    load_auth_config,
    create_authenticator,
    handle_authentication,
    show_authentication_ui,
)
from modules.data_loader import load_data_from_url, load_data_from_upload
from modules.utils import is_arabic, translate_text
from modules.chat_explorer import show_chat_explorer
from modules.search import show_keyword_search
from modules.analytics import show_analytics_dashboard
from modules.latency import show_latency_dashboard
from modules.intelligence import show_intelligence_chat


def main():
    st.set_page_config(page_title="Layla Conversation Analyzer", layout="wide")
    
    # Handle authentication
    config = load_auth_config()
    authenticator = create_authenticator(config)
    
    # Check authentication status
    if not handle_authentication(authenticator):
        show_authentication_ui()
        return
    
    # If authenticated, show the main app with simple top bar
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
        authenticator.logout("🚪 Logout", "main")

    # Data source selection
    st.divider()
    st.subheader("📊 Data Source")
    
    data_source = st.radio(
        "Choose your data source:",
        ["Use Cloud Database", "Upload CSV File"],
        horizontal=True,
        help="Select whether to use the pre-configured cloud database or upload your own CSV file"
    )
    
    df = None
    
    if data_source == "Use Cloud Database":
        # Create a placeholder for loading message
        loading_placeholder = st.empty()
        loading_placeholder.info("🔄 Loading conversation data from cloud database...")
        
        df = load_data_from_url()
        
        if df is None:
            loading_placeholder.empty()  # Clear loading message
            st.error("❌ Failed to load conversation data from cloud database.")
            st.stop()
        
        loading_placeholder.empty()  # Clear loading message
        st.success(f"✅ Successfully loaded {len(df)} conversation records from cloud database!")
        
    else:  # Upload CSV File
        st.info("📁 Please upload your conversation data CSV file")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload a CSV file with columns: thread_id, timestamp, role, message, region",
        )
        
        if uploaded_file is not None:
            df = load_data_from_upload(uploaded_file)
            if df is not None:
                st.success(f"✅ Successfully loaded {len(df)} conversation records from uploaded file!")
            else:
                st.stop()
        else:
            st.warning("⚠️ Please upload a CSV file to continue.")
            st.stop()
    
    # Display data info
    if df is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Unique Conversations", df['thread_id'].nunique())
        with col3:
            # Format dates as "Jul 2 - Jul 29" to save space (chronological order)
            # Calculate from original data before any filtering
            original_min_date = df['timestamp'].min()
            original_max_date = df['timestamp'].max()
            min_date_str = original_min_date.strftime('%b %d')
            max_date_str = original_max_date.strftime('%b %d')
            st.metric("Date Range", f"{min_date_str} - {max_date_str}")

    # Filter by launch date (July 1, 2025) to latest
    min_date = pd.to_datetime('2025-07-01')
    max_date = df['timestamp'].max().normalize()
    df = df[df['timestamp'] >= min_date]

    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Analytics Dashboard",
            "Chat Explorer",
            "Keyword Search",
            "Response Latency",
            "Intelligence",
        ]
    )

    with tab1:
        show_analytics_dashboard(df)

    with tab2:
        show_chat_explorer(df)

    with tab3:
        show_keyword_search(df)

    with tab4:
        show_latency_dashboard(df)

    with tab5:
        show_intelligence_chat(df)


if __name__ == "__main__":
    main()
