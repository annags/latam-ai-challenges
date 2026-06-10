"""
Network graph — Cytoscape.js 3.28 con layout cose built-in (sin dependencias CDN extras).
Uses __PLACEHOLDER__ substitution to avoid f-string / JS-brace conflicts.
"""
import json
import os
import tempfile
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

CAT1_COLORS = {
    "Socio-technical": "#7F77DD",
    "Ethical":         "#00BF63",
    "Institutional":   "#004AAD",
}
ARTICLE_COLOR  = "#6c8ebf"
ARTICLE_BORDER = "#3a5f8a"

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    overflow: hidden;
    background: #f4f5f9;
  }
  #wrapper { position: relative; width: 100%; height: 100vh; }
  #cy      { width: 100%; height: 100vh; }

  /* ── Tooltip ──────────────────────────────────────────────── */
  #tooltip {
    display: none;
    position: fixed;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 9px;
    padding: 10px 13px;
    box-shadow: 0 6px 22px rgba(0,0,0,0.13);
    font-size: 12.5px;
    color: #1a1a1a;
    max-width: 265px;
    line-height: 1.55;
    z-index: 1000;
    pointer-events: none;
  }
  #tooltip .t-title { font-weight: 700; font-size: 13px; margin-bottom: 5px; }
  #tooltip .t-row   { margin-bottom: 2px; color: #444; }
  #tooltip .t-label { font-weight: 600; color: #222; }
  #tooltip hr { border: none; border-top: 1px solid #eee; margin: 6px 0; }

  /* ── Controls ─────────────────────────────────────────────── */
  #controls {
    position: absolute; top: 12px; left: 12px; z-index: 300;
    background: rgba(255,255,255,0.97);
    border: 1px solid #e2e2e2;
    border-radius: 12px; padding: 14px 16px; width: 218px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.10);
  }
  #controls h4 {
    font-size: 12px; font-weight: 700; color: #222; margin-bottom: 10px;
    border-bottom: 1px solid #eee; padding-bottom: 6px;
  }
  .sec {
    font-size: 10px; font-weight: 700; color: #aaa;
    text-transform: uppercase; letter-spacing: 0.7px;
    margin: 11px 0 5px;
  }
  .cat-label {
    display: flex; align-items: center; gap: 7px;
    cursor: pointer; margin-bottom: 5px; font-size: 12px; color: #333;
  }
  .cat-label input { cursor: pointer; }
  .cat-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  input[type=range] { width: 100%; accent-color: #004AAD; margin: 4px 0; }
  .srow { display: flex; justify-content: space-between; font-size: 10px; color: #bbb; }
  .toggle-label {
    display: flex; align-items: center; gap: 7px;
    cursor: pointer; font-size: 12px; color: #333; margin-top: 9px;
  }
  .toggle-label input { cursor: pointer; }
  #applyBtn {
    width: 100%; margin-top: 11px; padding: 7px 0;
    background: #004AAD; color: #fff; border: none;
    border-radius: 7px; cursor: pointer; font-size: 12px; font-weight: 700;
    letter-spacing: 0.2px; transition: background 0.15s;
  }
  #applyBtn:hover { background: #003a8a; }
  #layoutBtn {
    width: 100%; margin-top: 5px; padding: 6px 0;
    background: #f0f0f0; color: #444;
    border: 1px solid #ddd; border-radius: 7px;
    cursor: pointer; font-size: 11px; transition: background 0.15s;
  }
  #layoutBtn:hover { background: #e3e3e3; }

  /* ── Top buttons ──────────────────────────────────────────── */
  .top-btn {
    position: absolute; top: 12px; z-index: 300;
    background: rgba(255,255,255,0.97);
    border: 1px solid #e2e2e2;
    border-radius: 8px; padding: 7px 13px; cursor: pointer;
    font-size: 12px; font-weight: 600; color: #333;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    display: flex; align-items: center; gap: 5px;
    transition: background 0.15s;
  }
  .top-btn:hover { background: #efefef; }
  #fsBtn  { right: 12px; }
  #fitBtn { right: 158px; }

  /* ── Legend ───────────────────────────────────────────────── */
  #legend {
    position: absolute; bottom: 14px; left: 12px; z-index: 300;
    background: rgba(255,255,255,0.97);
    border: 1px solid #e2e2e2;
    border-radius: 10px; padding: 11px 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  }
  .leg-item {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 5px; font-size: 11.5px; color: #333;
  }
  .l-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .l-sq  { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
  .leg-note { font-size: 10px; color: #bbb; margin-top: 8px; line-height: 1.5; }

  /* ── Loading ──────────────────────────────────────────────── */
  #loading {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    font-size: 13px; color: #999; z-index: 200;
    background: rgba(244,245,249,0.85);
    padding: 12px 20px; border-radius: 8px;
  }
</style>
</head>
<body>
<div id="wrapper">
  <div id="cy"></div>
  <div id="tooltip"></div>
  <div id="loading">Calculando disposición…</div>

  <!-- Controls -->
  <div id="controls">
    <h4>🔍 Filtros</h4>
    <div class="sec">Categoría</div>
    __CAT_CHECKBOXES__
    <div class="sec">Mín. artículos por reto</div>
    <input type="range" id="minArt" min="1" max="__MAX_COUNT__" value="1"
           oninput="document.getElementById('minVal').textContent=this.value">
    <div class="srow">
      <span>1</span><b><span id="minVal">1</span></b><span>__MAX_COUNT__</span>
    </div>
    <label class="toggle-label">
      <input type="checkbox" id="showArt" checked>&nbsp;Mostrar artículos
    </label>
    <button id="applyBtn"  onclick="applyFilters()">Aplicar filtros</button>
    <button id="layoutBtn" onclick="runLayout()">↺ Reorganizar</button>
  </div>

  <!-- Top buttons -->
  <button class="top-btn" id="fitBtn" onclick="cy.fit(undefined,40)">⊙ Centrar</button>
  <button class="top-btn" id="fsBtn"  onclick="toggleFullscreen()">⛶ Pantalla completa</button>

  <!-- Legend -->
  <div id="legend">
    <div class="leg-item"><span class="l-dot" style="background:#7F77DD"></span>Socio-technical</div>
    <div class="leg-item"><span class="l-dot" style="background:#00BF63"></span>Ethical</div>
    <div class="leg-item"><span class="l-dot" style="background:#004AAD"></span>Institutional</div>
    <div class="leg-item"><span class="l-sq"  style="background:#6c8ebf"></span>Artículo (hover para ver)</div>
    <div class="leg-note">
      Tamaño del círculo = nº artículos citados<br>
      Clic en nodo → resalta conexiones
    </div>
  </div>
</div>

<script src="https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
<script>
// ── Data ─────────────────────────────────────────────────────────────────────
var allNodes = __NODES_JSON__;
var allEdges = __EDGES_JSON__;

// ── Graph ─────────────────────────────────────────────────────────────────────
var cy = cytoscape({
  container: document.getElementById('cy'),
  elements: { nodes: allNodes, edges: allEdges },
  style: [
    /* base node */
    {
      selector: 'node',
      style: {
        'background-color':     'data(color)',
        'border-color':         'data(borderColor)',
        'border-width':         2,
        'width':                'data(size)',
        'height':               'data(size)',
        'label':                'data(label)',
        'font-size':            11,
        'font-family':          '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
        'color':                '#111',
        'text-outline-color':   '#fff',
        'text-outline-width':   2,
        'text-valign':          'center',
        'text-halign':          'center',
        'text-wrap':            'wrap',
        'text-max-width':       75,
        'min-zoomed-font-size': 6
      }
    },
    /* article nodes — smaller, no label shown (tooltip on hover) */
    {
      selector: 'node[grp = "article"]',
      style: {
        'shape':      'round-rectangle',
        'label':      '',
        'border-width': 1.5
      }
    },
    /* edges */
    {
      selector: 'edge',
      style: {
        'width':       1.2,
        'line-color':  '#c8c8c8',
        'curve-style': 'bezier',
        'opacity':     0.55
      }
    },
    /* highlight states */
    {
      selector: '.faded',
      style: { 'opacity': 0.06 }
    },
    {
      selector: 'node.highlighted',
      style: {
        'opacity':      1,
        'border-width': 3.5,
        'border-color': '#111',
        'z-index':      100
      }
    },
    {
      selector: 'node[grp = "article"].highlighted',
      style: {
        'label':     'data(label)',
        'font-size': 9,
        'text-outline-width': 1.5,
        'text-valign': 'bottom',
        'text-margin-y': 5
      }
    },
    {
      selector: 'edge.highlighted',
      style: {
        'opacity':    1,
        'line-color': '#555',
        'width':      2
      }
    }
  ],
  minZoom: 0.2,
  maxZoom: 4.0,
  userZoomingEnabled: true,
  userPanningEnabled: true
});

// ── Layout ────────────────────────────────────────────────────────────────────
var LAYOUT_OPTS = {
  name:            'cose',
  animate:         true,
  animationThreshold: 250,
  refresh:         20,
  fit:             true,
  padding:         55,
  randomize:       true,
  boundingBox:     { x1: 0, y1: 0, w: 2200, h: 1400 },
  componentSpacing: 120,
  nodeRepulsion:   650000,
  nodeOverlap:     20,
  idealEdgeLength: 110,
  edgeElasticity:  100,
  nestingFactor:   5,
  gravity:         80,
  numIter:         2000,
  initialTemp:     500,
  coolingFactor:   0.95,
  minTemp:         1.0
};

function runLayout(opts) {
  var visible = cy.elements().filter(function(el) {
    return el.style('display') !== 'none';
  });
  var lo = Object.assign({}, LAYOUT_OPTS, opts || {});
  var l  = visible.length > 0 ? visible.layout(lo) : cy.layout(lo);
  l.on('layoutstop', function() {
    document.getElementById('loading').style.display = 'none';
    cy.fit(undefined, 40);
  });
  l.run();
}

runLayout();

// ── Tooltip ───────────────────────────────────────────────────────────────────
var tip = document.getElementById('tooltip');

cy.on('mouseover', 'node', function(e) {
  tip.innerHTML = e.target.data('tooltip');
  tip.style.display = 'block';
});
document.addEventListener('mousemove', function(e) {
  if (tip.style.display !== 'none') {
    var x = e.clientX + 16;
    var y = e.clientY - 10;
    if (x + 275 > window.innerWidth)  x = e.clientX - 285;
    if (y + 160 > window.innerHeight) y = e.clientY - 150;
    tip.style.left = x + 'px';
    tip.style.top  = y + 'px';
  }
});
cy.on('mouseout', 'node', function() {
  tip.style.display = 'none';
});

// ── Neighbour highlight ───────────────────────────────────────────────────────
cy.on('tap', 'node', function(e) {
  var node  = e.target;
  var nbhd  = node.closedNeighborhood();
  cy.elements().removeClass('highlighted faded');
  cy.elements().not(nbhd).addClass('faded');
  nbhd.addClass('highlighted');
});
cy.on('tap', function(e) {
  if (e.target === cy) {
    cy.elements().removeClass('highlighted faded');
  }
});

// ── Filters ───────────────────────────────────────────────────────────────────
function applyFilters() {
  cy.elements().removeClass('highlighted faded');
  tip.style.display = 'none';

  var selCats = Array.from(
    document.querySelectorAll('.cat-check:checked')
  ).map(function(c) { return c.value; });
  var minArt  = parseInt(document.getElementById('minArt').value, 10);
  var showArt = document.getElementById('showArt').checked;

  cy.nodes().forEach(function(n) {
    if (n.data('grp') !== 'challenge') return;
    var vis = (!selCats.length || selCats.includes(n.data('cat')))
              && n.data('artCount') >= minArt;
    n.style('display', vis ? 'element' : 'none');
  });

  cy.nodes().forEach(function(n) {
    if (n.data('grp') !== 'article') return;
    if (!showArt) { n.style('display', 'none'); return; }
    var ok = n.connectedEdges().some(function(e) {
      return e.target().style('display') !== 'none';
    });
    n.style('display', ok ? 'element' : 'none');
  });

  cy.edges().forEach(function(e) {
    var hide = e.source().style('display') === 'none'
            || e.target().style('display') === 'none';
    e.style('display', hide ? 'none' : 'element');
  });

  var vis = cy.elements().filter(function(el) {
    return el.style('display') !== 'none';
  });
  if (vis.length) cy.fit(vis, 40);
}

// Re-layout button (already defined as runLayout above)
document.getElementById('layoutBtn').addEventListener('click', function() {
  runLayout({ randomize: true });
});

// ── Fullscreen ────────────────────────────────────────────────────────────────
var fsBtn = document.getElementById('fsBtn');
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.getElementById('wrapper').requestFullscreen()
      .then(function() {
        fsBtn.innerHTML = '✕ Salir';
        cy.resize(); cy.fit();
      })
      .catch(function() {
        var w = document.getElementById('wrapper');
        w.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;background:#f4f5f9';
        fsBtn.innerHTML = '✕ Salir';
        cy.resize(); cy.fit();
      });
  } else {
    document.exitFullscreen();
  }
}
document.addEventListener('fullscreenchange', function() {
  if (!document.fullscreenElement) {
    fsBtn.innerHTML = '⛶ Pantalla completa';
    cy.resize(); cy.fit();
  }
});
</script>
</body>
</html>"""


def _prepare_data(
    df_by_paper: pd.DataFrame,
    df_challenges: pd.DataFrame,
    df_articles: pd.DataFrame,
) -> tuple[list, list, int]:
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
        size  = 38 + int((count / max_count) * 45)

        label = str(row.get("title_en", cid))
        if len(label) > 22:
            label = label[:20] + "…"

        spec   = str(row.get("regional_specificity", "")).strip()
        full_t = str(row.get("title_en", "")).strip()
        tooltip = (
            f'<div class="t-title">{full_t}</div>'
            f'<hr>'
            f'<div class="t-row"><span class="t-label">Categoría:</span> {cat}</div>'
            f'<div class="t-row"><span class="t-label">Artículos:</span> {count}</div>'
            f'<div class="t-row"><span class="t-label">Especificidad:</span> {spec}</div>'
        )

        nodes.append({
            "data": {
                "id":          f"C:{cid}",
                "label":       label,
                "tooltip":     tooltip,
                "color":       color,
                "borderColor": "#1a1a1a",
                "size":        size,
                "grp":         "challenge",
                "cat":         cat,
                "artCount":    count,
            }
        })

    # ── Article nodes + edges ────────────────────────────────────────────────
    added_papers: set = set()
    bp = df_by_paper.copy()
    if "challenge_id" not in bp.columns and "id" in bp.columns:
        bp = bp.rename(columns={"id": "challenge_id"})

    for _, row in bp.iterrows():
        pid = str(row.get("paper_id", "")).strip()
        cid = str(row.get("challenge_id", "")).strip()
        if not pid or not cid or cid not in valid_cids:
            continue

        if pid not in added_papers:
            if not art_lookup.empty and pid in art_lookup.index:
                ar    = art_lookup.loc[pid]
                qref  = str(ar.get("quick_ref", ar.get("author_short", pid))).strip()
                year  = int(ar["year"]) if pd.notna(ar.get("year")) else "n.d."
                typ   = str(ar.get("type", "")).strip()
                title = str(ar.get("title", ar.get("title_short", ""))).strip()
                tooltip = (
                    f'<div class="t-title">{qref} ({year})</div>'
                    f'<hr>'
                    f'<div class="t-row" style="color:#555;margin-bottom:6px">{title[:80]}{"…" if len(title)>80 else ""}</div>'
                    f'<div class="t-row"><span class="t-label">Tipo:</span> {typ}</div>'
                )
                node_label = qref
            else:
                node_label = pid
                tooltip    = f'<div class="t-title">{pid}</div>'

            nodes.append({
                "data": {
                    "id":          f"A:{pid}",
                    "label":       node_label,
                    "tooltip":     tooltip,
                    "color":       ARTICLE_COLOR,
                    "borderColor": ARTICLE_BORDER,
                    "size":        18,
                    "grp":         "article",
                    "cat":         "article",
                    "artCount":    0,
                }
            })
            added_papers.add(pid)

        edges.append({
            "data": {
                "id":     f"e{edge_id}",
                "source": f"A:{pid}",
                "target": f"C:{cid}",
            }
        })
        edge_id += 1

    return nodes, edges, max_count


def _build_html(nodes: list, edges: list, max_count: int) -> str:
    checkboxes = ""
    for cat, color in CAT1_COLORS.items():
        checkboxes += (
            f'<label class="cat-label">'
            f'<input type="checkbox" class="cat-check" value="{cat}" checked>'
            f'<span class="cat-dot" style="background:{color}"></span>'
            f'{cat}</label>'
        )
    return (
        _HTML_TEMPLATE
        .replace("__NODES_JSON__",     json.dumps(nodes,  ensure_ascii=False))
        .replace("__EDGES_JSON__",     json.dumps(edges,  ensure_ascii=False))
        .replace("__CAT_CHECKBOXES__", checkboxes)
        .replace("__MAX_COUNT__",      str(max_count))
    )


def render_network_graph(
    df_by_paper: pd.DataFrame,
    df_challenges: pd.DataFrame,
    df_articles: pd.DataFrame,
    filter_cat1: list | None = None,
    min_articles: int = 1,
    show_articles: bool = True,
) -> None:
    nodes, edges, max_count = _prepare_data(df_by_paper, df_challenges, df_articles)

    if not nodes:
        st.info("No hay datos para mostrar.")
        return

    n_challenge = sum(1 for n in nodes if n["data"]["grp"] == "challenge")
    n_article   = sum(1 for n in nodes if n["data"]["grp"] == "article")
    st.caption(
        f"**{n_challenge}** retos · **{n_article}** artículos · **{len(edges)}** conexiones  "
        f"— filtra, haz clic en un nodo para resaltar sus conexiones, usa ⛶ para pantalla completa"
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
    """Kept for API compatibility — legend is embedded inside the graph HTML."""
    pass
