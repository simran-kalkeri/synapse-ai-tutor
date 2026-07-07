"""Generate a minimal knowledge graph JSON from PREREQUISITE_MAP.
The generated file is written to synapse_ai_tutor/data/knowledge_graph.json and is used by
backend.knowledge_graph.build_knowledge_graph()."""

import json
from pathlib import Path

import sys
from pathlib import Path
# Ensure the project root is in sys.path for relative imports
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))
from synapse_ai_tutor.backend.gap_detector import PREREQUISITE_MAP

def _collect_nodes_and_edges():
    nodes = {}
    edges = []
    for topic, data in PREREQUISITE_MAP.items():
        # Topic node
        nodes[topic] = {"id": topic, "type": "topic"}
        # Prerequisites
        for prereq in data.get("prerequisites", []):
            nodes[prereq] = {"id": prereq, "type": "concept"}
            edges.append({"source": prereq, "target": topic, "relation": "prerequisite"})
        # Key concepts
        for concept in data.get("key_concepts", []):
            nodes[concept] = {"id": concept, "type": "concept"}
            edges.append({"source": topic, "target": concept, "relation": "key_concept"})
        # Related topics (bidirectional for navigation)
        for rel in data.get("related_topics", []):
            nodes[rel] = {"id": rel, "type": "topic"}
            edges.append({"source": topic, "target": rel, "relation": "related"})
            edges.append({"source": rel, "target": topic, "relation": "related"})
    return list(nodes.values()), edges

def main():
    nodes, edges = _collect_nodes_and_edges()
    graph = {"nodes": nodes, "edges": edges}
    data_path = Path(__file__).resolve().parents[1] / "data" / "knowledge_graph.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Knowledge graph written to {data_path}")

if __name__ == "__main__":
    main()
