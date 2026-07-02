"""
Graph Renderer
Utility to render Graphviz sources as PIL images for Streamlit display.
"""
import io
import graphviz
from PIL import Image


def render_graphviz_to_pil(dot: graphviz.Digraph, fmt: str = "png") -> Image.Image:
    """Render a Graphviz digraph object to a PIL Image."""
    data = dot.pipe(format=fmt)
    return Image.open(io.BytesIO(data)).copy()


def render_source_to_pil(source: str, fmt: str = "png") -> Image.Image:
    """Render raw Graphviz DOT source to a PIL Image."""
    src = graphviz.Source(source)
    data = src.pipe(format=fmt)
    return Image.open(io.BytesIO(data)).copy()
