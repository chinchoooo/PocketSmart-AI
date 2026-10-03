/* PocketSmart AI - frontend logic (vanilla JS, no build step).
 * All AI-generated text is inserted with textContent (never innerHTML) so it cannot inject markup. */
"use strict";

// ------------------------------------------------------------------ helpers
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

/** Tiny DOM builder: h("div", {class: "x"}, "text", childNode, [more...]) */
function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === false || value == null) continue;
    if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat(Infinity)) {
    if (child == null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

const inrFmt = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const inr = (n) => "₹" + inrFmt.format(Math.round(n || 0));
const PLATFORM_LABELS = { bigbasket: "BigBasket", bookmyshow: "BookMyShow", makemytrip: "MakeMyTrip", oyorooms: "OYO", nobroker: "NoBroker", bluestone: "BlueStone", caratlane: "CaratLane", ikea: "IKEA" };
const platformLabel = (name) => PLATFORM_LABELS[name] || name.charAt(0).toUpperCase() + name.slice(1);
const prettify = (text) => { const t = String(text).replace(/_/g, " ").trim(); return t.charAt(0).toUpperCase() + t.slice(1); };
const sentence = (...parts) => parts.filter(Boolean).map((t) => String(t).trim().replace(/\.+$/, "")).filter(Boolean).join(". ");
const SWATCHES = ["var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)", "var(--c6)"];
const TYPE_TITLE = { home: "Home interior", party: "Party", jewelry: "Jewelry" };

/** Normalise a FastAPI error body to {message, fields:{name:msg}}. */
function parseError(data, status) {
  const out = { message: "", fields: {} };
  const detail = data && data.detail;
  if (typeof detail === "string") { out.message = detail; return out; }
  if (Array.isArray(detail)) {
    const general = [];
    for (const e of detail) {
      const msg = String(e.msg || "Invalid value").replace(/^Value error, /, "");
      const loc = Array.isArray(e.loc) ? e.loc.filter((p) => p !== "body" && p !== "form") : [];
      const name = loc.length ? String(loc[loc.length - 1]) : "";
      if (name && !out.fields[name]) out.fields[name] = msg; else general.push(msg);
    }
    out.message = general.join(". ");
    return out;
  }
  out.message = `Something went wrong (HTTP ${status}). Please try again.`;
  return out;
}

class ApiError extends Error {
  constructor(parsed, status) { super(parsed.message || "Request failed"); this.fields = parsed.fields; this.status = status; }
}

/** fetch wrapper: parses JSON, throws ApiError on failure, redirects to /login on 401 (except sign-in). */
async function api(path, options = {}) {
  let response;
  try { response = await fetch(path, { credentials: "same-origin", ...options }); }
  catch (_) { throw new ApiError({ message: "Could not reach the server. Check your connection and try again.", fields: {} }, 0); }
  let data = null;
  try { data = await response.json(); } catch (_) { /* empty body */ }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/token")) window.location.href = "/login";
    throw new ApiError(parseError(data, response.status), response.status);
  }
  return data;
}

function setBusy(button, busy, idleLabel, busyLabel = "Working") {
  button.disabled = busy;
  button.setAttribute("aria-busy", busy ? "true" : "false");
  button.replaceChildren(...(busy ? [h("span", { class: "spinner", "aria-hidden": "true" }), " " + busyLabel] : [idleLabel]));
}

function formError(box, message) { if (!box) return; box.textContent = message || ""; box.hidden = !message; }

function fieldError(scope, name, message) {
  const slot = $(`[data-error-for="${name}"]`, scope);
  const wrap = $(`[data-field="${name}"]`, scope) || (slot && slot.closest("fieldset"));
  if (slot) { slot.textContent = message || ""; slot.hidden = !message; }
  if (wrap) {
    wrap.classList.toggle("invalid", !!message);
    const input = $("input, select, textarea", wrap);
    if (input) { if (message) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid"); }
  }
  return !!slot;
}

function clearErrors(scope) {
  $$("[data-error-for]", scope).forEach((el) => fieldError(scope, el.dataset.errorFor, ""));
  $$(".invalid", scope).forEach((el) => el.classList.remove("invalid"));
}

function focusFirstInvalid(scope) {
  const bad = $(".invalid input, .invalid select, .invalid textarea", scope);
  if (bad) bad.focus();
}

// ------------------------------------------------------------------ result rendering
const safeLinks = (links) => Object.entries(links || {}).filter(([, url]) => /^https:\/\//.test(String(url)));

function shopRow(links) {
  const list = safeLinks(links);
  if (!list.length) return null;
  return h("div", { class: "shop" }, "Search on",
    list.map(([name, url]) => h("a", { href: url, target: "_blank", rel: "noopener noreferrer" }, platformLabel(name))));
}

function lineItem(name, description, cost, sub, links) {
  return h("li", { class: "line" },
    h("div", {}, h("div", { class: "name" }, name), description ? h("div", { class: "desc" }, description) : null),
    h("div", { class: "cost" }, cost, sub ? h("small", {}, sub) : null),
    shopRow(links));
}

function allocationBar(categories, total, remaining) {
  const bar = h("div", { class: "alloc", role: "img", "aria-label": "How the budget is split" });
  categories.forEach((c, i) => {
    const seg = h("span", { title: `${prettify(c.category)}: ${inr(c.spent)}` });
    seg.style.flex = `${Math.max(c.spent, 0.0001)} 1 0`;
    seg.style.background = SWATCHES[i % SWATCHES.length];
    bar.append(seg);
  });
  if (remaining > 0) {
    const left = h("span", { class: "left", title: `Unspent: ${inr(remaining)}` });
    left.style.flex = `${remaining} 1 0`;
    bar.append(left);
  }
  const pct = (v) => (total > 0 ? Math.round((v / total) * 100) : 0) + "%";
  const legend = h("ul", { class: "legend" },
    categories.map((c, i) => {
      const dot = h("span", { class: "swatch", "aria-hidden": "true" });
      dot.style.background = SWATCHES[i % SWATCHES.length];
      return h("li", {}, dot, h("span", {}, prettify(c.category)), h("span", { class: "pct" }, pct(c.spent)), h("span", { class: "amt" }, inr(c.spent)));
    }),
    remaining > 0 ? h("li", {}, h("span", { class: "swatch", "aria-hidden": "true", style: "border:1px solid var(--line-strong)" }), h("span", {}, "Unspent"), h("span", { class: "pct" }, pct(remaining)), h("span", { class: "amt" }, inr(remaining))) : null);
  return [bar, legend];
}

/** Build the whole plan view. `result` is the server's JSON; `type` is home|party|jewelry. */
function renderPlan(type, result, opts = {}) {
  const root = h("div", { class: "plan" });
  const categories = (result.budget_breakdown || []).map((c) => ({
    ...c, spent: (c.items || []).reduce((s, it) => s + (it.estimated_price || 0) * (it.quantity || 1), 0),
  }));
  const total = result.total_budget || 0;
  const remaining = result.remaining_budget != null ? result.remaining_budget : Math.max(total - categories.reduce((s, c) => s + c.spent, 0), 0);
  const planned = Math.max(total - remaining, 0);

  root.append(h("div", { class: "result-head" },
    h("div", {}, h("h2", {}, `${TYPE_TITLE[type] || "Plan"} plan`),
      opts.when ? h("p", {}, opts.when) : null),
    opts.noPrint ? null : h("button", { type: "button", class: "btn btn-secondary btn-sm no-print", onclick: () => window.print() }, "Print plan")));

  if (result.source === "fallback") {
    root.append(h("div", { class: "notice", role: "status" },
      "The AI service was unavailable, so this is a standard estimate based on typical prices. Try again later for a tailored plan."));
  }

  root.append(h("dl", { class: "totals" },
    h("div", {}, h("dt", {}, "Budget"), h("dd", {}, inr(total))),
    h("div", {}, h("dt", {}, "Planned"), h("dd", {}, inr(planned))),
    h("div", { class: "remaining" }, h("dt", {}, "Left over"), h("dd", {}, inr(remaining)))));
  if (categories.length) root.append(...allocationBar(categories, total, remaining));

  if (type === "jewelry" && result.outfit_analysis) {
    const o = result.outfit_analysis;
    root.append(h("section", { class: "group" },
      h("div", { class: "group-head" }, h("h3", {}, "Your outfit")),
      h("p", { class: "desc", style: "padding-top:.75rem;color:var(--ink-2)" },
        sentence(o.style && `Style: ${o.style}`, o.formality && `Formality: ${o.formality}`) + "."),
      (o.colors || []).length ? h("div", { class: "tags" }, o.colors.map((c) => h("span", { class: "tag" }, c))) : null));
  }

  categories.forEach((c) => {
    root.append(h("section", { class: "group" },
      h("div", { class: "group-head" }, h("h3", {}, prettify(c.category)),
        h("span", { class: "total" }, inr(c.spent), h("span", { class: "muted", style: "font-weight:400" }, ` of ${inr(c.allocation)}`))),
      h("ul", { class: "lines" }, (c.items || []).map((it) =>
        lineItem(it.name, it.description, inr((it.estimated_price || 0) * (it.quantity || 1)),
          (it.quantity || 1) > 1 ? `${it.quantity} × ${inr(it.estimated_price)}` : null, it.shopping_links)))));
  });

  if (type === "party" && (result.venue_suggestions || []).length) {
    root.append(h("section", { class: "group" },
      h("div", { class: "group-head" }, h("h3", {}, "Venue ideas")),
      h("ul", { class: "lines" }, result.venue_suggestions.map((v) =>
        lineItem(v.name, sentence(v.type, v.capacity ? `up to ${v.capacity} guests` : ""), inr(v.estimated_cost), null, v.shopping_links)))));
  }

  if (type === "jewelry" && (result.jewelry_recommendations || []).length) {
    root.append(h("section", { class: "group" },
      h("div", { class: "group-head" }, h("h3", {}, "Recommended pieces")),
      h("ul", { class: "lines" }, result.jewelry_recommendations.map((j) =>
        lineItem(prettify(j.item_type), sentence(j.description, j.style), inr(j.estimated_price), null, j.shopping_links)))));
  }

  const notes = [].concat(result.additional_suggestions || [], result.styling_tips || []).filter(Boolean);
  if (notes.length) {
    root.append(h("section", { class: "group" }, h("div", { class: "group-head" }, h("h3", {}, "Tips")),
      h("ul", { class: "notes", style: "margin-top:.5rem" }, notes.map((t) => h("li", {}, t)))));
  }
  return root;
}

function skeleton() {
  return h("div", { class: "skeleton", role: "status", "aria-label": "Building your plan" },
    Array.from({ length: 8 }, () => h("i")));
}

// ------------------------------------------------------------------ money + steppers
function parseMoney(text) { const digits = String(text).replace(/[^\d]/g, ""); return digits ? Number(digits) : NaN; }

function initMoney(scope) {
  $$("[data-money]", scope).forEach((input) => {
    input.addEventListener("input", () => {
      const caretFromEnd = input.value.length - (input.selectionStart || 0);
      const n = parseMoney(input.value);
      input.value = Number.isNaN(n) ? "" : inrFmt.format(n);
      const pos = Math.max(input.value.length - caretFromEnd, 0);
      try { input.setSelectionRange(pos, pos); } catch (_) { /* unsupported */ }
    });
  });
  $$(".preset", scope).forEach((btn) => {
    const value = Number(btn.dataset.value);
    btn.textContent = inr(value);
    btn.addEventListener("click", () => {
      const input = $("[data-money]", btn.closest(".field"));
      input.value = inrFmt.format(value);
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.focus();
    });
  });
}

function initSteppers(scope) {
  $$(".stepper", scope).forEach((box) => {
    const input = $("input", box);
    box.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-step]");
      if (!btn) return;
      const max = Number(input.max) || 9999;
      const next = (Number(input.value) || 0) + Number(btn.dataset.step);
      input.value = String(Math.min(Math.max(next, Number(input.min) || 0), max));
    });
  });
}

// ------------------------------------------------------------------ planner pages
function readPlanner(form) {
  const f = form.elements;
  const num = (name) => (f[name].value === "" ? NaN : Number(f[name].value));
  const txt = (name) => (f[name] ? f[name].value.trim() : "");
  const chk = (name) => !!(f[name] && f[name].checked);
  const base = { total_budget: parseMoney(f.total_budget.value) };
  switch (form.dataset.planner) {
    case "home": return { ...base, num_lights: num("num_lights"), num_fans: num("num_fans"), num_furniture: num("num_furniture"),
      num_dining_tables: num("num_dining_tables"), has_living_room: chk("has_living_room"), has_kitchen: chk("has_kitchen"),
      has_bedroom: chk("has_bedroom"), additional_requirements: txt("additional_requirements") || null };
    case "party": return { ...base, num_guests: num("num_guests"), party_type: f.party_type.value, venue_type: f.venue_type.value,
      needs_catering: chk("needs_catering"), needs_decoration: chk("needs_decoration"), needs_entertainment: chk("needs_entertainment"),
      additional_requirements: txt("additional_requirements") || null };
    default: return { ...base, occasion: f.occasion.value, preferences: txt("preferences") || null };
  }
}

/** Client-side checks that mirror the server rules. Returns {field: message}. */
function checkPlanner(kind, v, form) {
  const e = {};
  if (Number.isNaN(v.total_budget) || v.total_budget <= 0) e.total_budget = "Enter a budget greater than zero.";
  else if (v.total_budget > 100000000) e.total_budget = "Enter a budget of ₹10,00,00,000 or less.";
  if (kind === "home") {
    const caps = { num_lights: 100, num_fans: 50, num_furniture: 100, num_dining_tables: 20 };
    for (const [k, max] of Object.entries(caps)) if (Number.isNaN(v[k]) || v[k] < 0 || v[k] > max || !Number.isInteger(v[k])) e[k] = `Enter a whole number from 0 to ${max}.`;
    if (!Object.keys(e).length && v.num_lights + v.num_fans + v.num_furniture + v.num_dining_tables === 0 && !(v.has_living_room || v.has_kitchen || v.has_bedroom))
      e.rooms = "Choose at least one item or room.";
  }
  if (kind === "party") {
    if (Number.isNaN(v.num_guests) || !Number.isInteger(v.num_guests) || v.num_guests < 1 || v.num_guests > 5000) e.num_guests = "Enter a guest count from 1 to 5,000.";
    if (!(v.needs_catering || v.needs_decoration || v.needs_entertainment)) e.needs = "Choose at least one of catering, decoration or entertainment.";
  }
  const text = $("[name=additional_requirements], [name=preferences]", form);
  if (text && text.value.length > 500) e[text.name] = "Keep this under 500 characters.";
  return e;
}

function initPlanner(form) {
  const kind = form.dataset.planner;
  const topError = $("[data-error]", form);
  const button = $("button[type=submit]", form);
  const idle = button.textContent;
  const result = $("#result");
  const photo = kind === "jewelry" ? initUpload(form) : null;
  initMoney(form); initSteppers(form);

  $$("input, select, textarea", form).forEach((el) => el.addEventListener("input", () => {
    const wrap = el.closest("[data-field]");
    if (wrap && wrap.classList.contains("invalid")) fieldError(form, wrap.dataset.field, "");
  }));
  $$("[data-group] input", form).forEach((el) => el.addEventListener("change", () => {
    const group = el.closest("[data-group]").dataset.group;
    fieldError(form, group, "");
  }));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    formError(topError, ""); clearErrors(form);
    const values = readPlanner(form);
    const problems = checkPlanner(kind, values, form);
    if (Object.keys(problems).length) {
      Object.entries(problems).forEach(([k, m]) => fieldError(form, k, m));
      focusFirstInvalid(form);
      return;
    }
    let options;
    if (kind === "jewelry") {
      const body = new FormData();
      body.append("total_budget", String(values.total_budget));
      body.append("occasion", values.occasion);
      if (values.preferences) body.append("preferences", values.preferences);
      if (photo && photo.file()) body.append("image", photo.file());
      options = { method: "POST", body };
    } else {
      options = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) };
    }

    setBusy(button, true, idle, "Building your plan");
    result.replaceChildren(skeleton());
    result.setAttribute("aria-busy", "true");
    try {
      const data = await api(form.dataset.endpoint, options);
      result.replaceChildren(renderPlan(kind, data, { when: "Saved to your history just now." }));
      result.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      result.focus({ preventScroll: true });
    } catch (err) {
      result.replaceChildren(h("div", { class: "empty" }, h("h2", {}, "No plan yet"), h("p", {}, "Fix the highlighted fields and try again.")));
      let shown = false;
      Object.entries(err.fields || {}).forEach(([k, m]) => { if (fieldError(form, k, m)) shown = true; else formError(topError, `${prettify(k)}: ${m}`); });
      if (!shown || err.message) formError(topError, err.message || topError.textContent);
      if (shown) focusFirstInvalid(form); else topError.scrollIntoView({ block: "nearest" });
    } finally {
      result.removeAttribute("aria-busy");
      setBusy(button, false, idle);
    }
  });
}

function initUpload(form) {
  const input = $("#image", form), label = $("#upload-label", form), box = $("#preview", form), img = $("#preview-img", form);
  const original = label.textContent;
  let url = null;
  const reset = () => { input.value = ""; if (url) URL.revokeObjectURL(url); url = null; box.hidden = true; img.removeAttribute("src"); label.textContent = original; };
  $("#remove-image", form).addEventListener("click", () => { reset(); fieldError(form, "image", ""); input.focus(); });
  input.addEventListener("change", () => {
    fieldError(form, "image", "");
    const file = input.files && input.files[0];
    if (!file) { reset(); return; }
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) { reset(); fieldError(form, "image", "Use a JPG, PNG or WEBP photo."); return; }
    if (file.size > 5 * 1024 * 1024) { reset(); fieldError(form, "image", "That photo is over 5 MB. Choose a smaller one."); return; }
    if (url) URL.revokeObjectURL(url);
    url = URL.createObjectURL(file);
    img.src = url; box.hidden = false;
    label.textContent = `${file.name} (${(file.size / 1024).toFixed(0)} KB). Choose a different photo to replace it.`;
  });
  return { file: () => (input.files && input.files[0]) || null };
}

// ------------------------------------------------------------------ landing demo
function initDemo(root) {
  const SPLITS = {
    home: [["Lighting", 22], ["Ceiling fans", 18], ["Furniture", 42], ["Dining tables", 18]],
    party: [["Venue", 25], ["Catering", 40], ["Decoration", 15], ["Entertainment", 12], ["Buffer", 8]],
    jewelry: [["Necklace", 38], ["Earrings", 22], ["Bangles", 25], ["Rings", 15]],
  };
  const range = $("#demo-range", root), out = $("#demo-out", root), bar = $("#demo-bar", root), legend = $("#demo-legend", root);
  let kind = "home";
  const draw = () => {
    const total = Number(range.value);
    out.textContent = inr(total);
    const cats = SPLITS[kind].map(([category, pct]) => ({ category, spent: (total * pct) / 100 }));
    const [b, l] = allocationBar(cats, total, 0);
    bar.replaceChildren(...b.children);
    legend.replaceChildren(...l.children);
  };
  $$("[data-demo]", root).forEach((btn) => btn.addEventListener("click", () => {
    kind = btn.dataset.demo;
    $$("[data-demo]", root).forEach((o) => o.setAttribute("aria-pressed", String(o === btn)));
    draw();
  }));
  range.addEventListener("input", draw);
  draw();
}

// ------------------------------------------------------------------ auth pages
function initPasswordToggles() {
  $$("[data-toggle=password]").forEach((btn) => btn.addEventListener("click", () => {
    const input = $("input", btn.parentElement);
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    btn.textContent = show ? "Hide" : "Show";
    btn.setAttribute("aria-pressed", String(show));
  }));
}

function initLogin(form) {
  const err = $("#error"), button = $("button[type=submit]", form), idle = button.textContent;
  if (new URLSearchParams(location.search).get("registered")) $("#notice").hidden = false;
  form.addEventListener("submit", async (e) => {
    e.preventDefault(); formError(err, ""); clearErrors(form);
    const username = form.username.value.trim(), password = form.password.value;
    if (!username) fieldError(form, "username", "Enter your username.");
    if (!password) fieldError(form, "password", "Enter your password.");
    if (!username || !password) { focusFirstInvalid(form); return; }
    setBusy(button, true, idle, "Signing in");
    try {
      await api("/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }) });
      window.location.href = "/dashboard";
    } catch (ex) {
      formError(err, ex.status === 401 || ex.status === 400 ? "Username or password is incorrect." : ex.message);
      setBusy(button, false, idle);
    }
  });
}

function passwordStrength(pw) {
  if (!pw) return ["Use at least 8 characters.", ""];
  if (pw.length < 8) return [`${8 - pw.length} more character${8 - pw.length === 1 ? "" : "s"} needed.`, "weak"];
  let score = 0;
  if (pw.length >= 12) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score >= 3 ? ["Strong password.", "strong"] : score >= 2 ? ["Good. Add a symbol or more length to strengthen it.", "ok"] : ["Acceptable. Mix letters, numbers and symbols to strengthen it.", "weak"];
}

function initRegister(form) {
  const err = $("#error"), button = $("button[type=submit]", form), idle = button.textContent, hint = $("#strength");
  form.password.addEventListener("input", () => { const [msg, level] = passwordStrength(form.password.value); hint.textContent = msg; hint.dataset.level = level; });
  form.addEventListener("submit", async (e) => {
    e.preventDefault(); formError(err, ""); clearErrors(form);
    const v = { username: form.username.value.trim(), email: form.email.value.trim(), password: form.password.value };
    if (!/^[A-Za-z0-9_.-]{3,30}$/.test(v.username)) fieldError(form, "username", "Use 3 to 30 letters, numbers, dots, dashes or underscores.");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v.email)) fieldError(form, "email", "Enter a valid email address.");
    if (v.password.length < 8) fieldError(form, "password", "Use at least 8 characters.");
    else if (new TextEncoder().encode(v.password).length > 72) fieldError(form, "password", "Use 72 bytes or fewer.");
    if (form.confirm.value !== v.password) fieldError(form, "confirm", "The passwords do not match.");
    if ($(".invalid", form)) { focusFirstInvalid(form); return; }
    setBusy(button, true, idle, "Creating account");
    try {
      await api("/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(v) });
      window.location.href = "/login?registered=1";
    } catch (ex) {
      let shown = false;
      Object.entries(ex.fields || {}).forEach(([k, m]) => { if (fieldError(form, k, m)) shown = true; });
      if (ex.message || !shown) formError(err, ex.message || "Could not create the account.");
      if (shown) focusFirstInvalid(form);
      setBusy(button, false, idle);
    }
  });
}

// ------------------------------------------------------------------ dashboard + history
const when = (iso) => {
  const d = new Date(String(iso).endsWith("Z") || /[+-]\d\d:?\d\d$/.test(String(iso)) ? iso : iso + "Z");
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" });
};

function historyRow(entry, onOpen) {
  const s = entry.summary || {};
  const cats = (s.categories || []).map(prettify).join(", ");
  const content = [
    h("span", { class: "title" }, h("span", { class: `type-dot type-${entry.type}`, "aria-hidden": "true" }), TYPE_TITLE[entry.type] || entry.type),
    h("span", { class: "sub" }, [when(entry.timestamp), cats].filter(Boolean).join(" – ")),
    h("span", { class: "aside" }, h("strong", {}, inr(s.total_budget)), s.source === "fallback" ? "Standard estimate" : "AI plan"),
  ];
  return h("li", {}, onOpen ? h("button", { type: "button", class: "item", onclick: () => onOpen(entry) }, content)
    : h("a", { href: "/history" }, content));
}

async function initDashboard(list) {
  try {
    const data = await api("/recommendation-history?limit=4");
    const rows = (data.history || data || []).slice(0, 4);
    list.replaceChildren(...(rows.length
      ? rows.map((r) => historyRow(r, null))
      : [h("li", { class: "muted", style: "padding:1.15rem .25rem" }, "No plans yet. Start one from the left and it will show up here.")]));
  } catch (_) {
    list.replaceChildren(h("li", { class: "muted", style: "padding:1.15rem .25rem" }, "Could not load your plans. Refresh to try again."));
  }
}

async function initHistory(list) {
  const dialog = $("#detail"), body = $("#detail-body");
  let all = [], filter = "all";
  const empty = (text) => h("li", { class: "muted", style: "padding:1.15rem .25rem" }, text);
  const draw = () => {
    const rows = all.filter((r) => filter === "all" || r.type === filter);
    list.replaceChildren(...(rows.length ? rows.map((r) => historyRow(r, open))
      : [empty(all.length ? "No plans of this type yet." : "No plans yet. Build one and it will be saved here.")]));
  };
  async function open(entry) {
    body.replaceChildren(skeleton());
    if (!dialog.open) dialog.showModal();
    try {
      const d = await api(`/recommendation-details/${encodeURIComponent(entry.id)}`);
      body.replaceChildren(renderPlan(d.type, d.full_result, { when: `Saved ${when(d.timestamp)}`, noPrint: true }));
    } catch (ex) { body.replaceChildren(h("div", { class: "form-error", role: "alert" }, ex.message)); }
  }
  $("#detail-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  $$("[data-filter]").forEach((btn) => btn.addEventListener("click", () => {
    filter = btn.dataset.filter;
    $$("[data-filter]").forEach((o) => o.setAttribute("aria-pressed", String(o === btn)));
    draw();
  }));
  try {
    const data = await api("/recommendation-history?limit=100");
    all = data.history || data || [];
    draw();
  } catch (_) { list.replaceChildren(empty("Could not load your plans. Refresh to try again.")); }
}

// ------------------------------------------------------------------ boot
document.addEventListener("DOMContentLoaded", () => {
  initPasswordToggles();
  const planner = $("form[data-planner]"); if (planner) initPlanner(planner);
  const demo = $("#demo"); if (demo) initDemo(demo);
  const login = $("#login-form"); if (login) initLogin(login);
  const register = $("#register-form"); if (register) initRegister(register);
  const recent = $("#recent"); if (recent) initDashboard(recent);
  const history = $("#history"); if (history) initHistory(history);
});
