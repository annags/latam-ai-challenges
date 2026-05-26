"""
Network graph component — built with vis.js directly (not pyvis wrapper).
Generates a self-contained HTML page embedded via st.components.v1.html.
"""
import json
import tempfile
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

CAT1_COLORS = {
    "Socio-technical": "#1D9E75",
    "Ethical":         "#D85A30",
    "Institutional":   "#7F77DD",
}
ARTICLE_COLOR  = "#6c8ebf"
ARTICLE_BORDER = "#4a6fa5"

# HTML template — uses __PLACEHOLDER__ substitution to avoid f-string/brace conflicts with JS
_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; overflow: hidden; background: #f9f9f9; }
  #wrapper { position: relative; width: 100%; height: 100vh; }
  #mynetwork { width: 100%; height: 100vh; }

  /* ── Control panel ────────────────────────────────────────── */
  #controls {
    position: absolute; top: 12px; left: 12px; z-index: 300;
    background: rgba(255,255,255,0.97); border: 1px solid #ddd;
    border-radius: 10px; padding: 14px 16px; width: 215px;
    box-shadow: 0 3px 14px rgba(0,0,0,0.13);
  }
  #controls h4 { font-size: 12px; font-weight: 700; color: #333; margin-bottom: 10px;
    border-bottom: 1px solid #eee; padding-bottom: 7px; }
  .sec { font-size: 10px; font-weight: 700; color: #888; text-transform: uppercase;
    letter-spacing: 0.6px; margin: 10px 0 6px; }
  .cat-label { display: flex; align-items: center; gap: 7px; cursor: pointer;
    margin-bottom: 5px; font-size: 12px; color: #333; }
  .cat-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  input[type=range] { width: 100%; accent-color: #1D9E75; margin: 3px 0; }
  .srow { display: flex; justify-content: space-between; font-size: 10px; color: #999; }
  .toggle-label { display: flex; align-items: center; gap: 7px; cursor: pointer;
    font-size: 12px; color: #333; margin-top: 8px; }
  #applyBtn {
    width: 100%; margin-top: 11px; padding: 7px;
    background: #1D9E75; color: #fff; border: none;
    border-radius: 7px; cursor: pointer; font-size: 12px; font-weight: 700;
    transition: background 0.15s;
  }
  #applyBtn:hover { background: #178563; }

  /* ── Top-right buttons ────────────────────────────────────── */
  .top-btn {
    position: absolute; top: 12px; z-index: 300;
    background: rgba(255,255,255,0.97); border: 1px solid #ddd;
    border-radius: 8px; padding: 7px 13px; cursor: pointer;
    font-size: 12px; font-weight: 600; color: #333;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    display: flex; align-items: center; gap: 6px;
    transition: background 0.15s;
  }
  .top-btn:hover { background: #f0f0f0; }
  #fsBtn  { right: 12px; }
  #fitBtn { right: 165px; }

  /* ── Legend ───────────────────────────────────────────────── */
  #legend {
    position: absolute; bottom: 14px; left: 12px; z-index: 300;
    background: rgba(255,255,255,0.95); border: 1px solid #ddd;
    border-radius: 9px; padding: 10px 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.09);
  }
  .leg-item { display: flex; align-items: center; gap: 7px;
    margin-bottom: 4px; font-size: 11px; color: #444; }
  .l-dot { width: 13px; height: 13px; border-radius: 50%; flex-shrink: 0; }
  .l-sq  { width: 11px; height: 11px; flex-shrink: 0; }
  .leg-note { font-size: 10px; color: #999; margin-top: 7px; line-height: 1.4; }

  /* ── Tooltip override (vis.js) ────────────────────────────── */
  .vis-tooltip {
    background: rgba(255,255,255,0.98) !important;
    border: 1px solid #ccc !important;
    border-radius: 8px !important;
    padding: 10px 13px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 12px !important;
    color: #222 !important;
    max-width: 280px !important;
    line-height: 1.5 !important;
    pointer-events: none !important;
  }
</style>
</head>
<body>
<div id="wrapper">
  <div id="mynetwork"></div>

  <!-- ── Filter panel ──────────────────────────────────────── -->
  <div id="controls">
    <h4>🔍 Filtros</h4>
    <div class="sec">Categoría de reto</div>
    __CAT_CHECKBOXES__
    <div class="sec">Mín. artículos por reto</div>
    <input type="range" id="minArt" min="1" max="__MAX_COUNT__" value="1"
           oninput="document.getElementById('minVal').textContent=this.value">
    <div class="srow"><span>1</span><b><span id="minVal">1</span></b><span>__MAX_COUNT__</span></div>
    <label class="toggle-label">
      <input type="checkbox" id="showArt" checked> Mostrar nodos de artículos
    </label>
    <button id="applyBtn" onclick="applyFilters()">Aplicar</button>
  </div>

  <!-- ── Top buttons ───────────────────────────────────────── -->
  <button class="top-btn" id="fitBtn" onclick="network.fit()">⊙ Centrar</button>
  <button class="top-btn" id="fsBtn"  onclick="toggleFullscreen()">⛶ Pantalla completa</button>

  <!-- ── Legend ────────────────────────────────────────────── -->
  <div id="legend">
    <div class="leg-item"><span class="l-dot" style="background:#1D9E75"></span>Socio-technical</div>
    <div class="leg-item"><span class="l-dot" style="background:#D85A30"></span>Ethical</div>
    <div class="leg-item"><span class="l-dot" style="background:#7F77DD"></span>Institutional</div>
    <div class="leg-item"><span class="l-sq"  style="background:#6c8ebf"></span>Artículo</div>
    <div class="leg-note">
      Tamaño del círculo = nº artículos que citan el reto<br>
      Clic en un nodo → resalta sus conexiones
    </div>
  </div>
</div>

<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<script>
// ── Data ─────────────────────────────────────────────────────────────────────
var allNodesData = __NODES_JSON__;
var allEdgesData = __EDGES_JSON__;

var nodes = new vis.DataSet(allNodesData);
var edges = new vis.DataSet(allEdgesData);

var container = document.getElementById('mynetwork');
var network   = new vis.Network(
  container,
  { nodes: nodes, edges: edges },
  {
    physics: {
      solver: 'barnesHut',
      barnesHut: {
        gravitationalConstant: -7000,
        centralGravity: 0.25,
        springLength: 130,
        springConstant: 0.04,
        damping: 0.12,
        avoidOverlap: 0.3
      },
      stabilization: { iterations: 200, fit: true }
    },
    interaction: {
      hover: true,
      tooltipDelay: 90,
      zoomView: true,
      dragNodes: true,
      dragView: true,
      multiselect: false
    },
    edges: {
      color: { color: '#dddddd', highlight: '#888', hover: '#aaa' },
      width: 1,
      smooth: { type: 'continuous' }
    },
    nodes: { borderWidthSelected: 3 }
  }
);

// ── Neighbour highlight ───────────────────────────────────────────────────────
function resetHighlight() {
  nodes.update(allNodesData.map(function(n) {
    return { id: n.id, opacity: 1.0 };
  }));
  edges.update(allEdgesData.map(function(e) {
    return { id: e.id, color: { color: '#dddddd', highlight: '#888', hover: '#aaa' } };
  }));
}

network.on('selectNode', function(params) {
  if (!params.nodes.length) return;
  var sel      = params.nodes[0];
  var nbrs     = new Set(network.getConnectedNodes(sel));
  nbrs.add(sel);
  var connEdge = new Set(network.getConnectedEdges(sel));

  nodes.update(nodes.get().map(function(n) {
    return { id: n.id, opacity: nbrs.has(n.id) ? 1.0 : 0.1 };
  }));
  edges.update(edges.get().map(function(e) {
    return {
      id: e.id,
      color: connEdge.has(e.id)
        ? { color: '#666', highlight: '#333', hover: '#555' }
        : { color: 'rgba(200,200,200,0.1)' }
    };
  }));
});

network.on('deselectNode', resetHighlight);
network.on('click', function(p) {
  if (!p.nodes.length && !p.edges.length) resetHighlight();
});

// ── Filters ───────────────────────────────────────────────────────────────────
function applyFilters() {
  resetHighlight();
  var selCats  = Array.from(document.querySelectorAll('.cat-check:checked')).map(function(c){ return c.value; });
  var minArt   = parseInt(document.getElementById('minArt').value);
  var showArt  = document.getElementById('showArt').checked;

  // Determine visible challenge IDs
  var visChal = new Set();
  allNodesData.forEach(function(n) {
    if (n.grp === 'challenge') {
      if ((selCats.length === 0 || selCats.includes(n.cat)) && n.artCount >= minArt) {
        visChal.add(n.id);
      }
    }
  });

  // Article nodes visible only if showArt AND connected to a visible challenge
  var visArt = new Set();
  if (showArt) {
    allEdgesData.forEach(function(e) {
      if (visChal.has(e.to)) visArt.add(e.from);
    });
  }

  nodes.update(allNodesData.map(function(n) {
    var hidden = n.grp === 'challenge' ? !visChal.has(n.id) : !visArt.has(n.id);
    return { id: n.id, hidden: hidden };
  }));

  network.fit();
}

// ── Fullscreen ────────────────────────────────────────────────────────────────
var fsBtn = document.getElementById('fsBtn');
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.getElementById('wrapper').requestFullscreen()
      .then(function() { fsBtn.innerHTML = '✕ Salir'; network.fit(); })
      .catch(function() {
        // Fallback: fixed overlay
        var w = document.getElementById('wrapper');
        w.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;background:#f9f9f9';
        fsBtn.innerHTML = '✕ Salir';
        network.redraw(); network.fit();
      });
  } else {
    document.exitFullscreen();
    fsBtn.innerHTML = '⛶ Pantalla completa';
  }
}
document.addEventListener('fullscreenchange', function() {
  if (!document.fullscreenElement) fsBtn.innerHTML = '⛶ Pantalla completa';
});

// Convert title strings → DOM elements so vis.js renders HTML, not escaped text
var domUpdates = [];
allNodesData.forEach(function(n) {
  if (typeof n.title === 'string') {
    var el = document.createElement('div');
    el.innerHTML = n.title;
    domUpdates.push({ id: n.id, title: el });
  }
});
nodes.update(domUpdates);

network.once('stabilized', function() { network.fit(); });
</script>
</body>
</html>"""


def _prepare_data(
    df_by_paper: pd.DataFrame,
    df_challenges: pd.DataFrame,
    df_articles: pd.DataFrame,
) -> tuple[list, list, int]:
    """Return (nodes, edges, max_article_count) for vis.js."""
    df_c = df_challenges.copy()
    df_c["article_count"] = (
        pd.to_numeric(df_c["article_count"], errors="coerce").fillna(0).astype(int)
    )
    max_count = max(int(df_c["article_count"].max()), 1)
    valid_cids = set(df_c["id"].str.strip())

    art_lookup = (
        df_articles.set_index("id") if "id" in df_articles.columns else pd.DataFrame()
    )

    nodes: list[dict] = []
    edges: list[dict] = []
    edge_id = 0

    # ── Challenge nodes ──────────────────────────────────────────────────────
    for _, row in df_c.iterrows():
        cid   = str(row["id"]).strip()
        cat   = str(row.get("cat_1", "")).strip()
        color = CAT1_COLORS.get(cat, "#888888")
        count = int(row.get("article_count", 1))
        size  = 18 + int((count / max_count) * 37)

        label = str(row.get("title_en", cid))
        if len(label) > 32:
            label = label[:30] + "…"

        # Tooltip HTML — vis.js renders title as innerHTML
        spec    = str(row.get("regional_specificity", "")).strip()
        qref    = str(row.get("quick_ref_en", "")).strip()
        full_t  = str(row.get("title_en", "")).strip()
        tooltip = (
            "<div style='max-width:260px;line-height:1.55'>"
            f"<b style='font-size:13px'>{full_t}</b><br><br>"
            f"<b>Categoría:</b> {cat}<br>"
            f"<b>Artículos:</b> {count}<br>"
            f"<b>Especificidad regional:</b> {spec}<br>"
            f"<span style='color:#666;font-style:italic'>{qref}</span>"
            "</div>"
        )

        nodes.append({
            "id":       f"C:{cid}",
            "label":    label,
            "title":    tooltip,
            "color":    {"background": color, "border": "#2a2a2a",
                         "highlight":  {"background": color, "border": "#000"},
                         "hover":      {"background": color, "border": "#000"}},
            "size":     size,
            "shape":    "dot",
            "font":     {"size": 11, "color": "#111",
                         "strokeWidth": 2, "strokeColor": "#fff"},
            "borderWidth": 2,
            # Extra fields for JS filtering (not used by vis.js itself)
            "grp":      "challenge",
            "cat":      cat,
            "artCount": count,
        })

    # ── Article nodes + edges ────────────────────────────────────────────────
    added_papers: set = set()
    edges_df = df_by_paper[
        df_by_paper["challenge_id"].str.strip().isin(valid_cids)
    ]

    for _, row in edges_df.iterrows():
        pid = str(row["paper_id"]).strip()
        cid = str(row["challenge_id"]).strip()

        if pid not in added_papers:
            if pid in art_lookup.index:
                ar     = art_lookup.loc[pid]
                author = str(ar.get("author_short", pid)).strip()
                year   = int(ar["year"]) if pd.notna(ar.get("year")) else "n.d."
                typ    = str(ar.get("type", "")).strip()
                tshort = str(ar.get("title_short", "")).strip()
                tooltip = (
                    "<div style='max-width:240px;line-height:1.55'>"
                    f"<b>{author}</b> ({year})<br>"
                    f"<span style='color:#555'>{tshort}</span><br><br>"
                    f"<b>Tipo:</b> {typ}<br>"
                    f"<b>ID:</b> {pid}"
                    "</div>"
                )
            else:
                author  = pid
                tooltip = f"<b>{pid}</b>"

            nodes.append({
                "id":    f"A:{pid}",
                "label": author,
                "title": tooltip,
                "color": {"background": ARTICLE_COLOR, "border": ARTICLE_BORDER,
                          "highlight":  {"background": "#8fafd4", "border": "#2a4f7c"},
                          "hover":      {"background": "#8fafd4", "border": "#2a4f7c"}},
                "size":  10,
                "shape": "square",
                "font":  {"size": 9, "color": "#333",
                          "strokeWidth": 1, "strokeColor": "#fff"},
                "borderWidth": 1,
                "grp":      "article",
                "cat":      "article",
                "artCount": 0,
            })
            added_papers.add(pid)

        edges.append({
            "id":   edge_id,
            "from": f"A:{pid}",
            "to":   f"C:{cid}",
            "color": {"color": "#dddddd", "highlight": "#888", "hover": "#aaa"},
        })
        edge_id += 1

    return nodes, edges, max_count


def _build_html(nodes: list, edges: list, max_count: int) -> str:
    # Category checkboxes (generated in Python, substituted into template)
    checkboxes = ""
    for cat, color in CAT1_COLORS.items():
        checkboxes += (
            f'<label class="cat-label">'
            f'<input type="checkbox" class="cat-check" value="{cat}" checked>'
            f'<span class="cat-dot" style="background:{color}"></span>'
            f'{cat}</label>'
        )

    html = (
        _HTML_TEMPLATE
        .replace("__NODES_JSON__",   json.dumps(nodes,  ensure_ascii=False))
        .replace("__EDGES_JSON__",   json.dumps(edges,  ensure_ascii=False))
        .replace("__CAT_CHECKBOXES__", checkboxes)
        .replace("__MAX_COUNT__",    str(max_count))
    )
    return html


def render_network_graph(
    df_by_paper: pd.DataFrame,
    df_challenges: pd.DataFrame,
    df_articles: pd.DataFrame,
    # filter params kept for API compatibility but filters now live inside the HTML
    filter_cat1: list | None = None,
    min_articles: int = 1,
    show_articles: bool = True,
) -> None:
    nodes, edges, max_count = _prepare_data(df_by_paper, df_challenges, df_articles)

    if not nodes:
        st.info("No hay datos para mostrar.")
        return

    n_challenge = sum(1 for n in nodes if n["grp"] == "challenge")
    n_article   = sum(1 for n in nodes if n["grp"] == "article")
    st.caption(
        f"**{n_challenge}** retos · **{n_article}** artículos · **{len(edges)}** conexiones  "
        f"— usa los filtros dentro del grafo o el botón de pantalla completa"
    )

    html = _build_html(nodes, edges, max_count)

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".html", mode="w", encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_path = f.name

    try:
        with open(tmp_path, "r", encoding="utf-8") as f:
            rendered = f.read()
        components.html(rendered, height=700, scrolling=False)
    finally:
        os.unlink(tmp_path)


def render_legend() -> None:
    """Kept for API compatibility — legend is now embedded inside the graph HTML."""
    pass
