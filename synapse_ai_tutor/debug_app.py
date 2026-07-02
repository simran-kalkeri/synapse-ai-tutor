"""Debug version of app.py — identifies which import hangs"""
import sys, os
print("DEBUG: Python started", flush=True)
sys.path.insert(0, os.path.dirname(__file__))
print("DEBUG: sys.path set", flush=True)

print("DEBUG: importing streamlit...", flush=True)
import streamlit as st
print("DEBUG: streamlit OK", flush=True)

print("DEBUG: importing pages.login...", flush=True)
from pages.login import render_login
print("DEBUG: login OK", flush=True)

print("DEBUG: importing pages.topic_selection...", flush=True)
from pages.topic_selection import render_topic_selection
print("DEBUG: topic_selection OK", flush=True)

print("DEBUG: importing pages.assessment...", flush=True)
from pages.assessment import render_assessment
print("DEBUG: assessment OK", flush=True)

print("DEBUG: importing pages.tutor...", flush=True)
from pages.tutor import render_tutor
print("DEBUG: tutor OK", flush=True)

print("DEBUG: importing pages.chatbot...", flush=True)
from pages.chatbot import render_chatbot
print("DEBUG: chatbot OK", flush=True)

print("DEBUG: importing pages.dashboard...", flush=True)
from pages.dashboard import render_dashboard
print("DEBUG: dashboard OK", flush=True)

print("DEBUG: importing pages.resources...", flush=True)
from pages.resources import render_resources
print("DEBUG: resources OK", flush=True)

print("DEBUG: importing pages.visualizer...", flush=True)
from pages.visualizer import render_visualizer
print("DEBUG: visualizer OK", flush=True)

print("DEBUG: importing pages.knowledge_graph_page...", flush=True)
from pages.knowledge_graph_page import render_knowledge_graph
print("DEBUG: knowledge_graph OK", flush=True)

print("DEBUG: importing pages.roadmap...", flush=True)
from pages.roadmap import render_roadmap
print("DEBUG: roadmap OK", flush=True)

print("DEBUG: importing pages.note_viewer...", flush=True)
from pages.note_viewer import render_note_viewer
print("DEBUG: note_viewer OK", flush=True)

print("DEBUG: importing pages.knowledge_vault...", flush=True)
from pages.knowledge_vault import render_knowledge_vault
print("DEBUG: knowledge_vault OK", flush=True)

print("DEBUG: importing pages.profile...", flush=True)
from pages.profile import render_profile
print("DEBUG: profile OK", flush=True)

print("DEBUG: importing ui.styles...", flush=True)
from ui.styles import inject_global_styles
print("DEBUG: ui.styles OK", flush=True)

print("DEBUG: importing ui.navigation...", flush=True)
from ui.navigation import render_sidebar_nav
print("DEBUG: ui.navigation OK", flush=True)

print("DEBUG: ALL IMPORTS OK - rendering app", flush=True)
st.write("All imports passed!")
