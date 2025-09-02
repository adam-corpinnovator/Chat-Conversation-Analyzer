# Layla AI Chat Analyzer

A **secure** Streamlit dashboard for analyzing conversations from a beauty AI assistant MVP. This tool helps you explore, filter, and visualize chat data, with a focus on thread-level exploration and actionable analytics.

## 🔐 Authentication & Security

**NEW**: The dashboard now includes complete user authentication and management:

- **Secure Login**: Username/password authentication with session management
- **User Roles**: Admin and user role-based access control
- **Profile Management**: Users can update their details and change passwords
- **Admin Features**: User registration and management capabilities

## Features

- **Thread Explorer**:

  - Filter and search conversations by date, region, time, and keywords
  - View full chat threads in a chat-like format
  - Translate Arabic messages to English on demand

- **Analytics Dashboard**:

  - Key metrics: total conversations, messages, user/assistant breakdown, language stats, error/empty responses, and more
  - Conversation length analysis (average, median, distribution)
  - Longest/shortest conversations
  - Daily chat and message trends
  - Region and role breakdowns (pie charts and tables)
  - Simple sentiment detection (happy/frustrated user messages)

- **🤖 Intelligence Chat (NEW)**:
  - Chat with your conversation data using AI
  - Ask natural language questions about your data
  - Get insights, statistics, and analysis through conversation
  - Example queries: "How many conversations happened this month?", "What are the most common user questions?"

## Hosting

The dashboard is hosted at: [https://layla-conversation-dashboard.streamlit.app/](https://layla-conversation-dashboard.streamlit.app/)

## Setup

1. **Clone or download this repo**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up OpenAI API Key (for Intelligence Chat)**:

   For the AI chat feature, you'll need an OpenAI API key:

   **Option 1: Environment Variable**

   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

   **Option 2: Streamlit Secrets**
   Create `.streamlit/secrets.toml`:

   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

4. **Place your CSV data** (e.g. `layla_export_2025-07-07.csv`) in the project folder

5. **Run the dashboard**:
   ```bash
   streamlit run app.py
   ```
6. **Login** using one of the demo accounts above or create your own

## Authentication Setup

**Quick Start:**

- The app will prompt for login on first access
- Use accounts for testing
- All user data is stored securely in `config.yaml`

## Data Format

The CSV should have columns:

- `thread_id`, `timestamp`, `role`, `message`, `region`, (optional extra column)

## Customization

- Update the `load_data()` function if your CSV format changes
- Adjust metrics or add new analytics in `app.py` as needed

## Notes

- Translation uses [deep-translator](https://github.com/nidhaloff/deep-translator) (Google Translate)
- The dashboard is designed for both light and dark mode
- For large CSVs, initial load may take a few seconds
