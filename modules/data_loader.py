"""
Data loading functions for the Layla Conversation Analyzer
"""
import streamlit as st
import pandas as pd
import ssl
import urllib.request

def load_data_from_url():
    """Load conversation data from the cloud storage URL"""
    try:
        # Get the conversations URL from secrets
        conversations_url = st.secrets["connections"]["supabase"]["CONVERSATIONS_URL"]
        
        # Create SSL context that doesn't verify certificates (for signed URLs)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # For HTTPS URLs, use urllib to handle SSL context properly
        if conversations_url.startswith('https'):
            # Create a custom opener with the SSL context
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
            urllib.request.install_opener(opener)
        
        # Load CSV from URL (urllib opener handles SSL)
        df = pd.read_csv(conversations_url, 
                        header=None, 
                        names=['thread_id', 'timestamp', 'role', 'message', 'region', 'extra'],
                        usecols=range(5))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"❌ Error loading data from URL: {e}")
        st.info("💡 Please check your cloud storage configuration")
        return None

def load_data_from_csv(file_path):
    """Load data from local CSV file"""
    df = pd.read_csv(file_path, header=None, names=[
        'thread_id', 'timestamp', 'role', 'message', 'region', 'extra'
    ], usecols=range(5))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def load_data_from_upload(uploaded_file):
    """Load data from uploaded CSV file"""
    try:
        df = pd.read_csv(uploaded_file, 
                       header=None, 
                       names=['thread_id', 'timestamp', 'role', 'message', 'region', 'extra'],
                       usecols=range(5))
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"❌ Error reading CSV file: {e}")
        st.info("💡 Please ensure your CSV has the correct format: thread_id, timestamp, role, message, region")
        return None

def show_data_source_selection():
    """Show data source selection interface and return loaded dataframe"""
    st.subheader("📊 Data Source")
    
    data_source = st.radio(
        "Choose your data source:",
        ["Use Cloud Database", "Upload CSV File"],
        horizontal=True,
        help="Select whether to use the pre-configured cloud database or upload your own CSV file"
    )
    
    df = None
    
    if data_source == "Use Cloud Database":
        st.info("🔄 Loading conversation data from cloud database...")
        df = load_data_from_url()
        
        if df is None:
            st.error("❌ Failed to load conversation data from cloud database.")
            st.stop()
        
        st.success(f"✅ Successfully loaded {len(df)} conversation records from cloud database!")
        
    else:  # Upload CSV File
        st.info("📁 Please upload your conversation data CSV file")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload a CSV file with columns: thread_id, timestamp, role, message, region"
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
    
    return df

def show_data_info(df):
    """Display data information metrics"""
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
