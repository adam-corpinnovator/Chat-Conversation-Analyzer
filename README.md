# Beauty AI Chat Analyzer

A Streamlit dashboard for analyzing conversations from a beauty AI assistant MVP. This tool helps you explore, filter, and visualize chat data, with a focus on thread-level exploration and actionable analytics.

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

## Hosting

The dashboard is hosted at: [https://layla-conversation-dashboard.streamlit.app/](https://layla-conversation-dashboard.streamlit.app/)

## Setup

1. **Clone or download this repo**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Place your CSV data** (e.g. `layla_export_2025-07-07.csv`) in the project folder
4. **Run the dashboard**:
   ```bash
   streamlit run app.py
   ```

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

