"""
Chat Explorer functionality for the Layla Conversation Analyzer
"""
import streamlit as st
import pandas as pd
from .utils import is_arabic, translate_text

def show_chat_explorer(df):
    """Display the chat explorer interface"""
    st.header("Chat Explorer")
    
    # Filter by launch date (July 1, 2025) to latest
    min_date = pd.to_datetime('2025-07-01')
    max_date = df['timestamp'].max().normalize()
    filtered_df = df[df['timestamp'] >= min_date]
    
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
        region_filter = st.selectbox("Region", options=["All"] + sorted(filtered_df['region'].unique().tolist()))
    with col3:
        time_filter = st.text_input("Time (HH:MM, optional)")

    # Apply filters
    if isinstance(date_filter, tuple) and len(date_filter) == 2:
        filtered_df = filtered_df[(filtered_df['timestamp'].dt.date >= date_filter[0]) & (filtered_df['timestamp'].dt.date <= date_filter[1])]
    
    if region_filter != "All":
        filtered_df = filtered_df[filtered_df['region'] == region_filter]
    
    if time_filter:
        filtered_df = filtered_df[filtered_df['timestamp'].dt.strftime('%H:%M').str.contains(time_filter)]

    # Search and conversation selection
    chats = filtered_df.groupby('thread_id').first().reset_index()
    search_term = st.text_input("Search in conversations (user/assistant/message)")
    
    if search_term:
        mask = chats.apply(lambda row: search_term.lower() in str(row['thread_id']).lower() or 
                          search_term.lower() in str(row['region']).lower() or 
                          search_term.lower() in str(row['message']).lower(), axis=1)
        chats = chats[mask]
    
    chat_options = chats['thread_id'] + ' | ' + chats['timestamp'].dt.strftime('%Y-%m-%d %H:%M') + ' | ' + chats['region']
    selected_chat = st.selectbox("Select a conversation:", 
                                chat_options if not chat_options.empty else ["No conversations found"])
    
    # Display selected conversation
    if selected_chat != "No conversations found":
        thread_id = selected_chat.split(' | ')[0]
        thread_df = df[df['thread_id'] == thread_id]
        
        for _, row in thread_df.iterrows():
            msg = row['message']
            if is_arabic(msg):
                if st.button(f"Translate (EN) {row['timestamp']}", key=f"trans_{row['timestamp']}"):
                    translation = translate_text(msg)
                    st.markdown(f"**{row['role'].capitalize()}** ({row['timestamp']}): {msg}")
                    st.markdown(f"<span style='color:green'><b>EN:</b> {translation}</span>", 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f"**{row['role'].capitalize()}** ({row['timestamp']}): {msg}")
            else:
                st.markdown(f"**{row['role'].capitalize()}** ({row['timestamp']}): {msg}")
    else:
        st.info("No conversations match the selected filters.")
