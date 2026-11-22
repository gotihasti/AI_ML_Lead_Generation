const API = "http://127.0.0.1:8000";
const PAGE_SIZE = 10;
const STATUSES = ["new", "contacted", "qualified", "converted"];
const $ = (s) => document.querySelector(s);
const state = { leads: [], priority: "", page: 1 };
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : "");
const h = (tag, props = {}, ...kids) => {
    const el = Object.assign(document.createElement(tag), props);
    el.append(...kids.filter((k) => k != null));
    return el;
};

function toast(text, type = "ok") {
    const t = h("div", { className: `toast ${type}`, textContent: text });
    $("#toasts").append(t);
    setTimeout(() => t.remove(), 4500);
}

async function api(path, options = {}) {
    const res = await fetch(API + path, {
        ...options,
        headers: options.body ? { "Content-Type": "application/json" } : {},
    });
    let data = null;
    try { data = await res.json(); } catch { /* empty body */ }
    if (!res.ok) {
        const d = data?.detail;
        const err = new Error(typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join(", ") : `Request failed (${res.status})`);
        err.status = res.status;
        throw err;
    }
    return data;
}

function busy(btn, on, label) {
    if (on) btn.dataset.label = btn.textContent;
    btn.textContent = on ? label : btn.dataset.label;
    btn.disabled = on;
}

/* ---------- data ---------- */
async function load() {
    try {
        const leads = await api("/leads/");
        state.leads = Array.isArray(leads) ? leads : leads.results ?? [];
        renderSummary();
        fillIndustries();
        render();
    } catch (e) {
        console.error(e);
        $("#rows").replaceChildren(h("tr", {}, h("td", {
            colSpan: 6, className: "empty",
            textContent: `Can't reach the API at ${API}. Start it with: uvicorn backend.app.main:app --reload`,
        })));
    }
    loadModel();
}

async function loadModel() {
    try {
        const i = await api("/ml/info");
        $("#modelName").textContent = "ML model active";
        $("#modelNote").textContent = `${i.model_source}. Outcome labels: ${i.n_real_labels}/${i.min_real_labels_needed}`;
    } catch {
        $("#modelName").textContent = "Rule-based scoring";
        $("#modelNote").textContent = "ML endpoints not found on the backend yet.";
    }
}

// Prefer the ML endpoint; fall back to the old rule-based one if it is not installed.
async function scoreAll() {
    try {
        return await api("/ml/score", { method: "POST" });
    } catch (e) {
        if (e.status !== 404) throw e;
        await api("/leads/score", { method: "POST" });
        return { model_source: "rule-based (ML endpoints not installed)" };
    }
}

/* ---------- rendering ---------- */
function renderSummary() {
    const L = state.leads, n = (lv) => L.filter((l) => l.opportunity_level === lv).length;
    const scored = L.filter((l) => l.ai_opportunity_score != null);
    const avg = scored.length ? Math.round(scored.reduce((s, l) => s + l.ai_opportunity_score, 0) / scored.length) : 0;
    $("#statTotal").textContent = L.length;
    $("#statHigh").textContent = n("High");
    $("#statMedium").textContent = n("Medium");
    $("#statAvg").textContent = avg;
    const bar = $("#distBar");
    bar.replaceChildren();
    for (const lv of ["High", "Medium", "Low"]) {
        if (n(lv)) bar.append(h("span", { className: `seg ${lv.toLowerCase()}`, style: `flex:${n(lv)}`, textContent: `${lv} · ${n(lv)}` }));
    }
    if (!bar.children.length) bar.append(h("span", { className: "seg", textContent: "No scored leads yet" }));
}

function fillIndustries() {
    const sel = $("#fIndustry"), cur = sel.value;
    const inds = [...new Set(state.leads.map((l) => (l.industry ?? "").trim().toLowerCase()).filter(Boolean))].sort();
    sel.replaceChildren(h("option", { value: "", textContent: "All industries" }), ...inds.map((i) => h("option", { value: i, textContent: cap(i) })));
    sel.value = inds.includes(cur) ? cur : "";
}

function visible() {
    const q = $("#fSearch").value.trim().toLowerCase(), ind = $("#fIndustry").value, st = $("#fStatus").value;
    const sorts = {
        score: (a, b) => (b.ai_opportunity_score ?? -1) - (a.ai_opportunity_score ?? -1),
        low: (a, b) => (a.ai_opportunity_score ?? 101) - (b.ai_opportunity_score ?? 101),
        name: (a, b) => (a.business_name ?? "").localeCompare(b.business_name ?? ""),
        new: (a, b) => b.id - a.id,
    };
    return state.leads
        .filter((l) =>
            (!q || [l.business_name, l.industry, l.location, l.email].some((v) => (v ?? "").toLowerCase().includes(q))) &&
            (!ind || (l.industry ?? "").trim().toLowerCase() === ind) &&
            (!st || l.status === st) &&
            (!state.priority || l.opportunity_level === state.priority))
        .sort(sorts[$("#fSort").value]);
}

function row(l) {
    const score = l.ai_opportunity_score, lvl = l.opportunity_level;
    const contact = [l.phone, l.email, l.website].filter(Boolean).join(" · ");
    const status = h("select", { className: "status-select", onchange: (e) => changeStatus(l, e.target) },
        ...STATUSES.map((s) => h("option", { value: s, textContent: cap(s) })));
    status.value = l.status ?? "new";
    return h("tr", {},
        h("td", {}, h("div", { className: "name", textContent: l.business_name }),
            h("div", { className: "sub", textContent: l.ai_opportunity ?? "Not scored yet" }),
            contact ? h("div", { className: "sub", textContent: contact }) : null),
        h("td", {}, h("div", { textContent: cap(l.industry) || "—" }), h("div", { className: "sub", textContent: l.location ?? "" })),
        h("td", {}, score == null ? "—" : h("div", { className: "score" }, h("b", { textContent: score }), h("i", {}, h("u", { style: `width:${score}%` })))),
        h("td", {}, lvl ? h("span", { className: `badge ${lvl.toLowerCase()}`, textContent: lvl }) : "—"),
        h("td", {}, status),
        h("td", { className: "actions" },
            h("button", { className: "ghost sm", textContent: "Edit", onclick: () => openDialog(l) }),
            h("button", { className: "danger sm", textContent: "Delete", onclick: () => removeLead(l) })));
}

function render() {
    const list = visible(), pages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * PAGE_SIZE, rows = list.slice(start, start + PAGE_SIZE);
    $("#rows").replaceChildren(...(rows.length ? rows.map(row) : [h("tr", {}, h("td", {
        colSpan: 6, className: "empty",
        textContent: state.leads.length ? "No leads match your filters." : "No leads yet. Use “Find new leads” or add one manually.",
    }))]));
    $("#count").textContent = list.length ? `Showing ${start + 1}–${start + rows.length} of ${list.length}` : "0 leads";
    $("#prev").disabled = state.page <= 1;
    $("#next").disabled = state.page >= pages;
    document.querySelectorAll(".chip").forEach((c) => c.classList.toggle("on", c.dataset.p === state.priority));
}

/* ---------- actions ---------- */
async function changeStatus(lead, select) {
    try {
        await api(`/leads/${lead.id}`, { method: "PUT", body: JSON.stringify({ status: select.value }) });
        lead.status = select.value;
        toast(`${lead.business_name} marked ${select.value}. Outcomes like this train the ML model.`);
    } catch (e) {
        select.value = lead.status ?? "new";
        toast(`Could not update status: ${e.message}`, "err");
    }
}

async function removeLead(lead) {
    if (!confirm(`Delete "${lead.business_name}"? This cannot be undone.`)) return;
    try {
        await api(`/leads/${lead.id}`, { method: "DELETE" });
        toast("Lead deleted.");
        await load();
    } catch (e) {
        toast(`Could not delete: ${e.message}`, "err");
    }
}

const dlg = $("#leadDialog"), form = $("#leadForm");
let editing = null;

function openDialog(lead = null) {
    editing = lead;
    form.reset();
    $("#dlgTitle").textContent = lead ? "Edit lead" : "Add lead";
    $("#dlgError").textContent = "";
    $("#statusField").hidden = !lead;
    if (lead) for (const el of form.elements) if (el.name) el.value = lead[el.name] ?? (el.name === "status" ? "new" : "");
    dlg.showModal();
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {};
    for (const el of form.elements) {
        if (!el.name) continue;
        const v = el.value.trim();
        if (editing) body[el.name] = v || null;
        else if (v && el.name !== "status") body[el.name] = v;
    }
    const btn = form.querySelector('[type="submit"]');
    busy(btn, true, "Saving…");
    try {
        await api(editing ? `/leads/${editing.id}` : "/leads/", { method: editing ? "PUT" : "POST", body: JSON.stringify(body) });
        await scoreAll().catch(console.error);
        dlg.close();
        toast(editing ? "Lead updated." : "Lead added and scored.");
        await load();
    } catch (err) {
        $("#dlgError").textContent = err.message;
    } finally {
        busy(btn, false);
    }
});

$("#discoverForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.currentTarget, btn = f.querySelector("button"), out = $("#discoverMsg");
    const params = new URLSearchParams({ industry: f.elements.industry.value, location: f.elements.location.value.trim() });
    busy(btn, true, "Searching…");
    out.textContent = "Searching OpenStreetMap — this can take up to a minute.";
    try {
        const d = await api(`/search/leads/save?${params}`, { method: "POST" });
        out.textContent = `Found ${d.found}, saved ${d.saved} new, skipped ${d.skipped_duplicates} duplicate(s).`;
        await scoreAll().catch(console.error);
        toast(`${d.saved} new lead(s) saved and scored.`);
        await load();
    } catch (err) {
        out.textContent = `Search failed: ${err.message}`;
        toast("Lead search failed.", "err");
    } finally {
        busy(btn, false);
    }
});

$("#scoreBtn").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    busy(btn, true, "Scoring…");
    try {
        let info = null;
        try { info = await api("/ml/train", { method: "POST" }); } catch (err) { if (err.status !== 404) throw err; }
        const r = await scoreAll();
        await load();
        toast(`Scored with ${info?.model_source ?? r.model_source}.`);
    } catch (err) {
        toast(`Scoring failed: ${err.message}`, "err");
    } finally {
        busy(btn, false);
    }
});

$("#exportBtn").addEventListener("click", () => {
    const cols = ["business_name", "industry", "location", "website", "email", "phone", "ai_opportunity_score", "opportunity_level", "status", "ai_opportunity"];
    const esc = (v) => { let s = String(v ?? ""); if (/^[=+\-@]/.test(s)) s = "'" + s; return `"${s.replace(/"/g, '""')}"`; };
    const csv = [cols.join(","), ...visible().map((l) => cols.map((c) => esc(l[c])).join(","))].join("\n");
    const a = h("a", { href: URL.createObjectURL(new Blob([csv], { type: "text/csv" })), download: "leads.csv" });
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
});

/* ---------- wiring ---------- */
["#fSearch", "#fIndustry", "#fStatus", "#fSort"].forEach((s) => $(s).addEventListener("input", () => { state.page = 1; render(); }));
document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => { state.priority = c.dataset.p; state.page = 1; render(); }));
$("#prev").addEventListener("click", () => { state.page--; render(); });
$("#next").addEventListener("click", () => { state.page++; render(); });
$("#clearBtn").addEventListener("click", () => {
    ["#fSearch", "#fIndustry", "#fStatus"].forEach((s) => ($(s).value = ""));
    $("#fSort").value = "score";
    state.priority = "";
    state.page = 1;
    render();
});
$("#addBtn").addEventListener("click", () => openDialog());
$("#cancelBtn").addEventListener("click", () => dlg.close());
$("#refreshBtn").addEventListener("click", load);
document.querySelectorAll("nav a").forEach((a) => a.addEventListener("click", () => {
    document.querySelectorAll("nav a").forEach((x) => x.classList.toggle("active", x === a));
    if (a.dataset.p !== undefined) { state.priority = a.dataset.p; state.page = 1; render(); }
}));

load();
