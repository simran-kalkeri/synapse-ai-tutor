"""
Knowledge Graph Module for Synapse AI Tutor.

Builds and manages a NetworkX-based knowledge graph of AI/ML topics and
concepts. Provides graph traversal, query expansion, and learning path
generation for GraphRAG retrieval.

Functions:
    build_knowledge_graph()   -- load/build the NetworkX graph
    expand_query()            -- expand a query using graph neighbours
    graph_learning_path()     -- find prerequisite study path for a concept
    get_concept_neighbours()  -- direct neighbour lookup
    concept_to_topic()        -- map a concept string to its parent topic
"""

import json
import os
import re
import networkx as nx
from functools import lru_cache

_GRAPH_JSON = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_graph.json"
)

# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_knowledge_graph() -> nx.DiGraph:
    """
    Load the knowledge graph from JSON and return a NetworkX DiGraph.

    The graph contains:
    * Topic nodes  (Neural Networks, Transformers, …)
    * Concept nodes (Self-Attention, Embeddings, …)
    * Directed edges with a 'relation' attribute
    """
    with open(_GRAPH_JSON, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    G = nx.DiGraph()

    for node in data["nodes"]:
        G.add_node(
            node["id"],
            node_type=node.get("type", "concept"),
            level=node.get("level", ""),
            topic=node.get("topic", ""),
        )

    for edge in data["edges"]:
        G.add_edge(
            edge["source"],
            edge["target"],
            relation=edge.get("relation", "related"),
        )

    return G


# Singleton – loaded once per process
@lru_cache(maxsize=1)
def _get_graph() -> nx.DiGraph:
    return build_knowledge_graph()


# ---------------------------------------------------------------------------
# Query expansion
# ---------------------------------------------------------------------------

def expand_query(question: str, topic: str, depth: int = 2) -> dict:
    """
    Expand a student question using the knowledge graph.

    Steps:
      1. Identify the best-matching concept node(s) in the question text.
      2. Collect neighbours up to *depth* hops in both directions.
      3. Return the expanded term list and metadata.

    Args:
        question: The raw student question string.
        topic:    The currently selected topic (used as anchor).
        depth:    How many hops from the matched concept(s) to include.

    Returns:
        {
            "original_query":   str,
            "expanded_query":   str,
            "matched_concepts": list[str],
            "neighbour_concepts": list[str],
            "expansion_path":   list[str],
        }
    """
    G = _get_graph()

    question_lower = question.lower()

    # 1. Match graph nodes whose names appear in the question
    matched = []
    for node in G.nodes():
        if node.lower() in question_lower:
            matched.append(node)

    # 2. Also include all concept nodes that belong to the selected topic
    topic_concepts = [
        n for n, d in G.nodes(data=True)
        if d.get("topic") == topic or n == topic
    ]

    if not matched:
        # Fall back to the topic node itself
        matched = [topic] if topic in G else []

    # 3. Collect neighbourhood
    neighbours = set()
    for concept in matched:
        if concept not in G:
            continue
        # Out-neighbours (concepts this concept leads to)
        for successor in nx.descendants(G, concept) if depth > 1 else G.successors(concept):
            neighbours.add(successor)
        # In-neighbours (prerequisites)
        for predecessor in G.predecessors(concept):
            neighbours.add(predecessor)

    # Remove the matched nodes themselves and pure topic nodes for cleaner terms
    expansion_concepts = list(neighbours - set(matched))
    expansion_concepts = [c for c in expansion_concepts if c != topic][:8]

    # 4. Build expanded query string
    all_terms = [question] + matched + expansion_concepts
    expanded_query = " ".join(dict.fromkeys(all_terms))  # dedup-preserving order

    return {
        "original_query":     question,
        "expanded_query":     expanded_query,
        "matched_concepts":   matched,
        "neighbour_concepts": expansion_concepts,
        "expansion_path":     matched + expansion_concepts,
    }


# ---------------------------------------------------------------------------
# Learning path
# ---------------------------------------------------------------------------

def graph_learning_path(concept: str, topic: str) -> list:
    """
    Return an ordered list of concepts the student should study to reach
    *concept* within *topic*.

    Uses shortest-path from the topic node to the concept node.
    If the concept is not directly reachable, falls back to prerequisite listing.

    Args:
        concept: Target concept string (e.g. "Self-Attention").
        topic:   The parent topic (e.g. "Transformers").

    Returns:
        List of concept/topic strings representing the study path.
    """
    G = _get_graph()

    if concept not in G:
        # Return prerequisite order from gap_detector data
        from backend.gap_detector import PREREQUISITE_MAP
        return PREREQUISITE_MAP.get(topic, {}).get("prerequisites", [])

    if topic not in G:
        return [concept]

    try:
        path = nx.shortest_path(G, source=topic, target=concept)
        return path
    except nx.NetworkXNoPath:
        # If no directed path, try undirected
        try:
            UG = G.to_undirected()
            path = nx.shortest_path(UG, source=topic, target=concept)
            return path
        except nx.NetworkXNoPath:
            return [topic, concept]
    except nx.NodeNotFound:
        return [concept]


# ---------------------------------------------------------------------------
# Neighbour lookup
# ---------------------------------------------------------------------------

def get_concept_neighbours(concept: str, max_hops: int = 1) -> list:
    """
    Return direct (1-hop) neighbours of a concept in the knowledge graph.

    Args:
        concept:  Node name.
        max_hops: Hop depth (1 = direct neighbours only).

    Returns:
        List of neighbour node names.
    """
    G = _get_graph()
    if concept not in G:
        return []

    if max_hops == 1:
        succs = list(G.successors(concept))
        preds = list(G.predecessors(concept))
        return list(dict.fromkeys(succs + preds))

    visited = set()
    frontier = {concept}
    for _ in range(max_hops):
        next_frontier = set()
        for node in frontier:
            next_frontier |= set(G.successors(node)) | set(G.predecessors(node))
        next_frontier -= visited | {concept}
        visited |= next_frontier
        frontier = next_frontier

    return list(visited)


# ---------------------------------------------------------------------------
# Concept → Topic resolution
# ---------------------------------------------------------------------------

def concept_to_topic(concept: str) -> str:
    """
    Return the parent topic for a given concept node.

    Args:
        concept: Concept name string.

    Returns:
        Topic string, or empty string if not found.
    """
    G = _get_graph()
    node_data = G.nodes.get(concept, {})
    topic = node_data.get("topic", "")
    if topic:
        return topic

    # Walk up in-edges to find a topic node
    for pred in G.predecessors(concept):
        pred_data = G.nodes.get(pred, {})
        if pred_data.get("node_type") == "topic":
            return pred
        # One more level
        for pred2 in G.predecessors(pred):
            if G.nodes.get(pred2, {}).get("node_type") == "topic":
                return pred2
    return ""


# ---------------------------------------------------------------------------
# Graph statistics (for UI display)
# ---------------------------------------------------------------------------

def get_graph_stats(username: str = None) -> dict:
    """Return summary statistics about the knowledge graph.

    Args:
        username: Optional. If provided, mastery data is included in stats.
                  Backward-compatible — existing callers with no args still work.
    """
    G = _get_graph()
    topics   = [n for n, d in G.nodes(data=True) if d.get("node_type") == "topic"]
    concepts = [n for n, d in G.nodes(data=True) if d.get("node_type") == "concept"]

    stats = {
        "total_nodes":  G.number_of_nodes(),
        "total_edges":  G.number_of_edges(),
        "num_topics":   len(topics),
        "num_concepts": len(concepts),
        "is_dag":       nx.is_directed_acyclic_graph(G),
        "density":      round(nx.density(G), 4),
        # Cytoscape page compat keys
        "main_topics":  len(topics),
        "prerequisites": 0,
        "mastered":     0,
        "in_progress":  0,
        "not_started":  len(topics),
    }

    # Enrich with mastery data if username provided
    if username:
        try:
            from backend.progress_tracker import get_user_progress
            user_progress = get_user_progress(username)
            mastered    = sum(1 for t in topics if user_progress.get(t, {}).get("mastery", 0) >= 76)
            in_progress = sum(1 for t in topics if 0 < user_progress.get(t, {}).get("mastery", 0) < 76)
            stats["mastered"]     = mastered
            stats["in_progress"]  = in_progress
            stats["not_started"]  = len(topics) - mastered - in_progress
        except Exception:
            pass

    return stats


def get_all_concepts_for_topic(topic: str) -> list:
    """Return all concept nodes belonging to a given topic."""
    G = _get_graph()
    return [
        n for n, d in G.nodes(data=True)
        if d.get("topic") == topic or (
            d.get("node_type") == "topic" and n == topic
        )
    ]


def get_topic_subgraph(topic: str) -> nx.DiGraph:
    """Return the induced subgraph containing the topic and all its concepts."""
    G   = _get_graph()
    nodes = [topic] + get_all_concepts_for_topic(topic)
    valid = [n for n in nodes if n in G]
    return G.subgraph(valid).copy()


# =============================================================================
# Cytoscape.js Visualization Layer
# (used by knowledge_graph_page.py, roadmap.py)
# This section is independent of the NetworkX / GraphRAG code above.
# =============================================================================

import json as _json

_MASTERY_COLORS = {
    "mastered":    "#2ECC71",
    "in_progress": "#F39C12",
    "not_started": "#3A3A5C",
    "prerequisite": "#6B6B8D",
}


def build_full_graph(username: str = None) -> dict:
    """
    Build the full curriculum knowledge graph for Cytoscape.js rendering.

    Pulls topic/mastery data from progress_tracker and prerequisite
    relationships from gap_detector.PREREQUISITE_MAP.

    Returns:
        dict with "nodes" and "edges" lists.
    """
    from backend.gap_detector import PREREQUISITE_MAP
    from backend.progress_tracker import get_user_progress

    user_progress = get_user_progress(username) if username else {}

    nodes, edges = [], []
    seen = set()

    for topic, data in PREREQUISITE_MAP.items():
        prog = user_progress.get(topic, {})
        mastery = prog.get("mastery", 0)
        level   = prog.get("level", "Not Assessed")

        nodes.append({
            "id":     _safe_id(topic),
            "label":  topic,
            "mastery": mastery,
            "level":  level,
            "group":  "main",
        })
        seen.add(topic)

        for prereq in data.get("prerequisites", []):
            edges.append({
                "source": _safe_id(prereq),
                "target": _safe_id(topic),
                "label":  "requires",
                "type":   "prerequisite",
            })
            if prereq not in seen:
                nodes.append({
                    "id":     _safe_id(prereq),
                    "label":  prereq,
                    "mastery": 0,
                    "level":  "Prerequisite",
                    "group":  "prerequisite",
                })
                seen.add(prereq)

        for related in data.get("related_topics", []):
            edges.append({
                "source": _safe_id(topic),
                "target": _safe_id(related),
                "label":  "related",
                "type":   "related",
            })

    return {"nodes": nodes, "edges": edges}


def build_topic_graph(topic: str, username: str = None) -> dict:
    """
    Build the concept-level graph for a single topic for Cytoscape.js rendering.

    Returns:
        dict with "nodes" and "edges" lists (topic node + concept nodes).
    """
    from backend.gap_detector import PREREQUISITE_MAP
    from backend.progress_tracker import get_user_progress

    user_progress = get_user_progress(username) if username else {}
    prog    = user_progress.get(topic, {})
    mastery = prog.get("mastery", 0)
    level   = prog.get("level", "Not Assessed")
    gaps    = set(prog.get("knowledge_gaps", []))

    nodes = [{
        "id":     _safe_id(topic),
        "label":  topic,
        "mastery": mastery,
        "level":  level,
        "group":  "main",
    }]
    edges = []

    # Concepts from the NetworkX graph
    G = _get_graph()
    concept_nodes = [
        n for n, d in G.nodes(data=True)
        if d.get("topic") == topic
    ]

    for concept in concept_nodes:
        status = "gap" if concept in gaps else "concept"
        nodes.append({
            "id":     _safe_id(concept),
            "label":  concept,
            "mastery": 0,
            "level":  "Concept",
            "group":  status,
        })
        edges.append({
            "source": _safe_id(topic),
            "target": _safe_id(concept),
            "label":  "contains",
            "type":   "concept",
        })
        # concept-to-concept edges from the NetworkX graph
        for succ in G.successors(concept):
            if G.nodes.get(succ, {}).get("topic") == topic:
                edges.append({
                    "source": _safe_id(concept),
                    "target": _safe_id(succ),
                    "label":  "leads to",
                    "type":   "concept",
                })

    return {"nodes": nodes, "edges": edges}


def generate_cytoscape_html(
    graph_data: dict = None,
    height=550,
    username: str = None,
) -> str:
    """
    Generate a self-contained HTML string that renders the graph with
    Cytoscape.js. Libraries are INLINED (not loaded from CDN) so they
    work inside Streamlit's sandboxed iframe.
    """
    # Auto-build graph data if not supplied
    if graph_data is None:
        graph_data = build_full_graph(username)

    # Normalise height
    if isinstance(height, str):
        height_px = int(height.replace('px', '').strip())
    else:
        height_px = int(height)

    elements_js = _build_elements_js(graph_data)

    # Read inlined JS libraries
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
    cyto_js = _read_static(os.path.join(static_dir, 'cytoscape.min.js'))
    bilkent_js = _read_static(os.path.join(static_dir, 'cytoscape-cose-bilkent.js'))

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0; padding: 0; background: #0A0A1A;
    font-family: 'Inter', sans-serif; overflow: hidden;
  }}
  #cy {{
    width: 100%; height: {height_px}px;
    background: radial-gradient(ellipse at center, #10103A 0%, #0A0A1A 100%);
  }}
  #tooltip {{
    position: absolute; display: none; pointer-events: none;
    background: rgba(18,18,42,0.97); border: 1px solid rgba(108,99,255,0.4);
    border-radius: 10px; padding: 10px 14px; z-index: 9999;
    max-width: 200px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .tt-title  {{ color: #FFFFFF; font-weight: 700; font-size: 13px; margin-bottom: 4px; }}
  .tt-mastery{{ font-size: 11px; margin-bottom: 2px; }}
  .tt-level  {{ color: #6B6B8D; font-size: 11px; }}
</style>
</head>
<body>
<div id="cy"></div>
<div id="tooltip"></div>
<script>{cyto_js}</script>
<script>{bilkent_js}</script>
<script>
  // Register cose-bilkent plugin
  if (typeof cytoscapeCoseBilkent !== 'undefined') {{
    cytoscape.use(cytoscapeCoseBilkent);
  }}

  var elements = {elements_js};

  var layoutCfg = (typeof cytoscapeCoseBilkent !== 'undefined')
    ? {{
        name: 'cose-bilkent', quality: 'proof',
        nodeDimensionsIncludeLabels: true, idealEdgeLength: 150,
        nodeRepulsion: 6000, edgeElasticity: 0.45, gravity: 0.35,
        numIter: 2000, animate: 'end', animationDuration: 700,
        fit: true, padding: 40, randomize: true,
      }}
    : {{
        name: 'cose', nodeDimensionsIncludeLabels: true,
        idealEdgeLength: function(){{ return 120; }},
        nodeRepulsion: function(){{ return 5000; }},
        gravity: 0.4, numIter: 1000, animate: true,
        animationDuration: 500, fit: true, padding: 40, randomize: true,
      }};

  var cy = cytoscape({{
    container: document.getElementById('cy'),
    elements: elements,
    style: [
      {{
        selector: 'node[group="main"]',
        style: {{
          'background-color': function(ele) {{
            var m = ele.data('mastery');
            return m >= 76 ? '#2ECC71' : (m > 0 ? '#F39C12' : '#3A3A5C');
          }},
          'label': 'data(label)', 'color': '#FFFFFF',
          'font-size': '10px', 'font-family': 'Inter, sans-serif',
          'font-weight': '600', 'text-valign': 'bottom', 'text-margin-y': 6,
          'text-wrap': 'wrap', 'text-max-width': '90px',
          'text-outline-color': '#0A0A1A', 'text-outline-width': 2,
          'width': 38, 'height': 38,
          'border-width': 2.5, 'border-color': '#6C63FF',
          'shadow-blur': 15, 'shadow-color': 'rgba(108,99,255,0.35)',
          'shadow-offset-x': 0, 'shadow-offset-y': 0, 'shadow-opacity': 1,
        }}
      }},
      {{
        selector: 'node[group="prerequisite"]',
        style: {{
          'background-color': '#6B6B8D', 'label': 'data(label)',
          'color': '#A0A0C0', 'font-size': '8px',
          'text-valign': 'bottom', 'text-margin-y': 5,
          'text-wrap': 'wrap', 'text-max-width': '75px',
          'text-outline-color': '#0A0A1A', 'text-outline-width': 1.5,
          'width': 24, 'height': 24,
          'border-width': 1.5, 'border-color': '#4A4A6A',
        }}
      }},
      {{
        selector: 'node[group="concept"]',
        style: {{
          'background-color': '#1A1A4E', 'label': 'data(label)',
          'color': '#A0A0C0', 'font-size': '8px',
          'text-valign': 'bottom', 'text-margin-y': 5,
          'text-wrap': 'wrap', 'text-max-width': '80px',
          'text-outline-color': '#0A0A1A', 'text-outline-width': 1.5,
          'width': 22, 'height': 22,
          'border-width': 1.5, 'border-color': '#00D2FF',
        }}
      }},
      {{
        selector: 'node[group="gap"]',
        style: {{
          'background-color': '#E74C3C', 'label': 'data(label)',
          'color': '#FFFFFF', 'font-size': '8px',
          'text-valign': 'bottom', 'text-margin-y': 5,
          'text-wrap': 'wrap', 'text-max-width': '80px',
          'text-outline-color': '#0A0A1A', 'text-outline-width': 1.5,
          'width': 22, 'height': 22,
          'border-width': 2, 'border-color': '#FF6B6B',
          'shadow-blur': 10, 'shadow-color': 'rgba(231,76,60,0.4)',
          'shadow-offset-x': 0, 'shadow-offset-y': 0, 'shadow-opacity': 1,
        }}
      }},
      {{
        selector: 'edge[type="prerequisite"]',
        style: {{
          'width': 1.5,
          'line-color': 'rgba(108,99,255,0.35)',
          'target-arrow-color': 'rgba(108,99,255,0.5)',
          'target-arrow-shape': 'triangle', 'arrow-scale': 0.8,
          'curve-style': 'bezier', 'opacity': 0.7,
        }}
      }},
      {{
        selector: 'edge[type="related"]',
        style: {{
          'width': 1, 'line-color': 'rgba(0,210,255,0.25)',
          'line-style': 'dashed', 'target-arrow-shape': 'none',
          'curve-style': 'bezier', 'opacity': 0.5,
        }}
      }},
      {{
        selector: 'edge[type="concept"]',
        style: {{
          'width': 1.2,
          'line-color': 'rgba(46,204,113,0.35)',
          'target-arrow-color': 'rgba(46,204,113,0.5)',
          'target-arrow-shape': 'triangle', 'arrow-scale': 0.7,
          'curve-style': 'bezier', 'opacity': 0.6,
        }}
      }},
      {{
        selector: 'node.highlighted',
        style: {{
          'border-color': '#6C63FF', 'border-width': 4,
          'shadow-blur': 25, 'shadow-color': 'rgba(108,99,255,0.6)',
          'z-index': 10,
        }}
      }},
      {{ selector: 'node.faded', style: {{ 'opacity': 0.15 }} }},
      {{
        selector: 'edge.highlighted',
        style: {{ 'width': 3, 'opacity': 1,
          'line-color': '#6C63FF', 'target-arrow-color': '#6C63FF' }}
      }},
      {{ selector: 'edge.faded', style: {{ 'opacity': 0.06 }} }},
    ],
    layout: layoutCfg,
    minZoom: 0.3, maxZoom: 3, wheelSensitivity: 0.3,
  }});

  var tooltip = document.getElementById('tooltip');

  cy.on('mouseover', 'node', function(e) {{
    var d = e.target.data();
    var mc = d.mastery >= 76 ? '#2ECC71' : (d.mastery > 0 ? '#F39C12' : '#6B6B8D');
    tooltip.innerHTML = '<div class="tt-title">' + d.label + '</div>'
      + '<div class="tt-mastery" style="color:' + mc + '">Mastery: ' + d.mastery + '%</div>'
      + '<div class="tt-level">Level: ' + d.level + '</div>'
      + '<div class="tt-level">Group: ' + d.group + '</div>';
    tooltip.style.display = 'block';
    var pos = e.renderedPosition || e.cyRenderedPosition;
    tooltip.style.left = (pos.x + 15) + 'px';
    tooltip.style.top  = (pos.y - 10) + 'px';
  }});
  cy.on('mouseout',  'node', function() {{ tooltip.style.display = 'none'; }});
  cy.on('mousemove', 'node', function(e) {{
    var pos = e.renderedPosition || e.cyRenderedPosition;
    tooltip.style.left = (pos.x + 15) + 'px';
    tooltip.style.top  = (pos.y - 10) + 'px';
  }});

  cy.on('tap', 'node', function(e) {{
    var node = e.target;
    var nbhd = node.closedNeighborhood();
    cy.elements().addClass('faded');
    nbhd.removeClass('faded');
    node.addClass('highlighted');
    nbhd.edges().addClass('highlighted');
    nbhd.nodes().removeClass('faded');
  }});
  cy.on('tap', function(e) {{
    if (e.target === cy) {{ cy.elements().removeClass('faded highlighted'); }}
  }});
</script>
</body>
</html>"""


def _read_static(path: str) -> str:
    """Read a static JS file for inlining. Returns empty string on failure."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''



def _build_elements_js(graph_data: dict) -> str:
    """Convert graph_data dict to a Cytoscape.js elements JSON string."""
    elements = []
    for node in graph_data["nodes"]:
        elements.append({"data": {
            "id":     node["id"],
            "label":  node["label"],
            "mastery": node["mastery"],
            "level":  node["level"],
            "group":  node["group"],
        }})
    for edge in graph_data["edges"]:
        elements.append({"data": {
            "source": edge["source"],
            "target": edge["target"],
            "label":  edge["label"],
            "type":   edge["type"],
        }})
    return _json.dumps(elements)


def _safe_id(name: str) -> str:
    """Convert a node label to a safe Cytoscape.js element ID."""
    return name.lower().replace(" ", "_").replace("/", "_").replace("&", "and")
