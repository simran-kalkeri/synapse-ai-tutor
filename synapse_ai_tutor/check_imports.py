"""Quick script to find which import hangs — no streamlit needed."""
import sys, os, importlib, traceback

sys.path.insert(0, os.getcwd())

# We need to mock streamlit so it doesn't block
import unittest.mock as mock
sys.modules['streamlit'] = mock.MagicMock()

mods = [
    'backend.auth',
    'backend.progress_tracker',
    'backend.gap_detector',
    'backend.note_generator',
    'backend.roadmap_generator',
    'backend.llm_client',
    'backend.resources',
    'backend.voice_components',
    'backend.student_memory',
    'backend.assessment',
    'backend.embeddings',
    'backend.knowledge_graph',
    'backend.rag',
    'config.settings',
    'config.logging_config',
    'core.exceptions',
    'core.types',
    'core.constants',
    'ui.theme',
    'ui.styles',
    'ui.navigation',
    'services.auth_service',
    'services.memory_service',
]

for mod in mods:
    try:
        importlib.import_module(mod)
        print(f"OK  {mod}")
    except Exception as e:
        print(f"ERR {mod}: {type(e).__name__}: {e}")
        traceback.print_exc()
        print()
