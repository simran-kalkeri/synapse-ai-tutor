"""
Learning Roadmap Page for Synapse AI Tutor.
Roadmap.sh-style interactive tree visualization using Cytoscape.js.
Click any node → navigates to the Note Viewer page for that topic.
"""

import json
import streamlit as st
import streamlit.components.v1 as components
from backend.roadmap_generator import (
    generate_roadmap, save_roadmap, load_roadmap,
    update_roadmap_step, get_roadmap_progress
)
from backend.note_generator import (
    generate_knowledge_note, save_note, note_exists
)
from backend.progress_tracker import get_topic_progress, get_mastery_scores
from backend.gap_detector import detect_knowledge_gaps


def render_roadmap():
    """Render the Learning Roadmap page."""
    username = st.session_state.username
    topic = st.session_state.get("selected_topic")

    if not topic:
        st.warning("Please select a topic first.")
        if st.button("Go to Topics"):
            st.session_state.page = "topic_selection"
            st.rerun()
        return

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="animate-fade-in" style="text-align:center;margin-bottom:1rem;">
        <h1 class="gradient-text" style="font-size:2.2rem;margin-bottom:0.3rem;">Learning Roadmap</h1>
        <p style="color:#A0A0C0;font-size:0.9rem;">
            Your personalized path for <strong style="color:#00D2FF;">{topic}</strong>
            — click any topic to view its note
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load or generate roadmap ──────────────────────────────────────────────
    roadmap = load_roadmap(username, topic)

    if not roadmap:
        progress = get_topic_progress(username, topic)
        level = progress.get("level", "Beginner")
        if level == "Not Assessed":
            level = "Beginner"
        mastery_scores = get_mastery_scores(username)
        gap_analysis = detect_knowledge_gaps(topic, mastery_scores)
        gaps = gap_analysis.get("gaps", [])
        roadmap = generate_roadmap(topic, level, gaps)
        save_roadmap(username, topic, roadmap)

        # Auto-generate notes for all steps
        with st.spinner("✨ Generating knowledge notes for your roadmap..."):
            rag = st.session_state.get("rag_pipeline")
            for step in roadmap:
                if not note_exists(username, step["name"]):
                    note_content = generate_knowledge_note(step["name"], level, rag)
                    save_note(username, step["name"], note_content)
        st.rerun()

    # ── Progress Bar ──────────────────────────────────────────────────────────
    rp = get_roadmap_progress(username, topic)
    _render_progress(rp)
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── Roadmap.sh-style Graph ────────────────────────────────────────────────
    tree = _build_tree(roadmap, topic, username)
    html = _generate_roadmap_html(tree, topic)
    components.html(html, height=500, scrolling=False)

    # ── Topic Selector → Note Viewer ──────────────────────────────────────────
    topic_names = [step["name"] for step in roadmap]
    sel_col1, sel_col2 = st.columns([3, 1])
    with sel_col1:
        selected_note = st.selectbox(
            "📝 Select a topic to read its note",
            options=["— Click a topic —"] + topic_names,
            key="_roadmap_topic_select",
            label_visibility="collapsed",
        )
    with sel_col2:
        go_clicked = st.button("Open Note →", use_container_width=True, type="primary",
                               disabled=(selected_note == "— Click a topic —"))

    if go_clicked and selected_note != "— Click a topic —":
        if note_exists(username, selected_note):
            st.session_state["_note_viewer_topic"] = selected_note
            st.session_state.page = "note_viewer"
            st.rerun()
        else:
            with st.spinner(f"Generating note for {selected_note}..."):
                progress = get_topic_progress(username, topic)
                level = progress.get("level", "Beginner")
                rag = st.session_state.get("rag_pipeline")
                content = generate_knowledge_note(selected_note, level, rag)
                save_note(username, selected_note, content)
            st.session_state["_note_viewer_topic"] = selected_note
            st.session_state.page = "note_viewer"
            st.rerun()

    # ── Bottom Navigation ─────────────────────────────────────────────────────
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💬 Tutor Chat", use_container_width=True, type="primary"):
            st.session_state.page = "tutor"
            st.rerun()
    with col2:
        if st.button("📚 Knowledge Vault", use_container_width=True):
            st.session_state.page = "knowledge_vault"
            st.rerun()
    with col3:
        if st.button("🔗 Knowledge Graph", use_container_width=True):
            st.session_state.page = "knowledge_graph"
            st.rerun()
    with col4:
        if st.button("🔄 Regenerate", use_container_width=True):
            progress = get_topic_progress(username, topic)
            level = progress.get("level", "Beginner")
            if level == "Not Assessed":
                level = "Beginner"
            mastery_scores = get_mastery_scores(username)
            gap_analysis = detect_knowledge_gaps(topic, mastery_scores)
            gaps = gap_analysis.get("gaps", [])
            new_roadmap = generate_roadmap(topic, level, gaps)
            save_roadmap(username, topic, new_roadmap)
            st.rerun()


# ── Progress Section ──────────────────────────────────────────────────────────

def _render_progress(rp: dict):
    cols = st.columns(4)
    items = [
        ("Total Steps", str(rp["total"]), "#FFFFFF"),
        ("Completed", str(rp["complete"]), "#2ECC71"),
        ("In Progress", str(rp["current"]), "#F39C12"),
        ("Progress", f"{rp['percentage']}%", "#6C63FF"),
    ]
    for col, (label, value, color) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.4rem;font-weight:800;color:{color};">{value}</div>
                <div style="color:#A0A0C0;font-size:0.7rem;margin-top:0.1rem;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    if rp["total"] > 0:
        st.progress(rp["percentage"] / 100)


# ── Tree Builder ──────────────────────────────────────────────────────────────

def _build_tree(roadmap: list, main_topic: str, username: str) -> dict:
    groups = {}
    for step in roadmap:
        st_type = step.get("step_type", "core")
        if st_type not in groups:
            groups[st_type] = []
        groups[st_type].append(step)

    nodes = []
    edges = []

    root_id = _sid(main_topic)
    nodes.append({"id": root_id, "label": main_topic, "group": "root",
                  "status": "root", "step_type": "root"})

    group_meta = {
        "prerequisite": ("Prerequisites", "#F39C12"),
        "gap": ("Knowledge Gaps", "#E74C3C"),
        "core": ("Core Concepts", "#6C63FF"),
        "advanced": ("Advanced", "#8B83FF"),
    }

    for g_type in ["prerequisite", "gap", "core", "advanced"]:
        if g_type not in groups:
            continue
        steps = groups[g_type]
        label, color = group_meta.get(g_type, (g_type.title(), "#6C63FF"))
        gid = f"g_{g_type}"

        nodes.append({"id": gid, "label": label, "group": "header",
                      "status": "group", "color": color})
        edges.append({"source": root_id, "target": gid})

        for step in steps:
            cid = _sid(step["name"])
            nodes.append({"id": cid, "label": step["name"], "group": "topic",
                          "status": step["status"], "color": color})
            edges.append({"source": gid, "target": cid})

    return {"nodes": nodes, "edges": edges}


def _sid(name: str) -> str:
    return name.lower().replace(" ", "_").replace("&", "and").replace("/", "_").replace("(", "").replace(")", "").replace(",", "")


def _read_static(path: str) -> str:
    """Read a static JS file for inlining. Returns empty string on failure."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''


# ── Cytoscape HTML ────────────────────────────────────────────────────────────

def _generate_roadmap_html(tree: dict, topic: str) -> str:
    import os
    elements = [{"data": n} for n in tree["nodes"]] + [{"data": e} for e in tree["edges"]]
    ejs = json.dumps(elements)

    # Read inlined JS libraries
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    cyto_js = _read_static(os.path.join(static_dir, "cytoscape.min.js"))
    dagre_js = _read_static(os.path.join(static_dir, "dagre.min.js"))
    cyto_dagre_js = _read_static(os.path.join(static_dir, "cytoscape-dagre.js"))

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0A0A1A;overflow:hidden;font-family:'Inter',-apple-system,sans-serif}}
#cy{{width:100%;height:480px;border:1px solid rgba(108,99,255,0.1);border-radius:14px;
     background:radial-gradient(ellipse at 50% 30%,#111130,#0A0A1A)}}
#tt{{position:absolute;display:none;background:rgba(16,16,40,0.96);border:1px solid rgba(108,99,255,0.35);
    border-radius:8px;padding:8px 12px;color:#fff;font-size:11px;font-family:Inter,sans-serif;
    box-shadow:0 6px 24px rgba(0,0,0,0.5);pointer-events:none;z-index:999;max-width:220px;
    backdrop-filter:blur(8px)}}
</style></head><body>
<div style="position:relative"><div id="cy"></div><div id="tt"></div></div>
<script>{cyto_js}</script>
<script>{dagre_js}</script>
<script>{cyto_dagre_js}</script>
<script>
var cy=cytoscape({{
  container:document.getElementById('cy'),
  elements:{ejs},
  style:[
    {{selector:'node[group="root"]',style:{{
      'label':'data(label)','shape':'round-rectangle','width':'label','height':38,'padding':'16px',
      'background-color':'#6C63FF','border-width':2.5,'border-color':'#8B83FF',
      'color':'#FFF','font-size':'12px','font-weight':'700','font-family':'Inter,sans-serif',
      'text-valign':'center','text-halign':'center','text-wrap':'wrap','text-max-width':'130px',
      'shadow-blur':18,'shadow-color':'rgba(108,99,255,0.5)','shadow-offset-x':0,'shadow-offset-y':0,'shadow-opacity':1
    }}}},
    {{selector:'node[group="header"]',style:{{
      'label':'data(label)','shape':'round-rectangle','width':'label','height':30,'padding':'10px',
      'background-opacity':0.12,'border-width':1.5,
      'background-color':function(e){{return e.data('color')||'#3A3A5C'}},
      'border-color':function(e){{return e.data('color')||'#4A4A6A'}},
      'color':function(e){{return e.data('color')||'#A0A0C0'}},
      'font-size':'10px','font-weight':'600','font-family':'Inter,sans-serif',
      'text-valign':'center','text-halign':'center'
    }}}},
    {{selector:'node[group="topic"][status="complete"]',style:{{
      'label':function(e){{return '✓ '+e.data('label')}},
      'shape':'round-rectangle','width':'label','height':28,'padding':'8px',
      'background-color':'rgba(46,204,113,0.12)','border-width':2,'border-color':'#2ECC71',
      'color':'#2ECC71','font-size':'9px','font-weight':'500','font-family':'Inter,sans-serif',
      'text-valign':'center','text-halign':'center','text-wrap':'wrap','text-max-width':'110px'
    }}}},
    {{selector:'node[group="topic"][status="current"]',style:{{
      'label':'data(label)','shape':'round-rectangle','width':'label','height':28,'padding':'8px',
      'background-color':'#F39C12','border-width':2,'border-color':'#FFB347',
      'color':'#0A0A1A','font-size':'9px','font-weight':'600','font-family':'Inter,sans-serif',
      'text-valign':'center','text-halign':'center','text-wrap':'wrap','text-max-width':'110px',
      'shadow-blur':12,'shadow-color':'rgba(243,156,18,0.4)','shadow-offset-x':0,'shadow-offset-y':0,'shadow-opacity':1
    }}}},
    {{selector:'node[group="topic"][status="locked"]',style:{{
      'label':'data(label)','shape':'round-rectangle','width':'label','height':28,'padding':'8px',
      'background-color':'rgba(58,58,92,0.4)','border-width':1,'border-color':'#3A3A5C',
      'color':'#7777AA','font-size':'9px','font-weight':'400','font-family':'Inter,sans-serif',
      'text-valign':'center','text-halign':'center','text-wrap':'wrap','text-max-width':'110px'
    }}}},
    {{selector:'edge',style:{{
      'width':1.5,'line-color':'rgba(108,99,255,0.2)','line-style':'dashed',
      'line-dash-pattern':[6,4],'target-arrow-shape':'triangle',
      'target-arrow-color':'rgba(108,99,255,0.3)','arrow-scale':0.6,
      'curve-style':'bezier'
    }}}},
    {{selector:'node.hl',style:{{'border-color':'#00D2FF','border-width':3,
      'shadow-blur':20,'shadow-color':'rgba(0,210,255,0.5)','shadow-offset-x':0,'shadow-offset-y':0,'shadow-opacity':1
    }}}},
    {{selector:'.faded',style:{{'opacity':0.12}}}}
  ],
  layout:{{
    name:'dagre', rankDir:'TB', nodeSep:50, rankSep:70, edgeSep:20,
    padding:35, animate:true, animationDuration:500, animationEasing:'ease-out-cubic', fit:true
  }},
  minZoom:0.35, maxZoom:2.5, wheelSensitivity:0.25
}});
var tt=document.getElementById('tt');
cy.on('mouseover','node[group="topic"],node[group="root"]',function(e){{
  var d=e.target.data();
  var s={{'complete':'✅ Done','current':'🟡 Current','locked':'🔒 Locked','root':'🎯 Main'}}[d.status]||'';
  tt.innerHTML='<b>'+d.label+'</b><br><span style="color:#A0A0C0">'+s+'</span>';
  tt.style.display='block';
}});
cy.on('mouseout','node',function(){{tt.style.display='none'}});
cy.on('mousemove','node',function(e){{
  var p=e.renderedPosition||e.cyRenderedPosition;
  tt.style.left=Math.min(p.x+12,window.innerWidth-230)+'px';tt.style.top=(p.y-45)+'px';
}});
cy.on('tap','node[group="topic"],node[group="root"]',function(e){{
  cy.elements().removeClass('faded hl');
  var nb=e.target.closedNeighborhood();
  cy.elements().not(nb).addClass('faded');
  e.target.addClass('hl');
}});
cy.on('tap',function(e){{if(e.target===cy)cy.elements().removeClass('faded hl')}});
</script></body></html>"""


