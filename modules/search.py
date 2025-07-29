"""
Keyword Search functionality for the Layla Conversation Analyzer
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime
from .utils import is_arabic, translate_text

def show_keyword_search(df):
    """Display the keyword search interface"""
    st.header("🔍 Keyword Search Across All Conversations")
    
    # Filter by launch date (July 1, 2025) to latest
    min_date = pd.to_datetime('2025-07-01')
    filtered_df = df[df['timestamp'] >= min_date]
    
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
        region_search_filter = st.selectbox("Filter by region:", 
                                          ["All"] + sorted(filtered_df['region'].unique().tolist()))
    with col5:
        min_results = st.number_input("Max results:", min_value=10, max_value=1000, value=100, step=10)
    
    if search_keyword:
        _perform_search(filtered_df, search_keyword, case_sensitive, role_filter, 
                       region_search_filter, min_results)
    else:
        st.info("Enter a keyword above to search across all messages in all conversations.")

def _perform_search(df, search_keyword, case_sensitive, role_filter, region_filter, max_results):
    """Perform the actual search and display results"""
    # Prepare search dataframe
    search_df = df.copy()
    
    # Apply filters
    if role_filter != "All":
        search_df = search_df[search_df['role'] == role_filter]
    
    if region_filter != "All":
        search_df = search_df[search_df['region'] == region_filter]
    
    # Perform search
    if case_sensitive:
        mask = search_df['message'].str.contains(search_keyword, na=False)
    else:
        mask = search_df['message'].str.contains(search_keyword, case=False, na=False)
    
    results = search_df[mask].copy()
    
    if len(results) > 0:
        _display_search_results(results, search_keyword, case_sensitive, max_results)
    else:
        st.warning(f"No messages found containing '{search_keyword}' with the selected filters.")
        _show_search_tips()

def _display_search_results(results, search_keyword, case_sensitive, max_results):
    """Display search results with summary and detailed view"""
    st.success(f"Found **{len(results)}** messages containing '{search_keyword}'")
    
    # Summary statistics
    _show_search_summary(results)
    
    # Limit results for display
    if len(results) > max_results:
        results_display = results.head(max_results)
        st.warning(f"Showing first {max_results} results out of {len(results)} total matches")
    else:
        results_display = results
    
    # Sort by timestamp (most recent first)
    results_display = results_display.sort_values('timestamp', ascending=False)
    
    # Display results with highlighting
    st.subheader("Search Results")
    
    # Add download button
    _add_download_button(results, search_keyword)
    
    # Display results
    _show_results_grouped_or_list(results_display, search_keyword, case_sensitive)
    
    # Analysis charts
    _show_search_analysis(results, search_keyword)

def _show_search_summary(results):
    """Show summary statistics for search results"""
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

def _add_download_button(results, search_keyword):
    """Add download button for search results"""
    csv_results = results[['thread_id', 'timestamp', 'role', 'message', 'region']].copy()
    csv_results['timestamp'] = csv_results['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    csv_string = csv_results.to_csv(index=False)
    st.download_button(
        label="📥 Download search results as CSV",
        data=csv_string,
        file_name=f"keyword_search_{search_keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def _show_results_grouped_or_list(results_display, search_keyword, case_sensitive):
    """Show results either grouped by conversation or as a list"""
    if st.checkbox("Group by conversation", value=True):
        _show_grouped_results(results_display, search_keyword, case_sensitive)
    else:
        _show_list_results(results_display, search_keyword, case_sensitive)

def _show_grouped_results(results_display, search_keyword, case_sensitive):
    """Show results grouped by conversation"""
    for thread_id in results_display['thread_id'].unique():
        thread_results = results_display[results_display['thread_id'] == thread_id]
        thread_info = thread_results.iloc[0]
        
        with st.expander(f"💬 Conversation {thread_id} | {thread_info['region']} | {len(thread_results)} matches"):
            for _, row in thread_results.iterrows():
                _display_message_with_highlighting(row, search_keyword, case_sensitive)

def _show_list_results(results_display, search_keyword, case_sensitive):
    """Show results as a list without grouping"""
    for _, row in results_display.iterrows():
        message = _highlight_search_term(row['message'], search_keyword, case_sensitive)
        
        role_color = "#1f77b4" if row['role'] == 'user' else "#ff7f0e"
        st.markdown(f"""
        <div style='border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 4px solid {role_color};'>
            <div style='display: flex; justify-content: between; align-items: center; margin-bottom: 8px;'>
                <small style='color: #666;'><b>Conversation:</b> {row['thread_id']} | <b>Time:</b> {row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | <b>Sender:</b> {row['role'].upper()} | <b>Region:</b> {row['region']}</small>
            </div>
            <div>{message}</div>
        </div>
        """, unsafe_allow_html=True)
        
        _add_translation_button(row, f"search_trans_list_{row.name}")

def _display_message_with_highlighting(row, search_keyword, case_sensitive):
    """Display a single message with search term highlighting"""
    message = _highlight_search_term(row['message'], search_keyword, case_sensitive)
    
    role_color = "#1f77b4" if row['role'] == 'user' else "#ff7f0e"
    st.markdown(f"""
    <div style='border-left: 4px solid {role_color}; padding-left: 12px; margin: 8px 0;'>
        <small style='color: #666;'>{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | <b>{row['role'].upper()}</b></small><br>
        {message}
    </div>
    """, unsafe_allow_html=True)
    
    _add_translation_button(row, f"search_trans_{row.name}")

def _highlight_search_term(message, search_keyword, case_sensitive):
    """Highlight search term in message"""
    if case_sensitive:
        return message.replace(search_keyword, f"**🔍{search_keyword}**")
    else:
        pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
        return pattern.sub(f"**🔍{search_keyword}**", message)

def _add_translation_button(row, key):
    """Add translation button for Arabic messages"""
    if is_arabic(row['message']):
        if st.button(f"Translate", key=key):
            translation = translate_text(row['message'])
            st.markdown(f"<span style='color:green; font-style:italic;'><b>Translation:</b> {translation}</span>", 
                      unsafe_allow_html=True)

def _show_search_analysis(results, search_keyword):
    """Show word analysis and timeline for search results"""
    # Word frequency analysis
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

def _show_search_tips():
    """Show tips for better search results"""
    st.info("💡 **Tips for better search results:**\n"
           "- Try different keywords or synonyms\n"
           "- Check if case sensitivity is affecting your search\n"
           "- Remove sender or region filters to broaden the search\n"
           "- Use partial words (e.g., 'book' to find 'booking', 'booked', etc.)")
