"""
Analytics functions for the Layla Conversation Analyzer
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from .utils import is_arabic, categorize_opening_message

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
    show_opening_categories_analysis(analytics_df)
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

def show_opening_categories_analysis(analytics_df):
    """Display conversation opening categories analysis"""
    st.subheader("📝 Conversation Opening Categories")

    st.markdown(
    """
    **What are these categories?**  
    Conversations are automatically categorized based on the first user message. This helps understand what topics users are most interested in when starting a conversation.
    """
    )

    st.markdown(
    """
    **Understanding the Delta (Week-over-Week Change):**  
    The delta compares the number of conversations in each category from the most recent 7 days to the previous 7 days.
    """
    )

    # Get unique conversations and their opening categories - fixed to avoid pandas warning
    conversations = analytics_df.groupby('thread_id').first().reset_index()
    
    # Get first user message for each conversation to categorize - optimized approach
    # Extract the first user message for each thread_id
    first_user_messages = (
        analytics_df[analytics_df['role'] == 'user']
        .sort_values('timestamp')
        .groupby('thread_id')
        .first()
        .reset_index()
    )
    
    # Categorize the opening messages
    first_user_messages['category'] = first_user_messages['message'].apply(categorize_opening_message)
    
    # Merge categories back with conversations
    category_df = conversations.merge(
        first_user_messages[['thread_id', 'category']],
        on='thread_id',
        how='left'
    ).fillna({'category': 'Others'})
    
    # Count conversations by category (for the currently filtered date range)
    category_counts = category_df['category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']
    
    # Calculate percentages
    total_conversations = len(category_df)
    category_counts['Percentage'] = (category_counts['Count'] / total_conversations * 100).round(1)
    
    # Compute Week-over-Week absolute deltas by category using first user message timestamp per thread,
    # anchored to the end of the selected date range and computed within the currently filtered data.
    try:
        # Use the currently filtered analytics_df as the base
        base_df = analytics_df.copy()
        # Extract first user message per thread with timestamp within the filtered range
        first_users_all = (
            base_df[base_df['role'] == 'user']
            .sort_values('timestamp')
            .groupby('thread_id')
            .first()
            .reset_index()[['thread_id', 'message', 'timestamp']]
        )
        first_users_all['category'] = first_users_all['message'].apply(categorize_opening_message)
        # Define windows relative to the end of the selected date range
        end_ts = base_df['timestamp'].max()
        curr_start = end_ts - pd.Timedelta(days=7)
        prev_start = end_ts - pd.Timedelta(days=14)
        curr_mask = first_users_all['timestamp'] > curr_start
        prev_mask = (first_users_all['timestamp'] > prev_start) & (first_users_all['timestamp'] <= curr_start)
        curr_counts = first_users_all.loc[curr_mask, 'category'].value_counts()
        prev_counts = first_users_all.loc[prev_mask, 'category'].value_counts()
        wow_delta_counts = (curr_counts - prev_counts).to_dict()

        # Calculate percentage deltas
        wow_delta_percent = {}
        for cat in set(curr_counts.index).union(set(prev_counts.index)):
            prev = prev_counts.get(cat, 0)
            curr = curr_counts.get(cat, 0)
            if prev > 0:
                percent = ((curr - prev) / prev) * 100
                wow_delta_percent[cat] = percent
            else:
                wow_delta_percent[cat] = None
    except Exception:
        wow_delta_counts = {}
        wow_delta_percent = {}

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    categories = ['Fragrance Help', 'Skincare Routine', 'Product Summarization', 'Others']
    cols = [col1, col2, col3, col4]
    
    for i, category in enumerate(categories):
        count = category_counts[category_counts['Category'] == category]['Count'].values
        count = count[0] if len(count) > 0 else 0
        percentage = category_counts[category_counts['Category'] == category]['Percentage'].values
        percentage = percentage[0] if len(percentage) > 0 else 0
        
        with cols[i]:
            delta_val = wow_delta_counts.get(category, None)
            if delta_val is None or pd.isna(delta_val):
                st.metric(category, f"{count} ({percentage}%)")
            else:
                percent_val = wow_delta_percent.get(category, None)
                delta_str = f"{int(delta_val):+d}"
                if percent_val is not None:
                    delta_str += f" ({percent_val:+.1f}%)"
                st.metric(
                    category,
                    f"{count} ({percentage}%)",
                    delta=delta_str,
                    delta_color="normal",  # up is green, down is red
                    help="Week-over-week change: absolute and percentage based on conversation openings (first user message).",
                )
    
    # Create visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        fig_pie = px.pie(
            category_counts, 
            values='Count', 
            names='Category',
            title='Distribution of Conversation Opening Categories',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart
        fig_bar = px.bar(
            category_counts.sort_values('Count', ascending=True), 
            x='Count', 
            y='Category',
            orientation='h',
            title='Conversations by Opening Category',
            text='Count',
            color='Category',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detailed breakdown table
    st.markdown("**Detailed Breakdown:**")
    display_df = category_counts.copy()
    display_df['Count'] = display_df['Count'].astype(str) + ' (' + display_df['Percentage'].astype(str) + '%)'
    display_df = display_df[['Category', 'Count']].rename(columns={'Count': 'Conversations (Percentage)'})
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def show_conversation_length_analysis(analytics_df):
    """Display conversation length analysis section"""
    metrics = calculate_metrics(analytics_df)
    conv_lengths = metrics['conv_lengths']
    
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
