"""
diagnose.py — Systematically test every import in app.py
Mocks streamlit so it doesn't block. Reports exactly which import fails or hangs.
Run: venv\Scripts\python.exe diagnose.py
"""
import sys, os, time, importlib, traceback

sys.path.insert(0, os.getcwd())

# ── Mock heavy packages before anything else ──────────────────────────────────
from unittest.mock import MagicMock, patch

# Mock streamlit entirely
st_mock = MagicMock()
st_mock.session_state = {}
st_mock.cache_resource = lambda **kw: (lambda f: f)
st_mock.secrets = MagicMock()
sys.modules['streamlit'] = st_mock
sys.modules['streamlit.components'] = MagicMock()
sys.modules['streamlit.components.v1'] = MagicMock()

GREEN = "\033[92m"
RED   = "\033[91m"
RESET = "\033[0m"
WARN  = "\033[93m"

def test(label, fn):
    t0 = time.time()
    try:
        fn()
        elapsed = time.time() - t0
        print(f"{GREEN}OK{RESET}   {label:<55} ({elapsed:.2f}s)")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"{RED}ERR{RESET}  {label:<55} ({elapsed:.2f}s)")
        print(f"      {type(e).__name__}: {e}")
        traceback.print_exc()
        print()

print("\n" + "=" * 70)
print("Synapse AI Tutor — Import Diagnostics")
print("=" * 70 + "\n")

# ── config + core ─────────────────────────────────────────────────────────────
test("config.settings",        lambda: importlib.import_module("config.settings"))
test("config.logging_config",  lambda: importlib.import_module("config.logging_config"))
test("core.exceptions",        lambda: importlib.import_module("core.exceptions"))
test("core.types",             lambda: importlib.import_module("core.types"))
test("core.constants",         lambda: importlib.import_module("core.constants"))

# ── backend (lightweight) ─────────────────────────────────────────────────────
test("backend.auth",              lambda: importlib.import_module("backend.auth"))
test("backend.progress_tracker",  lambda: importlib.import_module("backend.progress_tracker"))
test("backend.gap_detector",      lambda: importlib.import_module("backend.gap_detector"))
test("backend.note_generator",    lambda: importlib.import_module("backend.note_generator"))
test("backend.roadmap_generator", lambda: importlib.import_module("backend.roadmap_generator"))
test("backend.assessment",        lambda: importlib.import_module("backend.assessment"))
test("backend.knowledge_graph",   lambda: importlib.import_module("backend.knowledge_graph"))
test("backend.student_memory",    lambda: importlib.import_module("backend.student_memory"))
test("backend.voice_config",      lambda: importlib.import_module("backend.voice_config"))

# ── voice (may need to mock more) ─────────────────────────────────────────────
test("backend.voice_components",  lambda: importlib.import_module("backend.voice_components"))

# ── llm client ────────────────────────────────────────────────────────────────
test("backend.llm_client",        lambda: importlib.import_module("backend.llm_client"))

# ── ui ────────────────────────────────────────────────────────────────────────
test("ui.theme",       lambda: importlib.import_module("ui.theme"))
test("ui.styles",      lambda: importlib.import_module("ui.styles"))
test("ui.navigation",  lambda: importlib.import_module("ui.navigation"))

# ── services ──────────────────────────────────────────────────────────────────
test("services.auth_service",    lambda: importlib.import_module("services.auth_service"))
test("services.memory_service",  lambda: importlib.import_module("services.memory_service"))

# ── pages ─────────────────────────────────────────────────────────────────────
pages = [
    "pages.login",
    "pages.topic_selection",
    "pages.assessment",
    "pages.tutor",
    "pages.dashboard",
    "pages.roadmap",
    "pages.note_viewer",
    "pages.knowledge_vault",
    "pages.knowledge_graph_page",
    "pages.chatbot",
    "pages.visualizer",
    "pages.resources",
    "pages.profile",
    "pages.home",
]

for p in pages:
    test(p, lambda m=p: importlib.import_module(m))

print("\n" + "=" * 70)
print("Diagnostics complete")
print("=" * 70 + "\n")
