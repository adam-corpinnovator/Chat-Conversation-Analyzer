import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
from deep_translator import GoogleTranslator

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
    st.set_page_config(page_title="AI Chat Analyzer", layout="wide")
    st.title("Chat Conversation Analyzer")

    # File uploader
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded_file is None:
        st.warning("Please upload a CSV file to proceed.")
        return

    # Load data from uploaded file
    df = pd.read_csv(uploaded_file, header=None, names=[
        'thread_id', 'timestamp', 'role', 'message', 'region', 'extra'
    ], usecols=range(5))
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filter by launch date (July 2, 2025) to latest
    min_date = pd.to_datetime('2025-07-04')
    max_date = df['timestamp'].max().normalize()
    df = df[df['timestamp'] >= min_date]

    tab2, tab1 = st.tabs(["Analytics Dashboard", "Thread Explorer"])

    with tab1:
        st.header("Thread Explorer")
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

        threads = filtered_df.groupby('thread_id').first().reset_index()
        search_term = st.text_input("Search in threads (user/assistant/message)")
        if search_term:
            mask = threads.apply(lambda row: search_term.lower() in str(row['thread_id']).lower() or search_term.lower() in str(row['region']).lower() or search_term.lower() in str(row['message']).lower(), axis=1)
            threads = threads[mask]
        thread_options = threads['thread_id'] + ' | ' + threads['timestamp'].dt.strftime('%Y-%m-%d %H:%M') + ' | ' + threads['region']
        selected_thread = st.selectbox("Select a thread:", thread_options if not thread_options.empty else ["No threads found"])
        if selected_thread != "No threads found":
            thread_id = selected_thread.split(' | ')[0]
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
            st.info("No threads match the selected filters.")

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
            (">6 Turn Conversations", conv_gt6, "≤2 Turn Conversations", conv_le2),
            ("Empty Assistant Responses", len(empty_assistant), "Explicit Error Messages", error_msgs),
            ("Happy User Messages", happy_msgs, "Frustrated User Messages", frustrated_msgs),
            ("Average Msgs/Thread", f"{avg_len:.2f}", "Median Msgs/Thread", f"{median_len:.0f}"),
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
        st.markdown(f"**Average Messages per Thread:** <span style='color:#2e7be6;font-size:1.3rem'><b>{avg_len:.2f}</b></span>", unsafe_allow_html=True)
        st.markdown(f"**Median Messages per Thread:** <span style='color:#2e7be6;font-size:1.3rem'><b>{median_len:.0f}</b></span>", unsafe_allow_html=True)
        fig_hist = px.histogram(conv_lengths, nbins=20, title='Distribution of Conversation Lengths', labels={'value':'Messages per Thread'})
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
        fig1 = px.bar(chats_per_day, x='timestamp', y='thread_id', labels={'timestamp':'Date', 'thread_id':'Chat Threads'}, title='Chat Threads per Day')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Messages per day
        msgs_per_day = df.groupby(df['timestamp'].dt.date).size().reset_index(name='messages')
        fig_msgs = px.line(msgs_per_day, x='timestamp', y='messages', title='Messages Sent per Day')
        st.plotly_chart(fig_msgs, use_container_width=True)

        # Region distribution
        region_counts = df.groupby('region')['thread_id'].nunique().reset_index()
        fig2 = px.pie(region_counts, names='region', values='thread_id', title='Chats by Region')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("**Chats by Region (Table):**")
        st.dataframe(region_counts.rename(columns={'thread_id': 'Chat Threads'}), use_container_width=True)

        # Shortest conversations
        st.subheader("Longest Conversations")
        st.dataframe(conv_lengths.sort_values(ascending=False).head(10).reset_index().rename(columns={0:'Messages'}))

if __name__ == "__main__":
    main()
