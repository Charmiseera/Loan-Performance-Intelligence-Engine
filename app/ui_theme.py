import streamlit as st


def apply_theme():
    """Inject clean institutional typography without breaking native contrast or alert readability."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            letter-spacing: -0.01em;
        }

        /* Metric cards styling */
        [data-testid="stMetric"] {
            background-color: var(--secondary-background-color, rgba(128, 128, 128, 0.08));
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.65rem !important;
            font-weight: 700 !important;
        }

        /* Fix all Alert callouts (Success, Info, Warning, Error) for 100% visible text */
        div[data-testid="stAlert"] {
            border-radius: 8px !important;
        }
        
        /* Success alert text contrast fix */
        div[data-testid="stAlert"]:has([data-testid="stNotificationIconSuccess"]),
        div[data-testid="stAlert"]:has([data-testid="stAlertIconSuccess"]) {
            background-color: rgba(34, 197, 94, 0.15) !important;
            border: 1px solid rgba(34, 197, 94, 0.4) !important;
        }
        div[data-testid="stAlert"]:has([data-testid="stNotificationIconSuccess"]) p,
        div[data-testid="stAlert"]:has([data-testid="stAlertIconSuccess"]) p {
            color: var(--text-color, #166534) !important;
            font-weight: 500 !important;
        }

        /* Section headers */
        h1 {
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
            margin-bottom: 0.25rem !important;
        }
        h2, h3, h4 {
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        }
        .stTabs [data-baseweb="tab"] {
            height: 38px;
            padding: 0 16px;
            font-size: 0.85rem;
            font-weight: 500;
            border-radius: 6px 6px 0 0;
        }

        /* Dataframe border */
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
