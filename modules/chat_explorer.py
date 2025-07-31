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
        
        .product-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 1px solid #dee2e6;
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .product-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }
        
        .product-card-header {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .product-icon {
            font-size: 16px;
            margin-right: 8px;
        }
        
        .product-title {
            font-weight: 600;
            color: #495057;
            font-size: 14px;
        }
        
        .product-id {
            font-family: 'Monaco', 'Consolas', monospace;
            background: #f8f9fa;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            color: #6c757d;
            margin: 5px 0;
        }
        
        .product-link {
            display: inline-block;
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .product-link:hover {
            transform: translateY(-1px);
            box-shadow: 0 3px 8px rgba(0,123,255,0.3);
            text-decoration: none;
            color: white;
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
        <div class="message-time">👤 User • {time_str} • {relative_time}</div>
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
    """Display product recommendations as separate cards"""
    if not recommendations:
        return
    
    rec_count = len(recommendations)
    rec_icon = "🎁" if rec_count == 1 else "🛍️"
    
    st.markdown(f"""
    <div style="margin: 15px 50px 15px 0;">
        <div style="font-size: 14px; font-weight: 600; color: #495057; margin-bottom: 10px;">
            {rec_icon} {rec_count} Product Recommendation{'s' if rec_count > 1 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    for i, product_id in enumerate(recommendations):
        if product_id:  # Only display if product_id is not empty
            product_link = f"https://www.faces.ae/en/search?q={product_id}&lang=en_AE"
            
            st.markdown(f"""
            <div class="product-card">
                <div class="product-card-header">
                    <span class="product-icon">🛍️</span>
                    <span class="product-title">Product Recommendation {i + 1}</span>
                </div>
                <div class="product-id">ID: {product_id}</div>
                <a href="{product_link}" target="_blank" class="product-link">
                    🔗 View on Faces.ae
                </a>
            </div>
            """, unsafe_allow_html=True)

def _parse_assistant_response(message):
    """Parse JSON from assistant response to extract recommendations and response text"""
    if not message or not message.strip():
        return [], message
    
    original_message = message.strip()
    
    # Handle CSV format: """{"recommendations":...}"""
    if original_message.startswith('"""') and original_message.endswith('"""'):
        # Remove triple quotes
        json_content = original_message[3:-3]
    else:
        json_content = original_message
    
    # Try to parse the JSON
    try:
        # First, unescape the JSON string - handle double escaped quotes
        # Convert \" back to " and \\" back to \"
        clean_json = json_content.replace('\\"', '"')
        
        # Handle cases where the JSON itself is quoted
        if clean_json.startswith('"') and clean_json.endswith('"'):
            clean_json = clean_json[1:-1]
            # Unescape again after removing outer quotes
            clean_json = clean_json.replace('\\"', '"')
        
        # Parse the JSON
        data = json.loads(clean_json)
        
        recommendations = []
        response_text = ""
        
        # Extract recommendations
        if 'recommendations' in data and isinstance(data['recommendations'], list):
            for item in data['recommendations']:
                if isinstance(item, dict) and 'primary_id' in item:
                    primary_id = str(item['primary_id']).strip()
                    if primary_id:
                        recommendations.append(primary_id)
        
        # Extract response text
        if 'response_text' in data and data['response_text']:
            response_text = data['response_text']
            # Unescape newlines and other escaped characters in response text
            response_text = response_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        
        return recommendations, response_text
        
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        # If JSON parsing fails completely, try regex extraction
        try:
            recommendations = []
            response_text = ""
            
            # Extract primary_ids using regex
            primary_id_pattern = r'"primary_id":\s*"([^"]+)"'
            matches = re.findall(primary_id_pattern, original_message)
            if matches:
                recommendations = [match.strip() for match in matches if match.strip()]
            
            # Extract response_text using regex
            response_patterns = [
                r'"response_text":\s*"(.*?)"(?=\s*[,}])',
                r'"response_text":"(.*?)"(?=,"|\})',
            ]
            
            for pattern in response_patterns:
                match = re.search(pattern, original_message, re.DOTALL)
                if match:
                    response_text = match.group(1)
                    # Clean up escape characters
                    response_text = response_text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    break
            
            if recommendations or response_text:
                return recommendations, response_text
                
        except Exception:
            pass
    
    # Final fallback - return original message if all parsing fails
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
