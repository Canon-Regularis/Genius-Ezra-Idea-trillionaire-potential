/*
 * Randomized Image Occlusion — reviewer renderer.
 *
 * This file is *embedded into the card template* at note-type install time (it
 * is NOT shipped as a media file), so synced cards render correctly on every
 * client — desktop, AnkiDroid, AnkiMobile — without the add-on installed.
 *
 * Responsibilities:
 *   1. Read the structures (base64 JSON) and config out of the DOM.
 *   2. Determine which structure this card tests (the active cloze ordinal).
 *   3. Place the prompt box at a *randomised* position each review, drawing a
 *      leader-line arrow from the box to the structure's fixed target.
 *   4. Keep the front and back of a single review identical by sharing one
 *      per-review seed (sessionStorage, with a window-global fallback).
 *
 * Everything is wrapped in an IIFE: Anki reuses one webview across cards on the
 * desktop, so top-level `let`/`const`/`class` would throw "already declared" on
 * the second card. Assigning to `window.RandomizedOcclusion` is re-entrant-safe.
 */
(function () {
  "use strict";

  var SEED_KEY = "randomizedOcclusion.seed";

  var DEFAULT_CONFIG = {
    minArrowFraction: 0.22, // shortest arrow as a fraction of the stage diagonal
    showTargetDot: true,
    promptText: "?",
    maxPlacementAttempts: 48,
  };

  // ---- small utilities ------------------------------------------------------

  /** Decode UTF-8-safe base64 into a string. */
  function decodeBase64Utf8(b64) {
    var binary = atob(b64);
    var bytes = new Uint8Array(binary.length);
    for (var i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new TextDecoder("utf-8").decode(bytes);
  }

  /** Deterministic 32-bit string hash (used only for the seedless fallback). */
  function hashString(str) {
    var h = 2166136261;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  /** mulberry32 — tiny seeded PRNG returning floats in [0, 1). */
  function makeRng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function readSeed() {
    try {
      return window.sessionStorage.getItem(SEED_KEY);
    } catch (e) {
      return window.__roSeedFallback || null;
    }
  }

  function writeSeed(value) {
    try {
      window.sessionStorage.setItem(SEED_KEY, String(value));
    } catch (e) {
      window.__roSeedFallback = String(value);
    }
  }

  // ---- DOM reading ----------------------------------------------------------

  function parseJsonElement(id, fallback) {
    var el = document.getElementById(id);
    if (!el) return fallback;
    var text = (el.textContent || "").trim();
    if (!text) return fallback;
    try {
      return JSON.parse(text);
    } catch (e) {
      return fallback;
    }
  }

  function readConfig() {
    var cfg = parseJsonElement("ro-config", {});
    var merged = {};
    for (var key in DEFAULT_CONFIG) {
      if (Object.prototype.hasOwnProperty.call(DEFAULT_CONFIG, key)) {
        merged[key] = key in cfg ? cfg[key] : DEFAULT_CONFIG[key];
      }
    }
    return merged;
  }

  function readStructures() {
    var el = document.getElementById("ro-data");
    if (!el) return [];
    var b64 = (el.textContent || "").trim();
    if (!b64) return [];
    try {
      return JSON.parse(decodeBase64Utf8(b64));
    } catch (e) {
      return [];
    }
  }

  /**
   * The active cloze ordinal tells us which structure this card is testing.
   * Anki renders the active deletion as `<span class="cloze" data-ordinal="N">`
   * and the others as `class="cloze-inactive"`, so `.cloze` selects the active.
   */
  function readActiveOrdinal(structures) {
    var active = document.querySelector("#ro-ordinal .cloze");
    if (active && active.dataset && active.dataset.ordinal) {
      return parseInt(active.dataset.ordinal, 10);
    }
    return structures.length ? structures[0].ord : null;
  }

  function isBackSide() {
    return !!document.getElementById("ro-answer");
  }

  /**
   * The image is provided by the `Image` field as a full `<img src=...>` tag
   * (so Anki's media check detects the reference), hence we select it by
   * position inside the stage rather than by id.
   */
  function getImage() {
    var stage = document.getElementById("ro-stage");
    return stage ? stage.querySelector("img") : null;
  }

  // ---- geometry / placement -------------------------------------------------

  function clamp(value, lo, hi) {
    if (hi < lo) return lo;
    return Math.max(lo, Math.min(hi, value));
  }

  /** True if point (px, py) lies inside the axis-aligned box. */
  function pointInBox(px, py, box) {
    return px >= box.x && px <= box.x + box.w && py >= box.y && py <= box.y + box.h;
  }

  /**
   * Choose a randomised, in-bounds position for the prompt box such that:
   *   - the whole box stays inside the stage,
   *   - the target point is not covered by the box,
   *   - the arrow (box-centre -> target) is at least `minLen` long.
   * Falls back to the in-bounds position furthest from the target.
   */
  function placeBox(rng, stage, target, boxSize, cfg) {
    var diag = Math.hypot(stage.w, stage.h);
    var minLen = cfg.minArrowFraction * diag;
    var maxLen = Math.max(minLen + 1, 0.6 * diag);
    var halfW = boxSize.w / 2;
    var halfH = boxSize.h / 2;

    var best = null;
    var bestLen = -1;

    for (var i = 0; i < cfg.maxPlacementAttempts; i++) {
      var angle = rng() * Math.PI * 2;
      var length = minLen + rng() * (maxLen - minLen);
      var cx = clamp(target.x + Math.cos(angle) * length, halfW, stage.w - halfW);
      var cy = clamp(target.y + Math.sin(angle) * length, halfH, stage.h - halfH);
      var box = { x: cx - halfW, y: cy - halfH, w: boxSize.w, h: boxSize.h };
      var actualLen = Math.hypot(cx - target.x, cy - target.y);

      if (!pointInBox(target.x, target.y, box) && actualLen >= minLen * 0.8) {
        return box;
      }
      if (actualLen > bestLen) {
        bestLen = actualLen;
        best = box;
      }
    }
    return best;
  }

  /**
   * Intersection of the segment from the box centre towards the target with the
   * box's border, so the arrow starts at the edge of the box rather than its
   * middle. Returns the box centre if target coincides with it (degenerate).
   */
  function boxBorderToward(box, target) {
    var cx = box.x + box.w / 2;
    var cy = box.y + box.h / 2;
    var dx = target.x - cx;
    var dy = target.y - cy;
    if (dx === 0 && dy === 0) return { x: cx, y: cy };

    var halfW = box.w / 2;
    var halfH = box.h / 2;
    // Scale (dx, dy) so it just reaches the rectangle border.
    var scaleX = dx !== 0 ? halfW / Math.abs(dx) : Infinity;
    var scaleY = dy !== 0 ? halfH / Math.abs(dy) : Infinity;
    var scale = Math.min(scaleX, scaleY);
    return { x: cx + dx * scale, y: cy + dy * scale };
  }

  // ---- SVG drawing ----------------------------------------------------------

  var SVG_NS = "http://www.w3.org/2000/svg";

  function svgEl(name, attrs) {
    var el = document.createElementNS(SVG_NS, name);
    if (attrs) {
      for (var key in attrs) {
        if (Object.prototype.hasOwnProperty.call(attrs, key)) {
          el.setAttribute(key, attrs[key]);
        }
      }
    }
    return el;
  }

  function ensureArrowMarker(svg) {
    var defs = svgEl("defs");
    var marker = svgEl("marker", {
      id: "ro-arrowhead",
      class: "ro-arrowhead",
      markerWidth: "10",
      markerHeight: "10",
      refX: "8",
      refY: "5",
      orient: "auto-start-reverse",
      markerUnits: "userSpaceOnUse",
    });
    marker.appendChild(svgEl("path", { d: "M0,1 L9,5 L0,9 Z" }));
    defs.appendChild(marker);
    svg.appendChild(defs);
  }

  /**
   * Render the single prompt box + arrow + target dot for `structure` onto the
   * (already cleared) svg. `text` is what the box shows ("?" front, label back).
   */
  function drawStructure(svg, stage, structure, text, cfg) {
    var target = { x: structure.x * stage.w, y: structure.y * stage.h };

    // Build the label group first so we can measure the text, then size + place.
    var group = svgEl("g", { class: "ro-box" });
    var rect = svgEl("rect", { class: "ro-box-rect", rx: "6", ry: "6" });
    var label = svgEl("text", {
      class: "ro-box-text",
      "text-anchor": "middle",
      "dominant-baseline": "central",
    });
    label.textContent = text;
    group.appendChild(rect);
    group.appendChild(label);
    svg.appendChild(group);

    var padX = 12;
    var padY = 8;
    var textLen;
    try {
      textLen = label.getComputedTextLength();
    } catch (e) {
      textLen = String(text).length * 9;
    }
    var fontSize = parseFloat(window.getComputedStyle(label).fontSize) || 18;
    var boxSize = {
      w: Math.max(36, textLen + padX * 2),
      h: Math.max(30, fontSize + padY * 2),
    };

    var rng = svg.__roRng;
    var box = placeBox(rng, stage, target, boxSize, cfg);

    rect.setAttribute("x", box.x);
    rect.setAttribute("y", box.y);
    rect.setAttribute("width", box.w);
    rect.setAttribute("height", box.h);
    label.setAttribute("x", box.x + box.w / 2);
    label.setAttribute("y", box.y + box.h / 2);

    var start = boxBorderToward(box, target);
    var line = svgEl("line", {
      class: "ro-arrow",
      x1: start.x,
      y1: start.y,
      x2: target.x,
      y2: target.y,
      "marker-end": "url(#ro-arrowhead)",
    });
    // Insert the arrow beneath the box group so the arrowhead reads cleanly.
    svg.insertBefore(line, group);

    if (cfg.showTargetDot) {
      svg.insertBefore(
        svgEl("circle", { class: "ro-dot", cx: target.x, cy: target.y, r: "5" }),
        group
      );
    }
  }

  // ---- orchestration --------------------------------------------------------

  function render() {
    var stageEl = document.getElementById("ro-stage");
    var img = getImage();
    var svg = document.getElementById("ro-overlay");
    if (!stageEl || !img || !svg) return;

    var width = img.clientWidth;
    var height = img.clientHeight;
    if (!width || !height) return; // image not laid out yet; a later pass will retry

    var structures = readStructures();
    if (!structures.length) return;

    var cfg = readConfig();
    var back = isBackSide();
    var activeOrdinal = readActiveOrdinal(structures);

    var structure = null;
    for (var i = 0; i < structures.length; i++) {
      if (structures[i].ord === activeOrdinal) {
        structure = structures[i];
        break;
      }
    }
    if (!structure) structure = structures[0];

    // Seed: the front mints a fresh seed each review and stores it; the back
    // (including the front script re-run via {{FrontSide}}) reads it back, so
    // both sides compute an identical layout.
    var seed;
    if (back) {
      var stored = readSeed();
      seed = stored !== null ? parseInt(stored, 10) >>> 0 : hashString("" + activeOrdinal + structures.length);
    } else {
      seed = (Math.floor(Math.random() * 0xffffffff)) >>> 0;
      writeSeed(seed);
    }

    // Match the SVG's user-space to the image's displayed pixel size.
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
    svg.setAttribute("viewBox", "0 0 " + width + " " + height);
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.__roRng = makeRng(seed);
    ensureArrowMarker(svg);

    var text = back ? structure.label : cfg.promptText;
    drawStructure(svg, { w: width, h: height }, structure, text, cfg);
  }

  /** Defer until the image is laid out, then render (and re-render on resize). */
  function run() {
    var img = getImage();
    if (!img) {
      // DOM may not be ready (parse-mode clients); try again on the next task.
      window.setTimeout(run, 0);
      return;
    }

    function go() {
      // setTimeout(0) guarantees we run after the full card HTML is in the DOM
      // (so the back-side sentinel #ro-answer is reliably detectable).
      window.setTimeout(render, 0);
    }

    if (img.complete && img.naturalWidth) {
      go();
    } else {
      img.addEventListener("load", go, { once: true });
      img.addEventListener("error", go, { once: true });
      // Safety net in case neither event fires (cached/odd clients).
      window.setTimeout(go, 250);
    }

    if (!window.__roResizeBound) {
      window.__roResizeBound = true;
      window.addEventListener("resize", function () {
        window.setTimeout(render, 0);
      });
    }
  }

  window.RandomizedOcclusion = { run: run, render: render };
  run();
})();
