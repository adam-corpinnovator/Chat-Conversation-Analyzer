"""
Latency (Assistant Response Time) analysis for the Layla Conversation Analyzer
"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from datetime import timedelta
import json
from deep_translator import GoogleTranslator


def _compute_assistant_latencies(df: pd.DataFrame) -> pd.DataFrame:
    """Compute latency from each user message to the next assistant reply within a thread.

    Returns a DataFrame with one row per assistant message that has a preceding user message in the same thread.
    Columns: thread_id, region, user_timestamp, assistant_timestamp, latency_seconds, latency_timedelta,
             user_message, assistant_message, user_char_len, user_word_len, assistant_char_len
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "thread_id",
                "region",
                "user_timestamp",
                "assistant_timestamp",
                "latency_seconds",
                "latency_timedelta",
                "user_message",
                "assistant_message",
                "user_char_len",
                "user_word_len",
                "assistant_char_len",
            ]
        )

    # Ensure proper types
    df = df.copy()
    if not np.issubdtype(df["timestamp"].dtype, np.datetime64):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Keep only the needed columns
    expected_cols = {"thread_id", "timestamp", "role", "message", "region"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for latency analysis: {missing}")

    # Sort per thread
    df = df.sort_values(["thread_id", "timestamp"]).reset_index(drop=True)

    rows = []
    for thread_id, g in df.groupby("thread_id", sort=False):
        last_user_ts = None
        last_user_msg = None
        region = g["region"].iloc[0] if "region" in g.columns else "Unknown"
        for _, r in g.iterrows():
            role = r["role"]
            ts = r["timestamp"]
            msg = r["message"]

            if role == "user":
                last_user_ts = ts
                last_user_msg = msg
            elif role == "assistant":
                if last_user_ts is not None and pd.notna(last_user_ts) and pd.notna(ts):
                    delta = ts - last_user_ts
                    # Only consider positive deltas up to a reasonable cap (e.g., 24h) to avoid data issues
                    if delta.total_seconds() >= 0 and delta <= timedelta(hours=24):
                        rows.append(
                            {
                                "thread_id": thread_id,
                                "region": region,
                                "user_timestamp": last_user_ts,
                                "assistant_timestamp": ts,
                                "latency_seconds": delta.total_seconds(),
                                "latency_timedelta": delta,
                                "user_message": str(last_user_msg) if last_user_msg is not None else "",
                                "assistant_message": str(msg) if msg is not None else "",
                                "user_char_len": len(str(last_user_msg)) if last_user_msg is not None else 0,
                                "user_word_len": len(str(last_user_msg).split()) if last_user_msg is not None else 0,
                                "assistant_char_len": len(str(msg)) if msg is not None else 0,
                            }
                        )
                # Do not reset last_user_ts; multiple assistant messages may respond to the same prompt

    return pd.DataFrame(rows)


def _format_seconds(s: float) -> str:
    try:
        s = float(s)
    except Exception:
        return "-"
    if s < 1:
        return f"{s*1000:.0f} ms"
    if s < 60:
        return f"{s:.2f} s"
    # minutes and seconds
    mins, secs = divmod(int(round(s)), 60)
    if mins < 60:
        return f"{mins}m {secs}s"
    hours, mins = divmod(mins, 60)
    return f"{hours}h {mins}m {secs}s"


# Helpers for cleaning and translation

def _clean_assistant_message(msg) -> str:
    """Extract a readable text from assistant message.
    If JSON, prefer the 'response_text' field; otherwise return the raw string.
    """
    if msg is None:
        return ""
    try:
        # If it's already a dict-like JSON string, parse it
        obj = json.loads(str(msg))
        if isinstance(obj, dict):
            # Prefer common text fields
            if obj.get("response_text"):
                return str(obj["response_text"]).strip()
            # Fallback: join all short text-like values
            texts = []
            for k, v in obj.items():
                if isinstance(v, str) and len(v) > 0:
                    texts.append(v)
            if texts:
                return "\n\n".join(texts).strip()
        # If it's a list or something else, just stringify
        return str(obj)
    except Exception:
        # Not JSON, return as-is
        return str(msg)


def _get_translator():
    """Create or reuse a translator that auto-detects source language and translates to English."""
    key = "_latency_translator_en"
    if key not in st.session_state:
        try:
            st.session_state[key] = GoogleTranslator(source="auto", target="en")
        except Exception:
            st.session_state[key] = None
    return st.session_state[key]


def _get_translation_cache():
    """A simple in-memory cache for translations in this session."""
    key = "_latency_translation_cache"
    if key not in st.session_state:
        st.session_state[key] = {}
    return st.session_state[key]


def _translate_series(series: pd.Series, enabled: bool) -> pd.Series:
    if not enabled:
        return series
    translator = _get_translator()
    if translator is None:
        return series
    cache = _get_translation_cache()

    def _t(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return x
        s = str(x)
        if not s.strip():
            return s
        if s in cache:
            return cache[s]
        try:
            translated = translator.translate(s)
            cache[s] = translated
            return translated
        except Exception:
            return s

    return series.apply(_t)


def _translate_text(s: str, enabled: bool) -> str:
    if not enabled or not s:
        return s
    translator = _get_translator()
    if translator is None:
        return s
    cache = _get_translation_cache()
    if s in cache:
        return cache[s]
    try:
        translated = translator.translate(str(s))
        cache[s] = translated
        return translated
    except Exception as e:
        st.warning(f"Translation failed: {e}")
        return s


def show_latency_dashboard(df: pd.DataFrame):
    """Display the Response Latency dashboard tab."""
    st.header("⚡ Response Latency")

    if df is None or df.empty:
        st.warning("No data available to analyze.")
        return

    # Short explainer for non-technical readers
    st.info(
        "Latency here means the time from a user's message to the assistant's next reply in the same thread. "
        "All metrics and charts below use this definition. Lower latency = faster assistant replies."
    )

    # Global filters for this tab
    colf1, colf2, colf3, colf4 = st.columns([2, 2, 2, 2])
    with colf1:
        # Date range based on dataset
        min_ts = df["timestamp"].min().date()
        max_ts = df["timestamp"].max().date()
        date_range = st.date_input(
            "Date range",
            value=(min_ts, max_ts),
            min_value=min_ts,
            max_value=max_ts,
            key="latency_date_range",
        )
    with colf2:
        regions = ["All"] + sorted([r for r in df["region"].dropna().unique()])
        region_filter = st.selectbox("Region", regions, key="latency_region")
    with colf3:
        critical_threshold_s = st.number_input(
            "Critical latency threshold (seconds)",
            min_value=1,
            max_value=3600,
            value=30,
            step=1,
            help="Assistant replies slower than this are flagged as critical.",
            key="latency_critical_threshold",
        )
    with colf4:
        show_advanced = st.checkbox("Show advanced charts", value=True, key="latency_show_advanced")

    # Global display options
    cold1, cold2 = st.columns([2, 2])
    with cold1:
        translate_enabled = st.checkbox("Translate messages to English", value=False, key="latency_translate_en_all")
    with cold2:
        clean_json_enabled = st.checkbox("Clean assistant JSON to plain text", value=True, key="latency_clean_json_all")

    # Apply filters
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_f = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)].copy()
    else:
        df_f = df.copy()

    if region_filter != "All":
        df_f = df_f[df_f["region"] == region_filter]

    # Compute latencies
    lat_df = _compute_assistant_latencies(df_f)

    if lat_df.empty:
        st.info("No assistant replies found to compute latency.")
        return

    # Prepare cleaned assistant message column (for display)
    if clean_json_enabled:
        lat_df["assistant_message_clean"] = lat_df["assistant_message"].apply(_clean_assistant_message)
    else:
        lat_df["assistant_message_clean"] = lat_df["assistant_message"].astype(str)

    # Key metrics
    avg_s = lat_df["latency_seconds"].mean()
    median_s = lat_df["latency_seconds"].median()
    p95_s = lat_df["latency_seconds"].quantile(0.95)
    min_row = lat_df.loc[lat_df["latency_seconds"].idxmin()]
    max_row = lat_df.loc[lat_df["latency_seconds"].idxmax()]

    colm1, colm2, colm3, colm4 = st.columns(4)
    with colm1:
        st.metric("Average time per answer", _format_seconds(avg_s))
    with colm2:
        st.metric("Median time per answer", _format_seconds(median_s))
    with colm3:
        st.metric("95th percentile", _format_seconds(p95_s))
    with colm4:
        st.metric("Total answers analyzed", f"{len(lat_df):,}")

    # Longest and shortest
    st.subheader("Extremes")
    colx1, colx2 = st.columns(2)
    with colx1:
        st.markdown("**Longest time to answer**")
        st.write(_format_seconds(max_row["latency_seconds"]))
        st.caption(f"Thread: {max_row['thread_id']} | {max_row['assistant_timestamp']}")
        st.markdown(
            f"- User: {str(max_row['user_message'])[:500]}\n\n- Assistant: {str(max_row['assistant_message'])[:500]}"
        )
    with colx2:
        st.markdown("**Shortest time to answer**")
        st.write(_format_seconds(min_row["latency_seconds"]))
        st.caption(f"Thread: {min_row['thread_id']} | {min_row['assistant_timestamp']}")
        st.markdown(
            f"- User: {str(min_row['user_message'])[:500]}\n\n- Assistant: {str(min_row['assistant_message'])[:500]}"
        )

    st.divider()

    # Slow replies explorer (merged: Critical cases + Longest prompts)
    st.subheader("Slow replies explorer")
    st.markdown(
        "This table helps you find and inspect the slowest assistant replies. "
        "Use the filters to either: (a) strictly show only replies slower than your critical threshold, or (b) simply rank by latency. "
        "You can also search within the user's prompt, pick columns to display, and limit the number of rows to keep things fast."
    )

    # Controls
    colsr1, colsr2, colsr3, colsr4 = st.columns([2, 1, 1, 1])
    with colsr1:
        slow_search = st.text_input("Search in user prompt", key="latency_slow_search")
    with colsr2:
        slow_min_latency = st.number_input(
            "Min latency (s)", value=max(critical_threshold_s, 5), min_value=0, step=1, key="latency_slow_min_latency"
        )
    with colsr3:
        slow_only_critical = st.checkbox(
            "Only show ≥ critical threshold", value=True, key="latency_slow_only_critical"
        )
    with colsr4:
        slow_top_n = st.number_input("Rows to show", min_value=10, max_value=1000, value=100, step=10, key="latency_slow_top_n")

    st.markdown("Choose columns to show:")
    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        sopt_region = st.checkbox("Region", value=True, key="latency_slow_opt_region")
        sopt_user_ts = st.checkbox("User timestamp", value=True, key="latency_slow_opt_user_ts")
    with scol2:
        sopt_assistant_ts = st.checkbox("Assistant timestamp", value=False, key="latency_slow_opt_assistant_ts")
        sopt_user_len = st.checkbox("User word count", value=False, key="latency_slow_opt_user_len")
    with scol3:
        sopt_user_msg = st.checkbox("User message", value=True, key="latency_slow_opt_user_msg")
        sopt_assistant_msg = st.checkbox("Assistant message", value=True, key="latency_slow_opt_assistant_msg")

    # Build unified filtered dataframe
    slow_df = lat_df.copy()
    if slow_only_critical:
        slow_df = slow_df[slow_df["latency_seconds"] >= float(critical_threshold_s)]
    if slow_min_latency and float(slow_min_latency) > 0:
        slow_df = slow_df[slow_df["latency_seconds"] >= float(slow_min_latency)]
    if slow_search:
        slow_df = slow_df[slow_df["user_message"].str.contains(str(slow_search), case=False, na=False)]

    if slow_df.empty:
        st.info("No rows match the current filters.")
    else:
        display_cols = ["latency", "thread_id"]
        if sopt_region:
            display_cols.append("region")
        if sopt_user_ts:
            display_cols.append("user_timestamp")
        if sopt_assistant_ts:
            display_cols.append("assistant_timestamp")
        if sopt_user_len:
            display_cols.append("user_word_len")
        if sopt_user_msg:
            display_cols.append("user_message")
        if sopt_assistant_msg:
            display_cols.append("assistant_message_clean")

        slow_display = (
            slow_df.assign(latency=lambda d: d["latency_seconds"].map(_format_seconds))
            .sort_values("latency_seconds", ascending=False)
            .head(int(slow_top_n))
            .loc[:, display_cols]
            .rename(
                columns={
                    "latency": "Latency",
                    "thread_id": "Thread",
                    "region": "Region",
                    "user_timestamp": "User time",
                    "assistant_timestamp": "Assistant time",
                    "user_word_len": "User words",
                    "user_message": "User message",
                    "assistant_message_clean": "Assistant message",
                }
            )
        )

        # Translate only the displayed rows (if enabled)
        if translate_enabled:
            if "User message" in slow_display.columns:
                slow_display["User message"] = _translate_series(slow_display["User message"], True)
            if "Assistant message" in slow_display.columns:
                slow_display["Assistant message"] = _translate_series(slow_display["Assistant message"], True)

        st.dataframe(slow_display, use_container_width=True, hide_index=True)
        st.caption(
            "Latency = time from user message to next assistant reply. "
            "If the toggle is on, only replies slower than your critical threshold are shown; otherwise it's just the slowest replies."
        )

    # Distribution & Trends
    if show_advanced:
        st.divider()
        st.subheader("Latency distribution and trends")
        colc1, colc2 = st.columns(2)
        with colc1:
            fig = px.histogram(lat_df, x="latency_seconds", nbins=30, title="Latency distribution (seconds)")
            fig.update_layout(height=350, bargap=0.05)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Histogram: how many replies fall into each latency range. A long right tail indicates slow outliers.")
        with colc2:
            lat_df["date"] = lat_df["assistant_timestamp"].dt.date
            daily = lat_df.groupby("date")["latency_seconds"].agg(["count", "mean", "median"]).reset_index()
            fig2 = px.line(
                daily,
                x="date",
                y=["mean", "median"],
                markers=True,
                title="Daily average and median latency",
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("Trend: average (mean) and typical (median) latency per day. A gap between mean and median suggests outliers.")

    st.divider()

    # Response time vs. conversation length (with outlier handling and explanation)
    st.subheader("Response time vs. conversation length")
    st.markdown(
        "This chart checks if longer conversations tend to have slower or faster replies. "
        "Each dot is one conversation (thread). The correlation number summarizes the linear relationship: "
        "-1 = strong negative (faster replies with longer chats), 0 = no clear link, +1 = strong positive."
    )

    # Per thread metrics
    per_thread_counts = df_f.groupby("thread_id").size().rename("messages_count").reset_index()
    per_thread_assistant_lat = (
        lat_df.groupby("thread_id")["latency_seconds"].mean().rename("avg_latency_seconds").reset_index()
    )
    per_thread = per_thread_counts.merge(per_thread_assistant_lat, on="thread_id", how="left")
    per_thread = per_thread.dropna(subset=["avg_latency_seconds"])  # keep threads with at least one assistant reply

    if per_thread.empty:
        st.info("Not enough data to compute per-thread correlation.")
        return

    col_out1, col_out2 = st.columns([2, 2])
    with col_out1:
        exclude_outliers = st.checkbox("Exclude latency outliers (IQR)", value=True, key="latency_corr_exclude_outliers")
    with col_out2:
        st.caption("Outliers are points outside 1.5×IQR for average latency.")

    plot_df = per_thread.copy()
    removed = 0
    if exclude_outliers and not plot_df.empty:
        q1 = plot_df["avg_latency_seconds"].quantile(0.25)
        q3 = plot_df["avg_latency_seconds"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (plot_df["avg_latency_seconds"] >= lower) & (plot_df["avg_latency_seconds"] <= upper)
        removed = int((~mask).sum())
        plot_df = plot_df[mask]

    if plot_df.empty:
        st.info("All points considered outliers under current rule. Try turning off the outlier filter.")
        return

    corr = plot_df[["messages_count", "avg_latency_seconds"]].corr().iloc[0, 1]

    colr1, colr2 = st.columns([3, 1])
    with colr1:
        fig3 = px.scatter(
            plot_df,
            x="messages_count",
            y="avg_latency_seconds",
            hover_name="thread_id",
            title="Avg latency (s) vs messages per conversation",
            opacity=0.7,
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.caption(
            f"Using {len(plot_df)} conversations (removed {removed} outliers). "
            "A downward pattern suggests faster replies correlate with longer conversations."
        )
    with colr2:
        st.metric("Pearson correlation", f"{corr:.3f}")
        st.caption("Closer to -1 or +1 means a stronger relationship. Values near 0 mean little to no linear relationship.")

    # Download helper
    st.download_button(
        label="📥 Download per-answer latency CSV",
        data=lat_df.drop(columns=["latency_timedelta"]).to_csv(index=False),
        file_name="assistant_latency_per_answer.csv",
        mime="text/csv",
    )
