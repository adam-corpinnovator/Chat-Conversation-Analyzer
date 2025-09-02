"""
Intelligence chat interface for the Layla Conversation Analyzer
Allows users to chat with their conversation data using AI
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from typing import List, Dict, Any
import io

try:
    from langchain_experimental.agents.agent_toolkits import (
        create_pandas_dataframe_agent,
    )
    from langchain_openai import ChatOpenAI
    from langchain.agents.agent_types import AgentType

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def show_intelligence_chat(df: pd.DataFrame):
    """Display the AI chat interface for data querying"""
    st.header("Intelligence Chat 🤖")
    st.markdown("Ask questions about your conversation data in natural language!")

    # Check if LangChain is available
    if not LANGCHAIN_AVAILABLE:
        st.error(
            "❌ LangChain dependencies not installed. Please install the required packages."
        )
        st.code("pip install langchain langchain-openai langchain-experimental")
        return

    # Check for OpenAI API key
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        st.warning(
            "⚠️ OpenAI API key required. Please add it to your Streamlit secrets or set the OPENAI_API_KEY environment variable."
        )
        return

    # Preprocess the DataFrame for better AI analysis
    processed_df = preprocess_dataframe(df)

    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display data info
    display_data_info(processed_df)

    # Add a test button to verify the agent works
    if st.button("🧪 Test Agent", help="Test if the AI agent can analyze the data"):
        test_agent_functionality(processed_df, openai_api_key)

    # Show suggested queries
    show_suggested_queries()

    # Chat interface
    display_chat_interface(processed_df, openai_api_key)


def get_openai_api_key() -> str:
    """Get OpenAI API key from secrets or environment"""
    try:
        # Try to get from Streamlit secrets first
        return st.secrets.get("OPENAI_API_KEY", "")
    except:
        # Fall back to environment variable
        return os.environ.get("OPENAI_API_KEY", "")


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the DataFrame to make it more suitable for AI analysis"""
    try:
        # Make a copy to avoid modifying the original
        processed_df = df.copy()

        # Ensure proper data types and handle NaN values
        processed_df["thread_id"] = processed_df["thread_id"].astype(str)
        processed_df["role"] = processed_df["role"].astype(str)
        processed_df["message"] = processed_df["message"].fillna("").astype(str)
        processed_df["region"] = processed_df["region"].astype(str)

        # Add helpful derived columns for analysis
        processed_df["message_length"] = processed_df["message"].str.len()
        processed_df["hour"] = processed_df["timestamp"].dt.hour
        processed_df["day_of_week"] = processed_df["timestamp"].dt.day_name()

        # Convert date to string to avoid PyArrow serialization issues
        processed_df["date"] = processed_df["timestamp"].dt.date.astype(str)

        # Remove any rows with missing critical data
        processed_df = processed_df.dropna(subset=["thread_id", "role"])

        # Ensure all columns are compatible with PyArrow
        for col in processed_df.columns:
            if processed_df[col].dtype == "object":
                processed_df[col] = processed_df[col].astype(str)

        return processed_df

    except Exception as e:
        st.error(f"Error preprocessing data: {e}")
        return df  # Return original if preprocessing fails


def test_agent_functionality(df: pd.DataFrame, openai_api_key: str):
    """Test if the agent can analyze the data"""
    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=openai_api_key)
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,  # Better for newer models
            allow_dangerous_code=True,
            handle_parsing_errors=True,  # Add this back for newer models
        )

        test_query = "How many rows are in this dataset?"
        with st.spinner("Testing agent..."):
            response = agent.invoke(test_query)
            st.success("✅ Agent test successful!")
            st.write("Test response:", response)

    except Exception as e:
        st.error(f"❌ Agent test failed: {str(e)}")
        st.write("Full error details:", str(e))  # More detailed error info


def display_data_info(df: pd.DataFrame):
    """Display basic information about the loaded data"""
    with st.expander("📊 Data Overview", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Messages", f"{len(df):,}")
        with col2:
            st.metric("Unique Conversations", f"{df['thread_id'].nunique():,}")
        with col3:
            st.metric(
                "Date Range",
                f"{df['timestamp'].min().strftime('%b %d')} - {df['timestamp'].max().strftime('%b %d')}",
            )
        with col4:
            st.metric("Regions", f"{df['region'].nunique()}")

        st.markdown("**Available Columns:**")
        st.write(f"• `thread_id`: Conversation identifier")
        st.write(f"• `timestamp`: Message timestamp")
        st.write(f"• `role`: user or assistant")
        st.write(f"• `message`: Message content")
        st.write(f"• `region`: Geographic region")


def show_suggested_queries():
    """Display suggested query examples"""
    with st.expander("💡 Suggested Questions", expanded=True):
        st.markdown("**Conversation Analytics:**")
        suggestions = [
            "How many conversations happened this month?",
            "What are the most common user questions?",
            "Show me conversation volume by region",
            "What's the average conversation length?",
            "Which days have the highest user activity?",
            "Find conversations that mention 'refund' or 'cancel'",
            "What percentage of conversations are from each region?",
            "Show me the busiest hour of the day",
            "What brands are mentioned most in the messages?",
        ]

        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(
                    suggestion, key=f"suggestion_{i}", use_container_width=True
                ):
                    st.session_state.suggested_query = suggestion


def display_chat_interface(df: pd.DataFrame, openai_api_key: str):
    """Display the main chat interface"""

    # Simplified info display without problematic DataFrame display
    with st.expander("� Dataset Info", expanded=False):
        st.write(f"**Dataset shape:** {df.shape[0]:,} rows × {df.shape[1]} columns")
        st.write(f"**Columns:** {', '.join(df.columns)}")
        st.write(f"**Date range:** {df['timestamp'].min().strftime('%Y-%m-%d')} to {df['timestamp'].max().strftime('%Y-%m-%d')}")
        st.write(f"**Regions:** {', '.join(df['region'].unique())}")

    # Create the AI agent
    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,  # Lower temperature for more consistent parsing
            api_key=openai_api_key,
        )

        # Create agent with configuration optimized for newer models
        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,  # Better for gpt-4o
            allow_dangerous_code=True,  # We need this for pandas operations
            handle_parsing_errors=True,  # Essential for newer models
            prefix="You are working with a pandas dataframe called `df`. This contains conversation data from a customer service chatbot. Analyze the data and provide clear, concise answers.",
        )
    except Exception as e:
        st.error(f"❌ Failed to initialize AI agent: {str(e)}")
        return

    # Chat input
    user_query = st.chat_input("Ask a question about your conversation data...")

    # Handle suggested query
    if "suggested_query" in st.session_state:
        user_query = st.session_state.suggested_query
        del st.session_state.suggested_query

    if user_query:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # Get AI response
        with st.spinner("🤖 Analyzing your data..."):
            try:
                # Use the user's question directly - let the agent figure it out
                response = agent.invoke(user_query)

                # Extract the answer from the response
                if isinstance(response, dict):
                    if "output" in response:
                        ai_response = response["output"]
                    elif "result" in response:
                        ai_response = response["result"]
                    else:
                        # If it's a dict but no clear output, show the whole thing
                        ai_response = str(response)
                else:
                    ai_response = str(response)

                # Add AI response to history
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": ai_response}
                )

            except Exception as e:
                error_message = f"❌ Sorry, I encountered an error: {str(e)}"
                st.error(error_message)
                # Also add to chat history
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": error_message}
                )

    # Display chat history
    display_chat_history()

    # Clear chat button
    if st.button("🗑️ Clear Chat", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()


def display_chat_history():
    """Display the chat conversation history"""
    if not st.session_state.chat_history:
        st.markdown(
            "👋 **Welcome!** Ask me any questions about your conversation data."
        )
        return

    # Display messages in reverse order (newest first)
    for message in reversed(st.session_state.chat_history):
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])


def estimate_token_cost(query: str, response: str) -> float:
    """Estimate the cost of the API call (rough estimation)"""
    # Rough estimation: ~1 token per 4 characters
    # GPT-3.5-turbo: $0.0015 per 1K input tokens, $0.002 per 1K output tokens
    input_tokens = len(query) / 4
    output_tokens = len(response) / 4

    input_cost = (input_tokens / 1000) * 0.0015
    output_cost = (output_tokens / 1000) * 0.002

    return input_cost + output_cost
