import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
from deep_translator import GoogleTranslator
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import ssl
import urllib.request

# Load data from cloud storage URL
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
            import urllib.request
            
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

# Load data
def load_data():
    df = pd.read_csv('layla_export_2025-07-07.csv', header=None, names=[
        'thread_id', 'timestamp', 'role', 'message', 'region', 'extra'
    ], usecols=range(5))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def is_arabic(text):
    # Simple check for Arabic characters
    return bool(re.search(r'[\u0600-\u06FF]', str(text)))

def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception:
        return "[Translation failed]"

def main():
    st.set_page_config(page_title="Layla Conversation Analyzer", layout="wide")
    
    # Load authentication config
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Create authenticator object with enhanced security
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    # Authentication widget with enhanced error handling
    try:
        authenticator.login()
    except Exception as e:
        st.error(f"Authentication error: {e}")
        st.stop()
    
    # Check authentication status with enhanced messages
    if st.session_state.get('authentication_status') is False:
        st.error('❌ Username/password is incorrect')
        st.info('💡 **Hint**: Check your credentials and try again')
        return
    elif st.session_state.get('authentication_status') is None:
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
        Username: user1    | Password: user123   | Role: user (standard access)  
        Username: demo     | Password: demo123   | Role: user (read-only access)
        ```
        
        Please login above to access the dashboard.
        """)
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
        authenticator.logout('🚪 Logout', 'main')

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
            try:
                df = pd.read_csv(uploaded_file, 
                               header=None, 
                               names=['thread_id', 'timestamp', 'role', 'message', 'region', 'extra'],
                               usecols=range(5))
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                st.success(f"✅ Successfully loaded {len(df)} conversation records from uploaded file!")
            except Exception as e:
                st.error(f"❌ Error reading CSV file: {e}")
                st.info("💡 Please ensure your CSV has the correct format: thread_id, timestamp, role, message, region")
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
            st.metric("Date Range", f"{df['timestamp'].dt.date.min()} to {df['timestamp'].dt.date.max()}")

    # Filter by launch date (July 2, 2025) to latest
    min_date = pd.to_datetime('2025-07-04')
    max_date = df['timestamp'].max().normalize()
    df = df[df['timestamp'] >= min_date]

    tab2, tab1, tab3 = st.tabs(["Analytics Dashboard", "Chat Explorer", "Keyword Search"])

    with tab1:
        st.header("Chat Explorer")
        # Sidebar filters
        col1, col2, col3 = st.columns(3)
        with col1:
            date_filter = st.date_input(
                "Date (range)",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date()
            )
        with col2:
            region_filter = st.selectbox("Region", options=["All"] + sorted(df['region'].unique().tolist()))
        with col3:
            time_filter = st.text_input("Time (HH:MM, optional)")

        # Apply filters
        filtered_df = df.copy()
        filtered_df = filtered_df[(filtered_df['timestamp'].dt.date >= date_filter[0]) & (filtered_df['timestamp'].dt.date <= date_filter[1])]
        if region_filter != "All":
            filtered_df = filtered_df[filtered_df['region'] == region_filter]
        if time_filter:
            filtered_df = filtered_df[filtered_df['timestamp'].dt.strftime('%H:%M').str.contains(time_filter)]

        chats = filtered_df.groupby('thread_id').first().reset_index()
        search_term = st.text_input("Search in conversations (user/assistant/message)")
        if search_term:
            mask = chats.apply(lambda row: search_term.lower() in str(row['thread_id']).lower() or search_term.lower() in str(row['region']).lower() or search_term.lower() in str(row['message']).lower(), axis=1)
            chats = chats[mask]
        chat_options = chats['thread_id'] + ' | ' + chats['timestamp'].dt.strftime('%Y-%m-%d %H:%M') + ' | ' + chats['region']
        selected_chat = st.selectbox("Select a conversation:", chat_options if not chat_options.empty else ["No conversations found"])
        if selected_chat != "No conversations found":
            thread_id = selected_chat.split(' | ')[0]
            thread_df = df[df['thread_id'] == thread_id]
            for _, row in thread_df.iterrows():
                msg = row['message']
                if is_arabic(msg):
                    if st.button(f"Translate (EN) {row['timestamp']}", key=f"trans_{row['timestamp']}"):
                        translation = translate_text(msg)
                        st.markdown(f"**{row['role'].capitalize()}** ({row['timestamp']}): {msg}")
                        st.markdown(f"<span style='color:green'><b>EN:</b> {translation}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{row['role'].capitalize()}** ({row['timestamp']}): {msg}")
                else:
                    st.markdown(f"**{row['role'].capitalize()}** ({row['timestamp']}): {msg}")
        else:
            st.info("No conversations match the selected filters.")

    with tab3:
        st.header("🔍 Keyword Search Across All Conversations")
        
        # Search interface
        col1, col2 = st.columns([3, 1])
        with col1:
            search_keyword = st.text_input("Enter keyword(s) to search across all messages:", 
                                         placeholder="e.g., error, booking, payment, help")
        with col2:
            case_sensitive = st.checkbox("Case sensitive", value=False)
        
        col3, col4, col5 = st.columns(3)
        with col3:
            role_filter = st.selectbox("Filter by sender:", ["All", "user", "assistant"])
        with col4:
            region_search_filter = st.selectbox("Filter by region:", ["All"] + sorted(df['region'].unique().tolist()))
        with col5:
            min_results = st.number_input("Max results:", min_value=10, max_value=1000, value=100, step=10)
        
        if search_keyword:
            # Prepare search dataframe
            search_df = df.copy()
            
            # Apply sender filter
            if role_filter != "All":
                search_df = search_df[search_df['role'] == role_filter]
            
            # Apply region filter
            if region_search_filter != "All":
                search_df = search_df[search_df['region'] == region_search_filter]
            
            # Perform search
            if case_sensitive:
                mask = search_df['message'].str.contains(search_keyword, na=False)
            else:
                mask = search_df['message'].str.contains(search_keyword, case=False, na=False)
            
            results = search_df[mask].copy()
            
            if len(results) > 0:
                st.success(f"Found **{len(results)}** messages containing '{search_keyword}'")
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Matches", len(results))
                with col2:
                    st.metric("Unique Conversations", results['thread_id'].nunique())
                with col3:
                    user_matches = len(results[results['role'] == 'user'])
                    st.metric("User Messages", user_matches)
                with col4:
                    assistant_matches = len(results[results['role'] == 'assistant'])
                    st.metric("Assistant Messages", assistant_matches)
                
                # Limit results for display
                if len(results) > min_results:
                    results_display = results.head(min_results)
                    st.warning(f"Showing first {min_results} results out of {len(results)} total matches")
                else:
                    results_display = results
                
                # Sort by timestamp (most recent first)
                results_display = results_display.sort_values('timestamp', ascending=False)
                
                # Display results with highlighting
                st.subheader("Search Results")
                
                # Add download button for results
                csv_results = results[['thread_id', 'timestamp', 'role', 'message', 'region']].copy()
                csv_results['timestamp'] = csv_results['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                csv_string = csv_results.to_csv(index=False)
                st.download_button(
                    label="📥 Download search results as CSV",
                    data=csv_string,
                    file_name=f"keyword_search_{search_keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Group by conversation for better organization
                if st.checkbox("Group by conversation", value=True):
                    for thread_id in results_display['thread_id'].unique():
                        thread_results = results_display[results_display['thread_id'] == thread_id]
                        thread_info = thread_results.iloc[0]
                        
                        with st.expander(f"💬 Conversation {thread_id} | {thread_info['region']} | {len(thread_results)} matches"):
                            for _, row in thread_results.iterrows():
                                # Highlight the search term in the message
                                message = row['message']
                                if case_sensitive:
                                    highlighted_message = message.replace(search_keyword, f"**🔍{search_keyword}**")
                                else:
                                    # Case-insensitive highlighting
                                    pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
                                    highlighted_message = pattern.sub(f"**🔍{search_keyword}**", message)
                                
                                # Display message with metadata
                                role_color = "#1f77b4" if row['role'] == 'user' else "#ff7f0e"
                                st.markdown(f"""
                                <div style='border-left: 4px solid {role_color}; padding-left: 12px; margin: 8px 0;'>
                                    <small style='color: #666;'>{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | <b>{row['role'].upper()}</b></small><br>
                                    {highlighted_message}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Add translation button for Arabic messages
                                if is_arabic(row['message']):
                                    if st.button(f"Translate", key=f"search_trans_{row.name}"):
                                        translation = translate_text(row['message'])
                                        st.markdown(f"<span style='color:green; font-style:italic;'><b>Translation:</b> {translation}</span>", unsafe_allow_html=True)
                else:
                    # Display as list without grouping
                    for _, row in results_display.iterrows():
                        # Highlight the search term in the message
                        message = row['message']
                        if case_sensitive:
                            highlighted_message = message.replace(search_keyword, f"**🔍{search_keyword}**")
                        else:
                            # Case-insensitive highlighting
                            pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
                            highlighted_message = pattern.sub(f"**🔍{search_keyword}**", message)
                        
                        # Display message with metadata
                        role_color = "#1f77b4" if row['role'] == 'user' else "#ff7f0e"
                        st.markdown(f"""
                        <div style='border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 4px solid {role_color};'>
                            <div style='display: flex; justify-content: between; align-items: center; margin-bottom: 8px;'>
                                <small style='color: #666;'><b>Conversation:</b> {row['thread_id']} | <b>Time:</b> {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | <b>Sender:</b> {row['role'].upper()} | <b>Region:</b> {row['region']}</small>
                            </div>
                            <div>{highlighted_message}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add translation button for Arabic messages
                        if is_arabic(row['message']):
                            if st.button(f"Translate", key=f"search_trans_list_{row.name}"):
                                translation = translate_text(row['message'])
                                st.markdown(f"<span style='color:green; font-style:italic;'><b>Translation:</b> {translation}</span>", unsafe_allow_html=True)
                
                # Word frequency analysis of search results
                st.subheader("📊 Word Analysis in Search Results")
                all_text = ' '.join(results['message'].astype(str))
                words = re.findall(r'\b\w+\b', all_text.lower())
                word_freq = pd.Series(words).value_counts().head(20)
                
                if not word_freq.empty:
                    fig_words = px.bar(
                        x=word_freq.values,
                        y=word_freq.index,
                        orientation='h',
                        title='Top 20 Most Frequent Words in Search Results',
                        labels={'x': 'Frequency', 'y': 'Words'}
                    )
                    fig_words.update_layout(height=600)
                    st.plotly_chart(fig_words, use_container_width=True)
                    
                # Timeline of search results
                if len(results) > 1:
                    st.subheader("📅 Timeline of Search Results")
                    timeline_data = results.groupby(results['timestamp'].dt.date).size().reset_index(name='count')
                    fig_timeline = px.line(
                        timeline_data, 
                        x='timestamp', 
                        y='count',
                        title=f"Daily frequency of '{search_keyword}' mentions",
                        labels={'timestamp': 'Date', 'count': 'Number of mentions'}
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
            else:
                st.warning(f"No messages found containing '{search_keyword}' with the selected filters.")
                st.info("💡 **Tips for better search results:**\n- Try different keywords or synonyms\n- Check if case sensitivity is affecting your search\n- Remove sender or region filters to broaden the search\n- Use partial words (e.g., 'book' to find 'booking', 'booked', etc.)")
        else:
            st.info("Enter a keyword above to search across all messages in all conversations.")

    with tab2:
        st.header("Analytics Dashboard")

        # --- Metrics Section ---
        # Calculate metrics first
        total_conversations = df['thread_id'].nunique()
        total_messages = len(df)
        user_messages = len(df[df['role'] == 'user'])
        assistant_messages = len(df[df['role'] == 'assistant'])
        arabic_messages = df['message'].apply(is_arabic).sum()
        english_messages = (~df['message'].apply(is_arabic)).sum()
        conv_lengths = df.groupby('thread_id').size()
        conv_gt6 = (conv_lengths > 6).sum()
        conv_le2 = (conv_lengths <= 2).sum()
        long_user_prompts = df[(df['role'] == 'user') & (df['message'].str.split().str.len() > 30)]
        empty_assistant = df[(df['role'] == 'assistant') & (df['message'].str.strip() == '')]
        error_msgs = df['message'].str.contains('error|failed|exception|problem|issue', case=False, na=False).sum()
        happy_msgs = df['message'].str.contains('thank|great|awesome|perfect|amazing|love|happy|helpful|👍', case=False, na=False).sum()
        frustrated_msgs = df['message'].str.contains('not working|bad|hate|angry|frustrated|annoy|useless|waste|problem|issue|disappoint|😡|😠|👎', case=False, na=False).sum()
        avg_len = conv_lengths.mean()
        median_len = conv_lengths.median()

        st.markdown("""
        <style>
        .metric-box {
            background: #f0f2f6;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            min-width: 180px;
            margin-bottom: 1rem;
            border: 1px solid #e0e0e0;
        }
        .metric-title {
            font-size: 1rem;
            color: #444;
            margin-bottom: 0.2rem;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: bold;
            color: #1a4a7a;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.subheader(":bar_chart: Key Metrics")
        paired_metrics = [
            ("Total Conversations", total_conversations, "Total Messages", total_messages),
            ("User Messages", user_messages, "Assistant Replies", assistant_messages),
            ("Arabic Messages", arabic_messages, "English Messages", english_messages),
            (">6 Message Conversations", conv_gt6, "≤2 Message Conversations", conv_le2),
            ("Empty Assistant Responses", len(empty_assistant), "Error Messages", error_msgs),
            ("Happy User Messages", happy_msgs, "Frustrated User Messages", frustrated_msgs),
            ("Average Messages/Chat", f"{avg_len:.2f}", "Median Messages/Chat", f"{median_len:.0f}"),
        ]
        metric_cols = st.columns(2)
        for left_label, left_val, right_label, right_val in paired_metrics:
            with metric_cols[0]:
                st.markdown(f"<div class='metric-box'><div class='metric-title'>{left_label}</div><div class='metric-value'>{left_val}</div></div>", unsafe_allow_html=True)
            with metric_cols[1]:
                st.markdown(f"<div class='metric-box'><div class='metric-title'>{right_label}</div><div class='metric-value'>{right_val}</div></div>", unsafe_allow_html=True)
        # Additional: Long user prompts
        st.markdown(f"<div class='metric-box'><div class='metric-title'>Long User Prompts (&gt;30 words)</div><div class='metric-value'>{len(long_user_prompts)}</div></div>", unsafe_allow_html=True)

        # --- Conversation Length Section ---
        st.subheader("Conversation Length Analysis")
        st.markdown(f"**Average Messages per Conversation:** <span style='color:#2e7be6;font-size:1.3rem'><b>{avg_len:.2f}</b></span>", unsafe_allow_html=True)
        st.markdown(f"**Median Messages per Conversation:** <span style='color:#2e7be6;font-size:1.3rem'><b>{median_len:.0f}</b></span>", unsafe_allow_html=True)
        fig_hist = px.histogram(conv_lengths, nbins=20, title='Distribution of Conversation Lengths', labels={'value':'Messages per Conversation'})
        st.plotly_chart(fig_hist, use_container_width=True)
        st.markdown("""
        <div style='margin-top:1.5rem;'></div>
        <div style='display:flex;gap:2rem;'>
            <div style='flex:1;'>
                <b>Longest Conversations</b>
                <div style='margin-bottom:0.5rem;'></div>
        """, unsafe_allow_html=True)
        st.dataframe(conv_lengths.sort_values(ascending=False).head(5).reset_index().rename(columns={0:'Messages'}), use_container_width=True)
        st.markdown("""
            </div>
            <div style='flex:1;'>
                <b>Shortest Conversations</b>
                <div style='margin-bottom:0.5rem;'></div>
        """, unsafe_allow_html=True)
        st.dataframe(conv_lengths.sort_values().head(5).reset_index().rename(columns={0:'Messages'}), use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        # Chats per day
        chats_per_day = df.groupby(df['timestamp'].dt.date)['thread_id'].nunique().reset_index()
        fig1 = px.bar(chats_per_day, x='timestamp', y='thread_id', labels={'timestamp':'Date', 'thread_id':'Conversations'}, title='New Conversations per Day')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Messages per day
        msgs_per_day = df.groupby(df['timestamp'].dt.date).size().reset_index(name='messages')
        fig_msgs = px.line(msgs_per_day, x='timestamp', y='messages', title='Messages Sent per Day')
        st.plotly_chart(fig_msgs, use_container_width=True)

        # Region distribution
        region_counts = df.groupby('region')['thread_id'].nunique().reset_index()
        fig2 = px.pie(region_counts, names='region', values='thread_id', title='Conversations by Region')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("**Conversations by Region (Table):**")
        st.dataframe(region_counts.rename(columns={'thread_id': 'Conversations'}), use_container_width=True)

        # Shortest conversations
        st.subheader("Longest Conversations")
        st.dataframe(conv_lengths.sort_values(ascending=False).head(10).reset_index().rename(columns={0:'Messages'}))

if __name__ == "__main__":
    main()
