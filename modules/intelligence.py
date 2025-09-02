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
    """Main function to display the intelligence chat interface"""
    st.title("Intelligence Chat")
    st.markdown("**Ask questions about your conversation data using natural language!**")

    # Get OpenAI API key
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        st.error("⚠️ OpenAI API key not found. Please add it to your Streamlit secrets.")
        st.markdown("""
        Add your OpenAI API key to `.streamlit/secrets.toml`:
        ```toml
        [secrets]
        OPENAI_API_KEY = "your-api-key-here"
        ```
        """)
        return

    # Preprocess the dataframe
    processed_df = preprocess_dataframe(df)

    # Display clean chat interface
    display_clean_chat_interface(processed_df, openai_api_key)


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


def display_clean_chat_interface(df: pd.DataFrame, openai_api_key: str):
    """Display a clean, simple chat interface for conversing with data"""
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Create the AI agent
    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=openai_api_key,
        )

        agent = create_pandas_dataframe_agent(
            llm,
            df,
            verbose=False,  # Keep it quiet
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True,
            handle_parsing_errors=True,
            prefix="You are working with a pandas dataframe called `df` containing conversation data from a customer service chatbot. Provide clear, helpful answers to questions about this data.",
        )
    except Exception as e:
        st.error(f"❌ Failed to initialize AI agent: {str(e)}")
        return

    # Display existing chat history first (oldest to newest)
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

    # Chat input at the bottom
    user_query = st.chat_input("Ask a question about your conversation data...")

    if user_query:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_query})

        # Display user message
        with st.chat_message("user"):
            st.write(user_query)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    response = agent.invoke(user_query)
                    
                    # Extract the answer
                    if isinstance(response, dict):
                        if "output" in response:
                            ai_response = response["output"]
                        elif "result" in response:
                            ai_response = response["result"]
                        else:
                            ai_response = str(response)
                    else:
                        ai_response = str(response)

                    # Display the response
                    st.write(ai_response)
                    
                    # Add to history
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": ai_response}
                    )

                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_message)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": error_message}
                    )

    # Add a subtle clear chat button at the bottom
    if st.session_state.chat_history:
        st.write("")  # Add some space
        if st.button("🗑️ Clear Conversation", type="secondary", help="Clear chat history"):
            st.session_state.chat_history = []
            st.rerun()
