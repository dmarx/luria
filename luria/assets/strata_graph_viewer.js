// Vendored from strata-g's graph export viewer ([[SG-ADR-237]], [[SG-ADR-238]]).
//
// PROVENANCE — this file is generated, not written here. It is the payload
// strata-g's `Canvas — embeddable snippet` export inlines, lifted so that
// `luria site` can serve one copy for the whole site instead of one per page.
//
//   source:   https://github.com/dmarx/strata-g
//             web/src/graph/export/webappViewer.ts  (viewerScript())
//   revision: 6870ddf7f08edfdecfb54053033308a5e57c9cff
//   pinned:   see LINEAGE_VIEWER_SHA256 in luria/site_graph.py
//
// Do not edit. To update: re-emit from strata-g, drop the file here, and
// update the pin — the test that compares them is what tells you the two
// have drifted (the same offline-drift discipline [[ADR-016]] applies to
// remote document content).
//
// The body below is strata-g's source, verbatim. It cites strata-g's own
// decisions by bare code, which are not this record's:
// unresolved-ok-file: ADR-237 — strata-g's numbering, inside its own source
// unresolved-ok-file: ADR-238 — the same
// unresolved-ok-file: ADR-170 — the same

(function () {
  "use strict";
  var TAG = "strata-g-graph";
  // Idempotent: two pasted embed fragments each carry this script, and the
  // second must not throw on a duplicate customElements.define.
  if (window.customElements && customElements.get(TAG)) return;

  var STYLE = "\n:host {\n  /* The host sizes the embed; these are defaults it can override, because a\n     host-page rule beats a :host rule. */\n  display: block;\n  height: 480px;\n  contain: content;\n}\n*, *::before, *::after { box-sizing: border-box; }\n.wrap {\n  display: flex; height: 100%; overflow: hidden;\n  font: 13px/1.5 ui-sans-serif, system-ui, -apple-system, \"Segoe UI\", sans-serif;\n  background: var(--strata-bg); color: var(--strata-fg);\n}\n.stage { position: relative; flex: 1; min-width: 0; }\ncanvas { display: block; width: 100%; height: 100%; touch-action: none; cursor: grab; }\ncanvas.dragging { cursor: grabbing; }\n.panel {\n  width: 300px; flex: none; padding: 14px; overflow-y: auto;\n  background: color-mix(in srgb, var(--strata-fg) 6%, var(--strata-bg));\n  border-left: 1px solid color-mix(in srgb, var(--strata-fg) 18%, transparent);\n}\n/* Narrow is decided from the HOST's width, not the viewport: a 400px embed in\n   a wide page has to stack, and a media query would never know. */\n.wrap.narrow { flex-direction: column; }\n.wrap.narrow .panel {\n  width: auto; max-height: 45%; border-left: none;\n  border-top: 1px solid color-mix(in srgb, var(--strata-fg) 18%, transparent);\n}\nh1 { font-size: 15px; margin: 0 0 2px; font-weight: 600; overflow-wrap: anywhere; }\n.muted { opacity: 0.65; }\n.counts { font-size: 12px; margin: 0 0 12px; }\ninput[type=\"search\"] {\n  width: 100%; padding: 6px 8px; margin-bottom: 10px; font: inherit;\n  color: inherit; background: var(--strata-bg); border-radius: 4px;\n  border: 1px solid color-mix(in srgb, var(--strata-fg) 25%, transparent);\n}\ninput[type=\"search\"]:focus {\n  outline: 2px solid color-mix(in srgb, var(--strata-fg) 40%, transparent); outline-offset: -1px;\n}\n.hits { list-style: none; margin: 0 0 12px; padding: 0; max-height: 30%; overflow-y: auto; }\n.hits li { padding: 4px 6px; border-radius: 3px; cursor: pointer; overflow-wrap: anywhere; }\n.hits li:hover, .hits li:focus-visible { background: color-mix(in srgb, var(--strata-fg) 12%, transparent); }\n.detail h2 { font-size: 13px; margin: 0 0 6px; overflow-wrap: anywhere; }\n.detail h2 a { color: inherit; }\n.legend { list-style: none; margin: 0 0 12px; padding: 0; font-size: 12px; }\n.legend li { display: flex; align-items: center; gap: 6px; padding: 2px 0; }\n.legend .swatch { width: 18px; height: 3px; border-radius: 2px; flex: none; }\n.detail p { margin: 0 0 6px; }\n.detail table { width: 100%; border-collapse: collapse; }\n.detail th, .detail td {\n  text-align: left; vertical-align: top; padding: 3px 4px; font-weight: normal;\n  border-top: 1px solid color-mix(in srgb, var(--strata-fg) 12%, transparent); overflow-wrap: anywhere;\n}\n.detail th { width: 38%; opacity: 0.7; }\n.controls { position: absolute; left: 10px; bottom: 10px; display: flex; gap: 6px; }\n.controls button {\n  font: inherit; color: inherit; padding: 4px 10px; border-radius: 4px; cursor: pointer;\n  background: color-mix(in srgb, var(--strata-fg) 10%, var(--strata-bg));\n  border: 1px solid color-mix(in srgb, var(--strata-fg) 25%, transparent);\n}\n.controls button:hover { background: color-mix(in srgb, var(--strata-fg) 18%, var(--strata-bg)); }\n";

  // A URL is only ever written to an href if it is http(s).
  //
  // The producer sanitizes too (strata-g's graph/nodeContent.ts safeLinkUrl),
  // but the producer is not always this app: an exported view can be built by
  // anything, and the data island is plain text in a file people hand-edit. A
  // javascript: href executes on click, so the check lives on BOTH sides of
  // the boundary and this is the side that is always present.
  function safeHref(url) {
    if (typeof url !== "string") return null;
    var s = url.trim();
    var lower = s.toLowerCase();
    // Deliberately indexOf rather than a regex. A backslash here is inside a
    // TEMPLATE LITERAL, so a /^https?:[escaped-slashes]/ collapses on the way
    // out to /^https?:/ followed by a division — valid JavaScript that quietly
    // returns the regex instead of a boolean. That shipped once and the unit
    // test that parses the payload could not see it, because it parsed. No
    // escapes here means no such hazard.
    return lower.indexOf("http://") === 0 || lower.indexOf("https://") === 0 ? s : null;
  }

  function buildShell(root, data) {
    var style = document.createElement("style");
    style.textContent = STYLE;
    root.appendChild(style);

    var wrap = document.createElement("div");
    wrap.className = "wrap";
    wrap.style.setProperty("--strata-bg", data.background);
    wrap.style.setProperty("--strata-fg", data.labelColor);

    var stage = document.createElement("div");
    stage.className = "stage";
    var canvas = document.createElement("canvas");
    stage.appendChild(canvas);

    var controls = document.createElement("div");
    controls.className = "controls";
    var fitBtn = document.createElement("button");
    fitBtn.type = "button";
    fitBtn.textContent = "Fit";
    var clearBtn = document.createElement("button");
    clearBtn.type = "button";
    clearBtn.textContent = "Clear";
    controls.appendChild(fitBtn);
    controls.appendChild(clearBtn);
    stage.appendChild(controls);

    var panel = document.createElement("aside");
    panel.className = "panel";
    var title = document.createElement("h1");
    title.textContent = data.title || "Graph";
    var counts = document.createElement("p");
    counts.className = "counts muted";
    counts.textContent = data.nodes.length.toLocaleString() + " nodes / " +
      data.edges.length.toLocaleString() + " edges";
    var search = document.createElement("input");
    search.type = "search";
    search.placeholder = "Search labels...";
    search.setAttribute("aria-label", "Search labels");
    search.autocomplete = "off";
    search.spellcheck = false;
    var hits = document.createElement("ul");
    hits.className = "hits";
    hits.setAttribute("aria-label", "Search results");
    var detail = document.createElement("div");
    detail.className = "detail";

    // Edge-colour legend. Present only when the export names its relations —
    // a typed record graph does; a data graph coloured by depth or weight has
    // nothing to list, and an unlabelled swatch row would be noise.
    var legend = null;
    if (data.legend && data.legend.length) {
      legend = document.createElement("ul");
      legend.className = "legend";
      legend.setAttribute("aria-label", "Edge relations");
      data.legend.forEach(function (entry) {
        var li = document.createElement("li");
        var swatch = document.createElement("span");
        swatch.className = "swatch";
        swatch.style.background = entry.color;
        li.appendChild(swatch);
        var text = document.createElement("span");
        text.textContent = entry.label;
        li.appendChild(text);
        legend.appendChild(li);
      });
    }
    panel.appendChild(title);
    panel.appendChild(counts);
    panel.appendChild(search);
    panel.appendChild(hits);
    if (legend) panel.appendChild(legend);
    panel.appendChild(detail);

    wrap.appendChild(stage);
    wrap.appendChild(panel);
    root.appendChild(wrap);
    return { wrap: wrap, canvas: canvas, search: search, hits: hits,
             detail: detail, fitBtn: fitBtn, clearBtn: clearBtn };
  }

  // Mount one graph into 'root' (a shadow root). Returns a handle; nothing is
  // written to any global from in here — the caller decides what to publish.
  function mount(root, data, host) {
    var nodes = data.nodes, edges = data.edges;
    var byId = {};
    nodes.forEach(function (n, i) { n.i = i; byId[n.id] = n; });

    var neighbours = {};
    nodes.forEach(function (n) { neighbours[n.id] = {}; });
    edges.forEach(function (e) {
      if (!byId[e.source] || !byId[e.target]) return;
      neighbours[e.source][e.target] = true;
      neighbours[e.target][e.source] = true;
    });

    var el = buildShell(root, data);
    var canvas = el.canvas;
    var ctx = canvas.getContext("2d");
    var camera = { x: 0, y: 0, scale: 1 };
    // The scale "Fit" landed on, and how authored sizes map to pixels there.
    // Neither the coordinate span nor the size values have a fixed relationship
    // to pixels: positions come from a force layout and span 50 units or 5000,
    // sizes come from a Size-by binding and reach the tens. Radius as
    // size x scale therefore gives anything from invisible dots to one node
    // filling the frame. So fit sets the scale, sizeUnit caps the widest node,
    // and zooming scales both from there.
    var baseScale = 1, sizeUnit = 1;
    var MAX_NODE_FRACTION = 0.055;
    var hovered = null, selected = null, dpr = 1;

    function width() { return canvas.clientWidth; }
    function height() { return canvas.clientHeight; }

    function resize() {
      // The narrow switch reads the ELEMENT, not the viewport.
      el.wrap.classList.toggle("narrow", (host ? host.clientWidth : width()) < 640);
      dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(width() * dpr));
      canvas.height = Math.max(1, Math.floor(height() * dpr));
      draw();
    }

    function toScreen(n) {
      return {
        x: (n.x - camera.x) * camera.scale + width() / 2,
        y: (n.y - camera.y) * camera.scale + height() / 2
      };
    }

    function fit() {
      if (!nodes.length) { camera = { x: 0, y: 0, scale: 1 }; baseScale = 1; draw(); return; }
      var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, maxSize = 0;
      nodes.forEach(function (n) {
        if (n.x < minX) minX = n.x;
        if (n.x > maxX) maxX = n.x;
        if (n.y < minY) minY = n.y;
        if (n.y > maxY) maxY = n.y;
        if (n.size > maxSize) maxSize = n.size;
      });
      camera.x = (minX + maxX) / 2;
      camera.y = (minY + maxY) / 2;
      var cap = MAX_NODE_FRACTION * Math.min(width(), height());
      sizeUnit = maxSize > 0 ? Math.min(1, cap / maxSize) : 1;
      // The bounding box is of node CENTRES, so the margin must cover the widest
      // node's radius as well as the breathing room — in pixels, which is what a
      // node's radius is at the fitted scale.
      var margin = 24 + maxSize * sizeUnit;
      var spanX = maxX - minX, spanY = maxY - minY;
      var scale = Math.min(
        (width() - margin * 2) / Math.max(spanX, 1e-6),
        (height() - margin * 2) / Math.max(spanY, 1e-6)
      );
      // One node (or a degenerate row/column) has no extent to fit to; scale 1
      // draws it at its authored size rather than at infinity.
      if (!isFinite(scale) || scale <= 0 || (spanX < 1e-6 && spanY < 1e-6)) scale = 1;
      camera.scale = scale;
      baseScale = scale;
      draw();
    }

    function zoomFactor() { return camera.scale / baseScale; }
    function nodeRadius(n) { return Math.max(1.5, n.size * sizeUnit * zoomFactor()); }

    function dimmed(id) {
      if (hovered === null) return false;
      return id !== hovered && !neighbours[hovered][id];
    }

    function draw() {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width(), height());

      for (var e = 0; e < edges.length; e++) {
        var edge = edges[e];
        var s = byId[edge.source], t = byId[edge.target];
        if (!s || !t) continue;
        var faded = dimmed(edge.source) && dimmed(edge.target);
        var a = toScreen(s), b = toScreen(t);
        // Full alpha for a normal edge: the resolved colour ALREADY carries the
        // layer's edge opacity (these arrive as #rrggbbaa), so a second
        // multiplier draws them fainter than the app does.
        ctx.globalAlpha = faded ? 0.12 : 1;
        ctx.strokeStyle = edge.color;
        ctx.lineWidth = Math.max(0.5, edge.size * Math.max(sizeUnit, 0.35) * zoomFactor());
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        if (edge.curvature) {
          var mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
          var dx = b.x - a.x, dy = b.y - a.y;
          ctx.quadraticCurveTo(mx - dy * edge.curvature, my + dx * edge.curvature, b.x, b.y);
        } else {
          ctx.lineTo(b.x, b.y);
        }
        ctx.stroke();
        if (edge.directed) {
          var ang = Math.atan2(b.y - a.y, b.x - a.x);
          var r = nodeRadius(t) + 1;
          var tipX = b.x - Math.cos(ang) * r, tipY = b.y - Math.sin(ang) * r;
          var head = Math.max(4, ctx.lineWidth * 3);
          ctx.fillStyle = edge.color;
          ctx.beginPath();
          ctx.moveTo(tipX, tipY);
          ctx.lineTo(tipX - Math.cos(ang - 0.4) * head, tipY - Math.sin(ang - 0.4) * head);
          ctx.lineTo(tipX - Math.cos(ang + 0.4) * head, tipY - Math.sin(ang + 0.4) * head);
          ctx.closePath();
          ctx.fill();
        }
      }

      var labelled = [];
      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i], p = toScreen(n), r = nodeRadius(n);
        if (p.x < -r || p.y < -r || p.x > width() + r || p.y > height() + r) continue;
        var isDim = dimmed(n.id);
        ctx.globalAlpha = isDim ? 0.15 : 1;
        ctx.fillStyle = n.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fill();
        if (n.id === selected || n.id === hovered) {
          ctx.globalAlpha = 1;
          ctx.strokeStyle = data.labelColor;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
        if (!isDim && n.label && (r > 6 || n.id === hovered || n.id === selected)) {
          labelled.push({ n: n, p: p, r: r });
        }
      }

      ctx.globalAlpha = 1;
      ctx.font = "12px ui-sans-serif, system-ui, sans-serif";
      ctx.textBaseline = "middle";
      ctx.lineJoin = "round";
      for (var l = 0; l < labelled.length; l++) {
        var item = labelled[l];
        ctx.lineWidth = 3;
        ctx.strokeStyle = data.background;
        ctx.strokeText(item.n.label, item.p.x + item.r + 4, item.p.y);
        ctx.fillStyle = data.labelColor;
        ctx.fillText(item.n.label, item.p.x + item.r + 4, item.p.y);
      }
    }

    function nodeAt(px, py) {
      for (var i = nodes.length - 1; i >= 0; i--) {
        var n = nodes[i], p = toScreen(n), r = Math.max(nodeRadius(n), 4);
        if ((px - p.x) * (px - p.x) + (py - p.y) * (py - p.y) <= r * r) return n;
      }
      return null;
    }

    function show(node) {
      selected = node ? node.id : null;
      el.detail.textContent = "";
      if (!node) {
        var hint = document.createElement("p");
        hint.className = "muted";
        // The empty state has to describe what a click actually does. Under
        // navigateOnClick it opens the node's page and the inspector never
        // appears, so promising data here is a hint that is never kept.
        hint.textContent = data.navigateOnClick
          ? "Click a node to open it."
          : "Click a node to see its data.";
        el.detail.appendChild(hint);
        draw();
        return;
      }
      var h = document.createElement("h2");
      if (safeHref(node.url)) {
        // The node's bound Link-by target (ADR-170), carried into the export.
        // An anchor rather than a click handler: middle-click, ctrl-click and
        // "copy link" are then the browser's job, as a reader expects.
        var a = document.createElement("a");
        a.href = safeHref(node.url);
        a.textContent = node.label || node.id;
        a.rel = "noopener noreferrer";
        h.appendChild(a);
      } else {
        h.textContent = node.label || node.id;
      }
      el.detail.appendChild(h);
      var keys = Object.keys(node.attrs);
      if (!keys.length) {
        var none = document.createElement("p");
        none.className = "muted";
        none.textContent = "No data columns.";
        el.detail.appendChild(none);
      }
      var table = document.createElement("table");
      for (var k = 0; k < keys.length; k++) {
        var row = document.createElement("tr");
        var th = document.createElement("th");
        th.textContent = keys[k];
        var td = document.createElement("td");
        var v = node.attrs[keys[k]];
        td.textContent = v === null || v === undefined ? "∅"
          : typeof v === "object" ? JSON.stringify(v) : String(v);
        row.appendChild(th);
        row.appendChild(td);
        table.appendChild(row);
      }
      el.detail.appendChild(table);
      draw();
    }

    function centreOn(node) {
      camera.x = node.x;
      camera.y = node.y;
      show(node);
    }

    function runSearch() {
      var q = el.search.value.trim().toLowerCase();
      el.hits.textContent = "";
      if (!q) return;
      var found = nodes.filter(function (n) {
        return (n.label || n.id).toLowerCase().indexOf(q) !== -1;
      }).slice(0, 40);
      found.forEach(function (n) {
        var li = document.createElement("li");
        li.textContent = n.label || n.id;
        li.tabIndex = 0;
        li.addEventListener("click", function () { centreOn(n); });
        li.addEventListener("keydown", function (ev) {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); centreOn(n); }
        });
        el.hits.appendChild(li);
      });
      if (!found.length) {
        var li2 = document.createElement("li");
        li2.className = "muted";
        li2.textContent = "No match";
        el.hits.appendChild(li2);
      }
    }

    el.search.addEventListener("input", runSearch);
    el.search.addEventListener("keydown", function (ev) {
      if (ev.key !== "Enter") return;
      var first = el.hits.querySelector("li:not(.muted)");
      if (first) first.click();
    });

    var dragging = false, moved = false, lastX = 0, lastY = 0;

    canvas.addEventListener("pointerdown", function (ev) {
      dragging = true;
      moved = false;
      lastX = ev.clientX;
      lastY = ev.clientY;
      canvas.classList.add("dragging");
      canvas.setPointerCapture(ev.pointerId);
    });

    canvas.addEventListener("pointermove", function (ev) {
      var rect = canvas.getBoundingClientRect();
      if (dragging) {
        var dx = ev.clientX - lastX, dy = ev.clientY - lastY;
        if (Math.abs(dx) + Math.abs(dy) > 2) moved = true;
        camera.x -= dx / camera.scale;
        camera.y -= dy / camera.scale;
        lastX = ev.clientX;
        lastY = ev.clientY;
        draw();
        return;
      }
      var over = nodeAt(ev.clientX - rect.left, ev.clientY - rect.top);
      canvas.style.cursor = data.navigateOnClick && over && safeHref(over.url) ? "pointer" : "";
      var next = over ? over.id : null;
      if (next !== hovered) { hovered = next; draw(); }
    });

    canvas.addEventListener("pointerup", function (ev) {
      dragging = false;
      canvas.classList.remove("dragging");
      if (moved) return;
      var rect = canvas.getBoundingClientRect();
      var hit = nodeAt(ev.clientX - rect.left, ev.clientY - rect.top);
      // navigateOnClick is for a graph whose nodes ARE pages — a docs site,
      // where following the link is what a click means and an attribute table
      // is the detour. Off by default: in an exported data graph the inspector
      // is the point, and a click that navigated away would be a trap.
      var target = data.navigateOnClick && hit ? safeHref(hit.url) : null;
      if (target) {
        window.location.href = target;
        return;
      }
      show(hit);
    });

    canvas.addEventListener("pointerleave", function () {
      if (hovered !== null) { hovered = null; draw(); }
    });

    canvas.addEventListener("wheel", function (ev) {
      ev.preventDefault();
      var rect = canvas.getBoundingClientRect();
      var mx = ev.clientX - rect.left - width() / 2;
      var my = ev.clientY - rect.top - height() / 2;
      var before = { x: camera.x + mx / camera.scale, y: camera.y + my / camera.scale };
      var factor = Math.pow(1.0015, -ev.deltaY);
      camera.scale = Math.min(2000, Math.max(0.002, camera.scale * factor));
      camera.x = before.x - mx / camera.scale;
      camera.y = before.y - my / camera.scale;
      draw();
    }, { passive: false });

    el.fitBtn.addEventListener("click", fit);
    el.clearBtn.addEventListener("click", function () {
      el.search.value = "";
      runSearch();
      show(null);
    });

    // Per-element sizing. window.resize would miss a host that resizes its own
    // container without the viewport changing at all — a sidebar opening, a
    // details element expanding — which is the normal case for an embed.
    var observer = null;
    if (window.ResizeObserver && host) {
      observer = new ResizeObserver(function () { resize(); });
      observer.observe(host);
    } else {
      window.addEventListener("resize", resize);
    }

    show(null);
    resize();
    fit();

    return {
      nodeCount: nodes.length,
      edgeCount: edges.length,
      camera: camera,
      baseScale: function () { return baseScale; },
      nodeRadius: nodeRadius,
      fit: fit,
      nodeAt: nodeAt,
      root: root,
      select: function (id) { if (byId[id]) centreOn(byId[id]); },
      selected: function () { return selected; },
      hover: function (id) { hovered = id; draw(); },
      search: function (q) { el.search.value = q; runSearch(); return el.hits; },
      destroy: function () { if (observer) observer.disconnect(); }
    };
  }

  function Graph() {
    return Reflect.construct(HTMLElement, [], Graph);
  }
  Graph.prototype = Object.create(HTMLElement.prototype);
  Graph.prototype.constructor = Graph;
  Object.setPrototypeOf(Graph, HTMLElement);

  Graph.prototype.connectedCallback = function () {
    if (this.__mounted) return;
    var island = this.querySelector('script[type="application/json"]');
    if (!island) {
      // Upgrade timing, and the reason the SECOND embed on a page used to stay
      // blank. The first fragment's element is upgraded by customElements.define
      // running after it, so its children are already parsed. By the time the
      // parser reaches a later element the definition exists, so this fires at
      // the OPENING TAG — before the data script inside it is parsed, and
      // querySelector finds nothing. Wait for the parser to finish and retry.
      if (document.readyState === "loading") {
        var self = this;
        document.addEventListener("DOMContentLoaded", function () {
          self.connectedCallback();
        }, { once: true });
      }
      return;
    }
    this.__mounted = true;
    var data = JSON.parse(island.textContent);
    // Open, not closed: the page's own scripts (and the test suite) can reach
    // in. There is nothing secret in here — the data is in the document.
    var shadow = this.attachShadow({ mode: "open" });
    this.graph = mount(shadow, data, this);
    var all = (window.__strataGGraphs = window.__strataGGraphs || []);
    all.push(this.graph);
    // The single-graph handle the standalone page has published since ADR-237.
    // Kept pointing at the FIRST graph so anything already scripting an
    // exported page keeps working; __strataGGraphs is the contract for pages
    // carrying more than one.
    if (!window.__strataGExport) window.__strataGExport = this.graph;
    this.dispatchEvent(new CustomEvent("strata-g-ready", { bubbles: true }));
  };

  Graph.prototype.disconnectedCallback = function () {
    if (this.graph) this.graph.destroy();
  };

  customElements.define(TAG, Graph);
})();
