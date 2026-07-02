"""
Global CSS design system for Synapse AI Tutor.
Extracted from app.py for independent maintenance.

Contains:
- Design tokens (light + dark themes)
- Component styles (buttons, cards, forms, chat, etc.)
- Streamlit chrome overrides
- Animations
- Focus mode styles
"""

from __future__ import annotations

import streamlit as st

from ui.theme import get_current_theme, get_fouc_prevention_js


def inject_global_styles() -> None:
    """
    Inject the complete design system CSS into the Streamlit page.
    Must be called once per page render, after st.set_page_config().
    """
    theme = get_current_theme()
    focus_mode = st.session_state.get("focus_mode", False)

    focus_css = ""
    if focus_mode:
        focus_css = """
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
        .block-container { max-width: 1100px !important; padding-top: 2rem !important; }
        """

    fouc_js = get_fouc_prevention_js(theme)

    css = f"""
{fouc_js}
<style>
/* ================================================================
   FONT IMPORT
================================================================ */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

/* ================================================================
   DESIGN TOKENS  — Light (default)
================================================================ */
:root, [data-theme="light"] {{
  /* Brand */
  --primary:        #2563EB;
  --primary-dark:   #1D4ED8;
  --primary-light:  #93C5FD;
  --primary-alpha:  rgba(37,99,235,0.07);

  /* Semantic */
  --success: #059669;
  --warning: #D97706;
  --danger:  #DC2626;
  --info:    #0284C7;

  /* Surfaces */
  --bg-page:     #F1F5F9;
  --bg-surface:  #FFFFFF;
  --bg-elevated: #FFFFFF;
  --bg-sunken:   #F8FAFC;

  /* Text — WCAG AA contrast on surfaces */
  --text-primary:   #0F172A;
  --text-secondary: #334155;
  --text-muted:     #64748B;
  --text-disabled:  #94A3B8;
  --text-on-primary: #FFFFFF;

  /* Borders */
  --border:        #CBD5E1;
  --border-light:  #E2E8F0;
  --border-strong: #94A3B8;

  /* Shadows */
  --shadow-xs:  0 1px 2px rgba(0,0,0,0.05);
  --shadow-sm:  0 2px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:  0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg:  0 12px 24px rgba(0,0,0,0.10), 0 4px 8px rgba(0,0,0,0.06);
  --shadow-focus: 0 0 0 3px rgba(37,99,235,0.25);

  /* Sidebar-specific */
  --sidebar-bg:     #FFFFFF;
  --sidebar-border: #E2E8F0;
}}

/* ================================================================
   DESIGN TOKENS  — Dark
================================================================ */
[data-theme="dark"] {{
  --primary:        #6366F1;
  --primary-dark:   #4F46E5;
  --primary-light:  #A5B4FC;
  --primary-alpha:  rgba(99,102,241,0.12);

  --success: #10B981;
  --warning: #F59E0B;
  --danger:  #F87171;
  --info:    #38BDF8;

  --bg-page:     #0C1120;
  --bg-surface:  #141C2E;
  --bg-elevated: #1C2640;
  --bg-sunken:   #090E1A;

  --text-primary:   #F1F5F9;
  --text-secondary: #CBD5E1;
  --text-muted:     #94A3B8;
  --text-disabled:  #475569;
  --text-on-primary: #FFFFFF;

  --border:        #1E293B;
  --border-light:  #243049;
  --border-strong: #334155;

  --shadow-xs:  0 1px 3px rgba(0,0,0,0.4);
  --shadow-sm:  0 2px 6px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md:  0 6px 18px rgba(0,0,0,0.55), 0 2px 4px rgba(0,0,0,0.3);
  --shadow-lg:  0 14px 34px rgba(0,0,0,0.65), 0 4px 8px rgba(0,0,0,0.4);
  --shadow-focus: 0 0 0 3px rgba(99,102,241,0.35);

  --sidebar-bg:     #0F1929;
  --sidebar-border: #1E293B;
}}

/* ================================================================
   SHARED TOKENS (theme-independent)
================================================================ */
:root {{
  --radius-xs:   6px;
  --radius-sm:  10px;
  --radius-md:  14px;
  --radius-lg:  20px;
  --radius-pill: 9999px;

  --t-fast:   120ms cubic-bezier(0.4,0,0.2,1);
  --t-base:   220ms cubic-bezier(0.4,0,0.2,1);
  --t-slow:   360ms cubic-bezier(0.16,1,0.3,1);
}}

/* ================================================================
   GLOBAL RESETS
================================================================ */
*, *::before, *::after {{ box-sizing: border-box; }}

html, body, .stApp {{
  background: var(--bg-page) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  transition: background-color var(--t-slow), color var(--t-base) !important;
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: 'Outfit', sans-serif !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.025em;
  line-height: 1.25;
}}

/* All markdown/text content */
p, li,
.stMarkdown p, .stMarkdown li, .stMarkdown span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {{
  color: var(--text-primary) !important;
  line-height: 1.65;
}}

/* Form labels */
label, [data-testid="stWidgetLabel"] > div,
[data-testid="stWidgetLabel"] > label {{
  color: var(--text-secondary) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
}}

/* Code blocks */
code {{
  background: var(--bg-sunken) !important;
  color: var(--primary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-xs) !important;
  padding: 0.1em 0.4em !important;
  font-size: 0.875em !important;
}}

/* ================================================================
   STREAMLIT CHROME — hide & neutralise
================================================================ */
#MainMenu {{ visibility: hidden !important; height: 0 !important; }}
footer     {{ visibility: hidden !important; height: 0 !important; }}
header[data-testid="stHeader"] {{
  background: transparent !important;
  box-shadow: none !important;
}}
.block-container {{
  padding-top: 1.5rem !important;
  padding-bottom: 3rem !important;
  max-width: 1200px;
}}

/* ================================================================
   SIDEBAR
================================================================ */
[data-testid="stSidebar"] {{
  background: var(--sidebar-bg) !important;
  border-right: 1px solid var(--sidebar-border) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: background var(--t-slow), border-color var(--t-base) !important;
}}
[data-testid="stSidebar"] > div:first-child {{
  padding-top: 1rem !important;
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not([data-testid]),
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
  color: var(--text-primary) !important;
}}
/* Sidebar section headings */
[data-testid="stSidebar"] h4 {{
  color: var(--text-muted) !important;
  font-size: 0.62rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.12em !important;
  margin: 1.25rem 0 0.35rem 0.1rem !important;
  padding: 0 !important;
}}

/* ================================================================
   BUTTONS
================================================================ */
/* Primary */
div.stButton > button[kind="primary"],
div.stFormSubmitButton > button {{
  background: var(--primary) !important;
  color: var(--text-on-primary) !important;
  border: 1px solid transparent !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.875rem !important;
  font-weight: 600 !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.55rem 1.35rem !important;
  box-shadow: var(--shadow-xs) !important;
  letter-spacing: 0.01em !important;
  transition: background var(--t-fast), transform var(--t-fast), box-shadow var(--t-fast) !important;
}}
div.stButton > button[kind="primary"]:hover,
div.stFormSubmitButton > button:hover {{
  background: var(--primary-dark) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow-md) !important;
}}
div.stButton > button[kind="primary"]:active {{
  transform: scale(0.98) !important;
  box-shadow: var(--shadow-xs) !important;
}}
div.stButton > button[kind="primary"]:focus-visible {{
  outline: none !important;
  box-shadow: var(--shadow-focus) !important;
}}

/* Secondary / default */
div.stButton > button[kind="secondary"],
div.stButton > button:not([kind]) {{
  background: transparent !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.55rem 1.35rem !important;
  transition: background var(--t-fast), border-color var(--t-fast), transform var(--t-fast) !important;
}}
div.stButton > button[kind="secondary"]:hover {{
  background: var(--bg-sunken) !important;
  border-color: var(--border-strong) !important;
  transform: translateY(-1px) !important;
}}
div.stButton > button[kind="secondary"]:active {{ transform: scale(0.98) !important; }}
div.stButton > button[kind="secondary"]:focus-visible {{
  outline: none !important;
  box-shadow: var(--shadow-focus) !important;
}}

/* ================================================================
   FORM INPUTS
================================================================ */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  transition: border-color var(--t-fast), box-shadow var(--t-fast) !important;
}}
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within {{
  border-color: var(--primary) !important;
  box-shadow: var(--shadow-focus) !important;
}}
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {{
  color: var(--text-primary) !important;
  background: transparent !important;
  font-family: 'Inter', sans-serif !important;
  caret-color: var(--primary) !important;
}}
input::placeholder, textarea::placeholder {{ color: var(--text-muted) !important; }}

/* SELECT */
div[data-baseweb="select"] > div {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  transition: border-color var(--t-fast) !important;
}}
div[data-baseweb="select"] > div:focus-within {{
  border-color: var(--primary) !important;
  box-shadow: var(--shadow-focus) !important;
}}
div[data-baseweb="select"] * {{ color: var(--text-primary) !important; }}
ul[data-baseweb="menu"] {{
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  box-shadow: var(--shadow-lg) !important;
}}
li[data-baseweb="menu-item"] {{
  color: var(--text-primary) !important;
  background: transparent !important;
  transition: background var(--t-fast) !important;
}}
li[data-baseweb="menu-item"]:hover {{ background: var(--primary-alpha) !important; }}

/* ================================================================
   CHAT
================================================================ */
[data-testid="stChatInput"] > div {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-pill) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: border-color var(--t-fast), box-shadow var(--t-fast) !important;
}}
[data-testid="stChatInput"] > div:focus-within {{
  border-color: var(--primary) !important;
  box-shadow: var(--shadow-focus) !important;
}}
[data-testid="stChatInput"] textarea {{
  color: var(--text-primary) !important;
  font-family: 'Inter', sans-serif !important;
  background: transparent !important;
}}

div[data-testid="stChatMessage"] {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem 1.25rem !important;
  margin-bottom: 0.875rem !important;
  box-shadow: var(--shadow-xs) !important;
  transition: background var(--t-base), border-color var(--t-base) !important;
}}
div[data-testid="stChatMessage"][data-is-user="true"] {{
  background: var(--bg-sunken) !important;
  border-color: var(--border) !important;
}}
div[data-testid="stChatMessage"] p {{
  color: var(--text-primary) !important;
  font-size: 0.9rem !important;
  line-height: 1.7 !important;
}}
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] {{
  background: var(--bg-elevated) !important;
  border: 1.5px solid var(--border) !important;
  color: var(--text-primary) !important;
  box-shadow: var(--shadow-xs) !important;
}}

/* ================================================================
   FILE UPLOADER
================================================================ */
section[data-testid="stFileUploader"] {{
  background: var(--bg-sunken) !important;
  border: 1.5px dashed var(--border) !important;
  border-radius: var(--radius-md) !important;
  transition: border-color var(--t-fast), background var(--t-fast) !important;
}}
section[data-testid="stFileUploader"]:hover {{
  border-color: var(--primary) !important;
  background: var(--primary-alpha) !important;
}}

/* ================================================================
   TABS
================================================================ */
[data-testid="stTabs"] [role="tablist"] {{
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}}
button[data-baseweb="tab"] {{
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  color: var(--text-muted) !important;
  border-bottom: 2px solid transparent !important;
  padding: 0.625rem 1.1rem 0.75rem !important;
  margin-bottom: -1px !important;
  border-radius: 0 !important;
  transition: color var(--t-fast), border-color var(--t-fast), background var(--t-fast) !important;
}}
button[data-baseweb="tab"]:hover {{
  color: var(--text-secondary) !important;
  background: var(--primary-alpha) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
  color: var(--primary) !important;
  border-bottom-color: var(--primary) !important;
  font-weight: 600 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {{
  padding-top: 1.25rem !important;
}}

/* ================================================================
   EXPANDERS
================================================================ */
[data-testid="stExpander"] {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  margin-bottom: 0.5rem !important;
  transition: background var(--t-base) !important;
}}
[data-testid="stExpander"] summary {{
  color: var(--text-primary) !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
}}
[data-testid="stExpander"] summary:hover {{ color: var(--primary) !important; }}

/* ================================================================
   METRICS
================================================================ */
[data-testid="stMetric"] {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-sm) !important;
  padding: 1rem !important;
  box-shadow: var(--shadow-xs) !important;
}}
[data-testid="stMetricLabel"] {{
  color: var(--text-muted) !important;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.07em !important;
}}
[data-testid="stMetricValue"] {{
  color: var(--text-primary) !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
}}

/* ================================================================
   RADIO BUTTONS
================================================================ */
[data-testid="stRadio"] label {{
  color: var(--text-primary) !important;
  font-size: 0.9rem !important;
  padding: 0.55rem 0.875rem !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-xs) !important;
  margin-bottom: 0.3rem !important;
  cursor: pointer !important;
  transition: background var(--t-fast), border-color var(--t-fast) !important;
  display: flex !important;
  align-items: center !important;
  background: var(--bg-surface) !important;
}}
[data-testid="stRadio"] label:hover {{
  background: var(--primary-alpha) !important;
  border-color: var(--primary-light) !important;
}}

/* Checkbox */
[data-testid="stCheckbox"] label {{ color: var(--text-primary) !important; }}

/* Progress bar */
[data-testid="stProgress"] > div {{
  background: var(--border) !important;
  border-radius: var(--radius-pill) !important;
}}
[data-testid="stProgress"] > div > div {{
  background: var(--primary) !important;
  border-radius: var(--radius-pill) !important;
}}

/* Slider */
[data-testid="stSlider"] [role="slider"] {{
  background: var(--primary) !important;
  border: 2px solid var(--bg-surface) !important;
  box-shadow: var(--shadow-sm) !important;
}}

/* ================================================================
   ALERTS / INFO / WARNING / ERROR
================================================================ */
div[data-testid="stAlert"] {{
  border-radius: var(--radius-sm) !important;
}}
div[data-testid="stNotification"] {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
}}

/* ================================================================
   CARD COMPONENTS
================================================================ */
.synapse-card {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-md) !important;
  padding: 1.5rem !important;
  margin-bottom: 1.25rem !important;
  box-shadow: var(--shadow-sm) !important;
  transition: transform var(--t-base), box-shadow var(--t-base), border-color var(--t-fast) !important;
}}
.synapse-card:hover {{
  transform: translateY(-2px) !important;
  box-shadow: var(--shadow-md) !important;
  border-color: var(--border) !important;
}}

.topic-card {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-md) !important;
  padding: 1.25rem 0.875rem !important;
  text-align: center !important;
  cursor: pointer !important;
  min-height: 155px !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: var(--shadow-sm) !important;
  transition: transform var(--t-base), box-shadow var(--t-base), border-color var(--t-fast) !important;
}}
.topic-card:hover {{
  transform: translateY(-3px) !important;
  box-shadow: var(--shadow-md) !important;
  border-color: var(--primary-light) !important;
}}
.topic-card .topic-name {{
  font-family: 'Outfit', sans-serif;
  font-size: 1rem; font-weight: 700;
  color: var(--text-primary); margin-bottom: 0.35rem;
}}
.topic-card .topic-desc {{
  font-size: 0.775rem; color: var(--text-secondary); line-height: 1.4;
}}

.stat-card {{
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-light) !important;
  border-radius: var(--radius-sm) !important;
  padding: 1.125rem 1rem !important;
  text-align: center !important;
  box-shadow: var(--shadow-xs) !important;
  transition: transform var(--t-base), box-shadow var(--t-base) !important;
}}
.stat-card:hover {{
  transform: translateY(-2px) !important;
  box-shadow: var(--shadow-sm) !important;
}}
.stat-value {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.875rem; font-weight: 800;
  color: var(--text-primary); letter-spacing: -0.03em;
}}
.stat-label {{
  font-size: 0.68rem; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;
  margin-top: 0.25rem;
}}
.stat-sub {{
  font-size: 0.66rem; color: var(--text-disabled); margin-top: 0.15rem;
}}

/* Gap / fallback banners */
.gap-warning {{
  background: rgba(217,119,6,0.06) !important;
  border-left: 3px solid var(--warning) !important;
  border-radius: 0 var(--radius-xs) var(--radius-xs) 0 !important;
  padding: 0.75rem 1rem !important;
  margin: 0.5rem 0 !important;
}}
.fallback-warning {{
  background: rgba(220,38,38,0.05) !important;
  border-left: 3px solid var(--danger) !important;
  border-radius: 0 var(--radius-xs) var(--radius-xs) 0 !important;
  padding: 0.75rem 1rem !important;
  margin: 0.5rem 0 !important;
}}

/* Source citations */
.source-citation {{
  background: var(--bg-sunken) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-xs) !important;
  padding: 0.5rem 0.875rem !important;
  margin-bottom: 0.35rem !important;
}}
.source-book {{ color: var(--primary) !important; font-weight: 600; font-size: 0.8rem; }}
.source-page {{ color: var(--text-muted) !important; font-size: 0.75rem; }}

/* ================================================================
   BADGES
================================================================ */
.badge {{
  display: inline-block; padding: 0.2rem 0.65rem;
  border-radius: var(--radius-pill); font-size: 0.68rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
  background: var(--bg-sunken); color: var(--text-secondary);
  border: 1px solid var(--border);
}}
.badge-beginner     {{ background: rgba(5,150,105,0.1)  !important; color: var(--success) !important; border-color: rgba(5,150,105,0.2)   !important; }}
.badge-intermediate {{ background: rgba(217,119,6,0.1)  !important; color: var(--warning) !important; border-color: rgba(217,119,6,0.25)  !important; }}
.badge-advanced     {{ background: rgba(220,38,38,0.1)  !important; color: var(--danger)  !important; border-color: rgba(220,38,38,0.2)   !important; }}

/* ================================================================
   TYPOGRAPHY UTILITIES
================================================================ */
.gradient-text {{ color: var(--primary) !important; font-weight: 800; }}
.text-muted     {{ color: var(--text-muted)     !important; }}
.text-secondary {{ color: var(--text-secondary) !important; }}

.main-header {{ text-align: center; padding: 1.75rem 0 1rem; }}
.main-header h1 {{ font-size: 2.4rem; font-weight: 800; margin-bottom: 0.4rem; }}
.main-header p  {{ color: var(--text-secondary); font-size: 1rem; }}

/* ================================================================
   DIVIDER & SCROLLBAR
================================================================ */
hr {{
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.5rem 0 !important;
}}

::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
  background: var(--border);
  border-radius: var(--radius-pill);
  transition: background var(--t-fast);
}}
::-webkit-scrollbar-thumb:hover {{ background: var(--border-strong); }}

/* ================================================================
   ANIMATIONS  (minimal, purposeful)
================================================================ */
@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
  from {{ opacity: 0; }}
  to   {{ opacity: 1; }}
}}
.animate-fade-in {{ animation: fadeInUp 0.3s cubic-bezier(0.16,1,0.3,1) both; }}
.animate-fade    {{ animation: fadeIn  0.2s ease both; }}

/* ================================================================
   FOCUS MODE
================================================================ */
{focus_css}

/* Plotly transparency */
.js-plotly-plot .plotly,
.plot-container {{ background: transparent !important; }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)
