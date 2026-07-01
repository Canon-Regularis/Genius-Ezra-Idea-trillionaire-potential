"use strict";

// Loads the reviewer renderer (which is written to run inside Anki's webview)
// into a headless `vm` sandbox with just enough DOM fakes that its top-level
// IIFE runs without a browser, then hands back the pure helper functions it
// exposes on `window.RandomizedOcclusion._internals`.

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const RENDER_JS = path.join(
  __dirname,
  "..",
  "..",
  "src",
  "randomized_occlusion",
  "web",
  "review",
  "render.js",
);

function stubNode() {
  return {
    setAttribute() {},
    appendChild() {},
    insertBefore() {},
    removeChild() {},
    getComputedTextLength() {
      return 0;
    },
    style: {},
    dataset: {},
    textContent: "",
    firstChild: null,
  };
}

function loadInternals() {
  const code = fs.readFileSync(RENDER_JS, "utf8");
  const noop = () => {};
  const store = {};
  const windowObj = {
    addEventListener: noop,
    setTimeout: noop,
    getComputedStyle: () => ({ fontSize: "18px" }),
    sessionStorage: {
      getItem: (k) => (Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null),
      setItem: (k, v) => {
        store[k] = String(v);
      },
    },
  };
  const documentObj = {
    getElementById: () => null,
    querySelector: () => null,
    createElement: () => stubNode(),
    createElementNS: () => stubNode(),
  };
  const sandbox = {
    window: windowObj,
    document: documentObj,
    atob,
    TextDecoder,
    Uint8Array,
    setTimeout: noop,
    console,
  };
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox, { filename: "render.js" });
  const api = sandbox.window.RandomizedOcclusion;
  if (!api || !api._internals) {
    throw new Error("render.js did not expose RandomizedOcclusion._internals");
  }
  return api._internals;
}

module.exports = { loadInternals, RENDER_JS };
