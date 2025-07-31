"""
Chat Explorer functionality for the Layla Conversation Analyzer
"""
import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
from .utils import is_arabic, translate_text

def show_chat_explorer(df):
    """Display the chat explorer interface"""
    st.header("Chat Explorer")
    
    # Check if dataframe is empty
    if df.empty:
        st.warning("No chat data available. Please upload a file first.")
        return
    
    # Ensure required columns exist
    required_columns = ['timestamp', 'region', 'thread_id', 'role', 'message']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return
    
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
        thread_df = df[df['thread_id'] == thread_id].sort_values('timestamp')
        
        # Get conversation metadata
        first_message = thread_df.iloc[0]
        message_count = len(thread_df)
        duration = thread_df['timestamp'].max() - thread_df['timestamp'].min()
        
        # Format duration as minutes and seconds
        total_seconds = duration.total_seconds()
        if total_seconds > 0:
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            if minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"
        else:
            duration_str = "< 1s"
        
        # Enhanced conversation header
        st.markdown(f"""
        <div class="conversation-header">
            <div class="conversation-title">💬 {thread_id}</div>
            <div class="conversation-meta">
                📅 {first_message['timestamp'].strftime('%B %d, %Y at %H:%M')} •  
                🌍 {first_message['region']} •  
                💬 {message_count} messages •  
                ⏱️ {duration_str}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add custom CSS for chat bubbles
        st.markdown("""
        <style>
        /* CSS Variables for light/dark mode support */
        :root {
            --background-color: white;
            --text-color: #333;
            --secondary-text-color: #666;
            --border-color: #e0e0e0;
            --code-background: #f5f5f5;
            --code-text: #2d3748;
            --code-border: #e2e8f0;
        }
        
        /* Dark mode detection using Streamlit's theme */
        @media (prefers-color-scheme: dark) {
            :root {
                --background-color: #262730;
                --text-color: #fafafa;
                --secondary-text-color: #a0a0a0;
                --border-color: #404040;
                --code-background: #1e1e1e;
                --code-text: #e2e8f0;
                --code-border: #404040;
            }
        }
        
        /* Streamlit dark mode override */
        [data-theme="dark"] {
            --background-color: #262730;
            --text-color: #fafafa;
            --secondary-text-color: #a0a0a0;
            --border-color: #404040;
            --code-background: #1e1e1e;
            --code-text: #e2e8f0;
            --code-border: #404040;
        }
        
        .user-message {
            background: #007bff;
            color: white;
            padding: 15px 20px;
            border-radius: 20px 20px 5px 20px;
            margin: 10px 0 10px 50px;
            box-shadow: 0 2px 10px rgba(0, 123, 255, 0.2);
            position: relative;
            max-width: 100%;
            word-wrap: break-word;
        }
        
        .assistant-message {
            background: #f1f3f4;
            color: #333;
            padding: 15px 20px;
            border-radius: 20px 20px 20px 5px;
            margin: 10px 50px 10px 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            position: relative;
            max-width: 80%;
            word-wrap: break-word;
            border: 1px solid #e0e0e0;
        }
        
        .message-time {
            font-size: 11px;
            opacity: 0.7;
            margin-bottom: 8px;
            font-weight: 500;
            letter-spacing: 0.5px;
        }
        
        .assistant-message .message-time {
            color: #666;
        }
        
        .user-message .message-time {
            color: rgba(255, 255, 255, 0.9);
        }
        
        .message-content {
            line-height: 1.6;
            font-size: 14px;
            font-weight: 400;
        }
        
        .translate-btn {
            background: rgba(0, 123, 255, 0.1);
            border: 1px solid rgba(0, 123, 255, 0.3);
            color: #007bff;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 11px;
            margin-top: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .translate-btn:hover {
            background: rgba(0, 123, 255, 0.2);
            transform: translateY(-1px);
        }
        
        .translation {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 10px 14px;
            margin-top: 10px;
            font-style: italic;
            border-left: 4px solid #007bff;
            font-size: 13px;
            line-height: 1.5;
            color: #333;
        }
        
        .conversation-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }
        
        .conversation-title {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }
        
        .conversation-meta {
            font-size: 12px;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        .product-recommendations {
            margin: 15px 50px 15px 0;
            background: linear-gradient(135deg, #f8f9fb 0%, #f1f4f8 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }
        
        .product-recommendations-header {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .product-recommendations-icon {
            font-size: 18px;
            margin-right: 8px;
        }
        
        .product-recommendations-title {
            font-weight: 600;
            color: #334155;
            font-size: 14px;
            margin: 0;
        }
        
        .product-cards-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: stretch;
        }
        
        .product-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 10px 12px;
            flex: 1;
            min-width: 180px;
            max-width: 250px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
        }
        
        .product-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 3px 8px rgba(0,0,0,0.1);
            border-color: #007bff;
        }
        
        .product-card-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            gap: 8px;
        }
        
        .product-info {
            display: flex;
            align-items: center;
            flex: 1;
            min-width: 0;
        }
        
        .product-icon {
            font-size: 12px;
            margin-right: 6px;
            opacity: 0.7;
            flex-shrink: 0;
        }
        
        .product-id {
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            color: #475569;
            font-weight: 500;
            letter-spacing: 0.3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1;
        }
        
        .product-link {
            display: inline-flex;
            align-items: center;
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 10px;
            font-weight: 500;
            transition: all 0.2s ease;
            white-space: nowrap;
            flex-shrink: 0;
        }
        
        .product-link:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0,123,255,0.3);
            text-decoration: none;
            color: white;
            background: linear-gradient(135deg, #0056b3 0%, #004085 100%);
        }
        
        .product-link-icon {
            font-size: 8px;
            margin-right: 3px;
        }
        
        /* Responsive design for smaller screens */
        @media (max-width: 768px) {
            .product-cards-grid {
                flex-direction: column;
            }
            
            .product-card {
                max-width: none;
            }
            
            .product-card-content {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .product-link {
                align-self: stretch;
                justify-content: center;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        for _, row in thread_df.iterrows():
            _display_message(row)
    else:
        st.info("No conversations match the selected filters.")

def _display_message(row):
    """Display a single message with proper formatting"""
    timestamp = row['timestamp']
    role = row['role']
    message = row['message']
    
    # Format timestamp
    time_str = timestamp.strftime('%H:%M')
    relative_time = _format_relative_time(timestamp)
    
    if role == 'user':
        _display_user_message(message, time_str, relative_time, row)
    else:
        _display_assistant_message(message, time_str, relative_time, row)

def _display_user_message(message, time_str, relative_time, row):
    """Display user message with chat bubble styling"""
    # Clean the message
    clean_message = _clean_message_text(message)
    
    message_html = f"""
    <div class="user-message">
        <div class="message-time">User • {time_str} • {relative_time}</div>
        <div class="message-content">{clean_message}</div>
    </div>
    """
    st.markdown(message_html, unsafe_allow_html=True)
    
    # Add translation button for Arabic messages
    if is_arabic(message):
        _add_translation_section(message, f"user_trans_{row.name}")

def _display_assistant_message(message, time_str, relative_time, row):
    """Display assistant message with chat bubble styling and JSON parsing"""
    # Try to parse JSON response
    recommendations, response_text = _parse_assistant_response(message)
    
    # If we successfully parsed JSON and got response_text, use it; otherwise use original message
    if response_text:
        clean_response = _clean_message_text(response_text)
    else:
        # If no response_text was found, try to clean the original message
        clean_response = _clean_message_text(message)
    
    # Build the message HTML (without inline recommendations)
    message_html = f"""
    <div class="assistant-message">
        <div class="message-time">🤖 Layla Assistant • {time_str} • {relative_time}</div>
        <div class="message-content">{clean_response}</div>
    </div>
    """
    
    st.markdown(message_html, unsafe_allow_html=True)
    
    # Display recommendations as separate cards below the message
    if recommendations:
        _display_product_recommendations(recommendations)
    
    # Add translation button for Arabic messages
    if is_arabic(response_text or message):
        _add_translation_section(response_text or message, f"assistant_trans_{row.name}")

def _display_product_recommendations(recommendations):
    """Display product recommendations as compact cards using native Streamlit components"""
    if not recommendations:
        return
    
    rec_count = len(recommendations)
    
    # Create a container for the recommendations
    with st.container():
        # Header
        st.markdown(f"### {rec_count} Product Recommendation{'s' if rec_count > 1 else ''}")
        
        # Create columns for horizontal layout
        # Calculate number of columns based on recommendations count (max 5 per row)
        cols_per_row = min(len(recommendations), 5)
        cols = st.columns(cols_per_row)
        
        for i, product_id in enumerate(recommendations):
            if product_id:  # Only display if product_id is not empty
                with cols[i % cols_per_row]:
                    # Create a card-like appearance using markdown and styling
                    product_link = f"https://www.faces.ae/en/search?q={product_id}&lang=en_AE"
                    
                    # Use a combination of markdown and button for the card
                    st.markdown(f"""
                    <div style="
                        background: var(--background-color, white);
                        border: 1px solid var(--border-color, #e0e0e0);
                        border-radius: 8px;
                        padding: 12px;
                        margin-bottom: 8px;
                        text-align: center;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        color: var(--text-color, #333);
                    ">
                        <div style="
                            font-size: 10px;
                            color: var(--secondary-text-color, #666);
                            margin-bottom: 4px;
                            font-weight: 500;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        ">Product ID</div>
                        <div style="
                            font-family: 'SF Mono', Monaco, Consolas, monospace;
                            font-size: 11px;
                            background: var(--code-background, #f5f5f5);
                            color: var(--code-text, #2d3748);
                            padding: 6px 8px;
                            border-radius: 4px;
                            margin-bottom: 8px;
                            word-break: break-all;
                            font-weight: 600;
                            border: 1px solid var(--code-border, #e2e8f0);
                        ">{product_id}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Use native Streamlit link button
                    st.link_button("🔗 View Product", product_link, use_container_width=True)

def _parse_assistant_response(message):
    """Parse JSON from assistant response to extract recommendations and response text"""
    if not message or not message.strip():
        return [], message
    
    original_message = message.strip()
    
    try:
        # Handle CSV format: """{"recommendations":...}"""
        if original_message.startswith('"""') and original_message.endswith('"""'):
            json_content = original_message[3:-3]
        else:
            json_content = original_message
        
        # Clean and parse JSON with improved error handling
        clean_json = json_content.replace('\\"', '"')
        
        if clean_json.startswith('"') and clean_json.endswith('"'):
            clean_json = clean_json[1:-1].replace('\\"', '"')
        
        data = json.loads(clean_json)
        
        recommendations = []
        response_text = ""
        
        # Extract recommendations with validation
        if 'recommendations' in data and isinstance(data['recommendations'], list):
            for item in data['recommendations']:
                if isinstance(item, dict) and 'primary_id' in item:
                    primary_id = str(item['primary_id']).strip()
                    if primary_id and primary_id.lower() != 'null':
                        recommendations.append(primary_id)
        
        # Extract response text
        if 'response_text' in data and data['response_text']:
            response_text = data['response_text']
            response_text = response_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        
        return recommendations, response_text
        
    except (json.JSONDecodeError, ValueError, TypeError):
        # Fallback to regex extraction with improved patterns
        try:
            recommendations = []
            response_text = ""
            
            # More robust primary_id extraction
            primary_id_patterns = [
                r'"primary_id":\s*"([^"]+)"',
                r'"primary_id":"([^"]+)"',
                r'primary_id["\']?\s*:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in primary_id_patterns:
                matches = re.findall(pattern, original_message, re.IGNORECASE)
                if matches:
                    recommendations = [match.strip() for match in matches if match.strip() and match.strip().lower() != 'null']
                    break
            
            # More robust response_text extraction
            response_patterns = [
                r'"response_text":\s*"(.*?)"(?=\s*[,}])',
                r'"response_text":"(.*?)"(?=,"|\})',
                r'response_text["\']?\s*:\s*["\']([^"\']*)["\']'
            ]
            
            for pattern in response_patterns:
                match = re.search(pattern, original_message, re.DOTALL | re.IGNORECASE)
                if match:
                    response_text = match.group(1)
                    response_text = response_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    break
            
            if recommendations or response_text:
                return recommendations, response_text
                
        except Exception:
            pass
    
    return [], original_message

def _clean_message_text(text):
    """Clean and format message text for better display"""
    if not text:
        return ""
    
    # First, check if this is a JSON string that needs parsing
    original_text = text.strip()
    if (original_text.startswith('{"') and original_text.endswith('"}')) or (original_text.startswith('{') and original_text.endswith('}')):
        try:
            # Try to parse JSON and extract response_text
            if original_text.startswith('"') and original_text.endswith('"'):
                original_text = original_text[1:-1].replace('\\"', '"')
            
            data = json.loads(original_text)
            if 'response_text' in data:
                text = data['response_text']
            else:
                text = original_text
        except:
            # If JSON parsing fails, continue with regular cleaning
            pass
    
    # Remove extra quotes and escape characters
    text = text.replace('\\"', '"').replace('\\n', '\n')
    
    # Remove leading/trailing quotes if they wrap the entire message
    if text.startswith('"') and text.endswith('"') and text.count('"') == 2:
        text = text[1:-1]
    
    # Remove unwanted symbols and clean up
    text = text.replace('\\', '')  # Remove backslashes
    
    # Convert newlines to HTML breaks
    text = text.replace('\n', '<br>')
    
    # Convert markdown-style formatting to HTML
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'### (.*?)(<br>|$)', r'<h4>\1</h4>', text)
    text = re.sub(r'- \*\*(.*?)\*\*', r'<br>• <strong>\1</strong>', text)
    
    # Handle bullet points and lists
    text = re.sub(r'^- (.*?)$', r'• \1', text, flags=re.MULTILINE)
    text = re.sub(r'<br>- (.*?)(<br>|$)', r'<br>• \1\2', text)
    
    # Handle FAQ formatting
    text = re.sub(r'FAQs?:\s*<br>', '<br><strong>FAQs:</strong><br>', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces and breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(<br>\s*){3,}', '<br><br>', text)  # Limit consecutive breaks
    text = text.strip()
    
    return text

def _add_translation_section(message, key):
    """Add translation button and display for Arabic messages"""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔤 Translate", key=key, help="Translate to English"):
            st.session_state[f"{key}_translation"] = translate_text(message)
    
    # Display translation if it exists
    if f"{key}_translation" in st.session_state:
        translation = st.session_state[f"{key}_translation"]
        st.markdown(f"""
        <div class="translation">
            <strong>🔤 Translation:</strong><br>{_clean_message_text(translation)}
        </div>
        """, unsafe_allow_html=True)

def _format_relative_time(timestamp):
    """Format timestamp to relative time (e.g., '2 minutes ago', '1 hour ago')"""
    now = datetime.now()
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=None)
    if now.tzinfo is None:
        now = now.replace(tzinfo=None)
    
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"
