"""
Analytics functions for the Layla Conversation Analyzer
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from .utils import is_arabic

def show_analytics_dashboard(df):
    """Display the complete analytics dashboard"""
    st.header("Analytics Dashboard")

    # Date range selector for analytics
    st.subheader("📅 Date Range Filter")
    
    # Define the full range (July 1, 2025 to latest date in database)
    full_range_min = pd.to_datetime('2025-07-01').date()
    full_range_max = df['timestamp'].max().date()
    
    analytics_date_filter = st.date_input(
        "Select date range for analytics:",
        value=(full_range_min, full_range_max),
        min_value=full_range_min,
        max_value=full_range_max,
        help="Filter all analytics and charts by this date range"
    )
    
    # Validate date range selection
    start_date, end_date = validate_date_range(analytics_date_filter)
    
    # Apply date filter to analytics data
    analytics_df = df[
        (df['timestamp'].dt.date >= start_date) & 
        (df['timestamp'].dt.date <= end_date)
    ].copy()
    
    # Show filtered data info
    if len(analytics_df) != len(df):
        st.info(f"📊 Showing analytics for {start_date} to {end_date} | "
               f"Filtered: {len(analytics_df):,} messages from {analytics_df['thread_id'].nunique():,} conversations "
               f"(Original: {len(df):,} messages from {df['thread_id'].nunique():,} conversations)")
    
    # Check if filtered data is empty
    if len(analytics_df) == 0:
        st.warning(f"⚠️ No data found for the selected date range ({start_date} to {end_date}). Please select a different date range.")
        st.stop()
    
    st.divider()

    # Display all analytics sections
    show_key_metrics(analytics_df)
    show_conversation_length_analysis(analytics_df)
    show_daily_analytics(analytics_df)
    show_region_distribution(analytics_df)

def validate_date_range(analytics_date_filter):
    """Validate and extract start and end dates from date input"""
    if isinstance(analytics_date_filter, tuple) and len(analytics_date_filter) == 2:
        start_date, end_date = analytics_date_filter
    elif isinstance(analytics_date_filter, (list, tuple)) and len(analytics_date_filter) == 1:
        # Only one date selected, use it as both start and end
        start_date = end_date = analytics_date_filter[0]
    else:
        # Single date object (shouldn't happen with range=True, but just in case)
        start_date = end_date = analytics_date_filter
    
    # Ensure we have valid dates
    if start_date is None or end_date is None:
        st.warning("⚠️ Please select a complete date range to continue.")
        st.stop()
    
    return start_date, end_date

def calculate_metrics(analytics_df):
    """Calculate all key metrics from the analytics dataframe"""
    total_conversations = analytics_df['thread_id'].nunique()
    total_messages = len(analytics_df)
    user_messages = len(analytics_df[analytics_df['role'] == 'user'])
    assistant_messages = len(analytics_df[analytics_df['role'] == 'assistant'])
    arabic_messages = analytics_df['message'].apply(is_arabic).sum()
    english_messages = (~analytics_df['message'].apply(is_arabic)).sum()
    
    conv_lengths = analytics_df.groupby('thread_id').size()
    conv_gt6 = (conv_lengths > 6).sum()
    conv_le2 = (conv_lengths <= 2).sum()
    
    long_user_prompts = analytics_df[(analytics_df['role'] == 'user') & (analytics_df['message'].str.split().str.len() > 30)]
    empty_assistant = analytics_df[(analytics_df['role'] == 'assistant') & (analytics_df['message'].str.strip() == '')]
    error_msgs = analytics_df['message'].str.contains('error|failed|exception|problem|issue', case=False, na=False).sum()
    happy_msgs = analytics_df['message'].str.contains('thank|great|awesome|perfect|amazing|love|happy|helpful|👍', case=False, na=False).sum()
    frustrated_msgs = analytics_df['message'].str.contains('not working|bad|hate|angry|frustrated|annoy|useless|waste|problem|issue|disappoint|😡|😠|👎', case=False, na=False).sum()
    
    avg_len = conv_lengths.mean() if len(conv_lengths) > 0 else 0
    median_len = conv_lengths.median() if len(conv_lengths) > 0 else 0

    return {
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'user_messages': user_messages,
        'assistant_messages': assistant_messages,
        'arabic_messages': arabic_messages,
        'english_messages': english_messages,
        'conv_gt6': conv_gt6,
        'conv_le2': conv_le2,
        'long_user_prompts': long_user_prompts,
        'empty_assistant': empty_assistant,
        'error_msgs': error_msgs,
        'happy_msgs': happy_msgs,
        'frustrated_msgs': frustrated_msgs,
        'avg_len': avg_len,
        'median_len': median_len,
        'conv_lengths': conv_lengths
    }

def show_key_metrics(analytics_df):
    """Display key metrics section"""
    metrics = calculate_metrics(analytics_df)
    
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
        ("Total Conversations", metrics['total_conversations'], "Total Messages", metrics['total_messages']),
        ("User Messages", metrics['user_messages'], "Assistant Replies", metrics['assistant_messages']),
        ("Arabic Messages", metrics['arabic_messages'], "English Messages", metrics['english_messages']),
        (">6 Message Conversations", metrics['conv_gt6'], "≤2 Message Conversations", metrics['conv_le2']),
        ("Empty Assistant Responses", len(metrics['empty_assistant']), "Error Messages", metrics['error_msgs']),
        ("Happy User Messages", metrics['happy_msgs'], "Frustrated User Messages", metrics['frustrated_msgs']),
        ("Average Messages/Chat", f"{metrics['avg_len']:.2f}", "Median Messages/Chat", f"{metrics['median_len']:.0f}"),
    ]
    
    metric_cols = st.columns(2)
    for left_label, left_val, right_label, right_val in paired_metrics:
        with metric_cols[0]:
            st.markdown(f"<div class='metric-box'><div class='metric-title'>{left_label}</div><div class='metric-value'>{left_val}</div></div>", unsafe_allow_html=True)
        with metric_cols[1]:
            st.markdown(f"<div class='metric-box'><div class='metric-title'>{right_label}</div><div class='metric-value'>{right_val}</div></div>", unsafe_allow_html=True)
    
    # Additional: Long user prompts
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Long User Prompts (&gt;30 words)</div><div class='metric-value'>{len(metrics['long_user_prompts'])}</div></div>", unsafe_allow_html=True)

def show_conversation_length_analysis(analytics_df):
    """Display conversation length analysis section"""
    metrics = calculate_metrics(analytics_df)
    conv_lengths = metrics['conv_lengths']
    
    st.subheader("Conversation Length Analysis")
    st.markdown(f"**Average Messages per Conversation:** <span style='color:#2e7be6;font-size:1.3rem'><b>{metrics['avg_len']:.2f}</b></span>", unsafe_allow_html=True)
    st.markdown(f"**Median Messages per Conversation:** <span style='color:#2e7be6;font-size:1.3rem'><b>{metrics['median_len']:.0f}</b></span>", unsafe_allow_html=True)
    
    # Histogram
    fig_hist = px.histogram(conv_lengths, nbins=20, title='Distribution of Conversation Lengths', labels={'value':'Messages per Conversation'})
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Show top 10 longest conversations
    st.subheader("Top 10 Longest Conversations")
    st.dataframe(conv_lengths.sort_values(ascending=False).head(10).reset_index().rename(columns={0:'Messages'}), use_container_width=True)

def show_daily_analytics(analytics_df):
    """Display daily analytics charts"""
    # Chats per day
    chats_per_day = analytics_df.groupby(analytics_df['timestamp'].dt.date)['thread_id'].nunique().reset_index()
    fig1 = px.bar(chats_per_day, x='timestamp', y='thread_id', labels={'timestamp':'Date', 'thread_id':'Conversations'}, title='New Conversations per Day')
    st.plotly_chart(fig1, use_container_width=True)
    
    # Messages per day
    msgs_per_day = analytics_df.groupby(analytics_df['timestamp'].dt.date).size().reset_index(name='messages')
    fig_msgs = px.line(msgs_per_day, x='timestamp', y='messages', title='Messages Sent per Day')
    st.plotly_chart(fig_msgs, use_container_width=True)

def show_region_distribution(analytics_df):
    """Display region distribution charts"""
    # Region distribution
    region_counts = analytics_df.groupby('region')['thread_id'].nunique().reset_index()
    fig2 = px.pie(region_counts, names='region', values='thread_id', title='Conversations by Region')
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("**Conversations by Region (Table):**")
    st.dataframe(region_counts.rename(columns={'thread_id': 'Conversations'}), use_container_width=True)
