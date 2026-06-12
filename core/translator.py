"""
app.py  –  AI Translator on Streamlit
======================================
Le API key non vengono mai salvate sul server.
L'utente può:
  • inserirle direttamente nei campi (session only)
  • caricare un file config.json locale → le chiavi vengono lette e restano in sessione
  • scaricare il proprio config.json per riutilizzarlo in futuro

Avvio:  streamlit run app.py
"""

import json
import sys
import os
import base64
import datetime

import streamlit as st

# Assicura che il package core sia importabile
sys.path.insert(0, os.path.dirname(__file__))

from core import (
    process,
    TranslationError,
    MODES,
    LANGUAGE_NAMES,
    GEMINI_MODELS,
    GEMINI_MODEL_NAMES,
    OPENROUTER_MODELS,
    OPENROUTER_MODEL_NAMES,
)

# ── Streamlit page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Translator",
    page_icon="⟺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────
DEFAULTS = {
    "gemini_api_key":    "",
    "openrouter_api_key": "",
    "provider":          "Gemini",
    "gemini_model":      GEMINI_MODEL_NAMES[0],
    "openrouter_model":  OPENROUTER_MODEL_NAMES[0],
    "mode":              "Translate",
    "source_lang":       "Auto-detect",
    "target_lang":       "English",
    "output_lang":       "English",
    "source_text":       "",
    "result_text":       "",
    "history":           [],        # list of dicts
    "settings_open":     False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helper: config dict (only persistent prefs, no secrets written to server) ─
def _session_to_config() -> dict:
    """Build a config dict to export. API keys ARE included (user's own file)."""
    return {
        "gemini_api_key":    st.session_state.gemini_api_key,
        "openrouter_api_key": st.session_state.openrouter_api_key,
        "provider":          st.session_state.provider,
        "gemini_model":      st.session_state.gemini_model,
        "openrouter_model":  st.session_state.openrouter_model,
        "mode":              st.session_state.mode,
        "source_lang":       st.session_state.source_lang,
        "target_lang":       st.session_state.target_lang,
        "output_lang":       st.session_state.output_lang,
    }


def _load_config(cfg: dict):
    """Load a config dict into session state."""
    allowed = set(DEFAULTS.keys()) - {"source_text", "result_text", "history", "settings_open"}
    for k, v in cfg.items():
        if k in allowed:
            st.session_state[k] = v


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global reset & base ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #0f1117;
}

[data-testid="stSidebar"] {
    background: #141720 !important;
    border-right: 1px solid #1e2433;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

/* ── Main header ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.75rem 0 1.25rem 0;
    border-bottom: 1px solid #1e2433;
    margin-bottom: 1.5rem;
}
.app-logo {
    font-size: 1.6rem;
    color: #6366f1;
    line-height: 1;
}
.app-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.01em;
}
.app-subtitle {
    font-size: 0.75rem;
    color: #475569;
    margin-top: 1px;
}

/* ── Mode pills ── */
.mode-row {
    display: flex;
    gap: 8px;
    margin-bottom: 1.25rem;
}
.mode-pill {
    padding: 6px 18px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid #2d3748;
    color: #64748b;
    background: #141720;
    transition: all 0.15s;
}
.mode-pill.active {
    background: #4f46e5;
    color: #fff;
    border-color: #4f46e5;
}

/* ── Text panels ── */
.panel-card {
    background: #141720;
    border: 1px solid #1e2433;
    border-radius: 12px;
    overflow: hidden;
    height: 100%;
}
.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    border-bottom: 1px solid #1e2433;
    background: #0f1117;
}
.panel-title {
    font-size: 0.7rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.char-count {
    font-size: 0.68rem;
    color: #334155;
}

/* ── Result box ── */
.result-box {
    background: #141720;
    border: 1px solid #1e2433;
    border-radius: 12px;
    padding: 18px 20px;
    min-height: 180px;
    color: #a5b4fc;
    font-size: 0.95rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
}
.result-placeholder {
    color: #334155;
    font-style: italic;
}

/* ── Status banner ── */
.status-ok    { background:#14532d22; border:1px solid #22c55e44;
                color:#4ade80; border-radius:8px; padding:8px 14px;
                font-size:0.82rem; margin-top:10px; }
.status-error { background:#7f1d1d22; border:1px solid #ef444444;
                color:#f87171; border-radius:8px; padding:8px 14px;
                font-size:0.82rem; margin-top:10px; }
.status-info  { background:#1e2433; border:1px solid #2d3748;
                color:#94a3b8; border-radius:8px; padding:8px 14px;
                font-size:0.82rem; margin-top:10px; }

/* ── Sidebar labels ── */
.sidebar-section {
    font-size: 0.68rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 1rem 0 0.4rem 0;
}

/* ── History item ── */
.hist-item {
    background: #0f1117;
    border: 1px solid #1e2433;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    font-size: 0.78rem;
    line-height: 1.5;
}
.hist-meta {
    color: #475569;
    font-size: 0.68rem;
    margin-bottom: 4px;
}
.hist-text {
    color: #94a3b8;
}

/* ── Streamlit widget overrides ── */
.stTextArea textarea {
    background: #0f1117 !important;
    border: none !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
    resize: none !important;
}
.stTextArea textarea::placeholder { color: #334155 !important; }
.stTextArea > label { display: none !important; }
div[data-baseweb="select"] > div {
    background: #1e2433 !important;
    border-color: #2d3748 !important;
    color: #cbd5e1 !important;
}
div[data-baseweb="select"] svg { color: #64748b !important; }

.stButton > button {
    background: #4f46e5;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.55rem 1.5rem;
    transition: background 0.15s;
    width: 100%;
}
.stButton > button:hover { background: #4338ca !important; }
.stButton > button:active { background: #3730a3 !important; }

.stDownloadButton > button {
    background: #1e2433 !important;
    color: #94a3b8 !important;
    border: 1px solid #2d3748 !important;
    border-radius: 7px !important;
    font-size: 0.82rem !important;
    padding: 0.35rem 1rem !important;
}
.stDownloadButton > button:hover {
    background: #2d3748 !important;
    color: #e2e8f0 !important;
}

[data-testid="stFileUploader"] {
    background: #141720 !important;
    border: 1px dashed #2d3748 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"] label { color: #64748b !important; }

.stRadio > label { color: #94a3b8 !important; font-size: 0.85rem !important; }
.stRadio > div   { gap: 0.5rem !important; }

h1, h2, h3 { color: #f1f5f9 !important; }
p, li { color: #94a3b8 !important; }

/* Remove Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:

    # ── App logo ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="app-header">
        <div class="app-logo">⟺</div>
        <div>
            <div class="app-title">AI Translator</div>
            <div class="app-subtitle">Powered by Gemini &amp; OpenRouter</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Provider & model ──────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Provider</div>', unsafe_allow_html=True)

    provider = st.selectbox(
        "provider",
        ["Gemini", "OpenRouter"],
        index=["Gemini", "OpenRouter"].index(st.session_state.provider),
        label_visibility="collapsed",
    )
    st.session_state.provider = provider

    if provider == "Gemini":
        model_names  = [GEMINI_MODELS[m] for m in GEMINI_MODEL_NAMES]
        model_ids    = GEMINI_MODEL_NAMES
        current_idx  = model_ids.index(st.session_state.gemini_model) \
                        if st.session_state.gemini_model in model_ids else 0
        model_choice = st.selectbox("Modello", model_names, index=current_idx,
                                    label_visibility="visible")
        st.session_state.gemini_model = model_ids[model_names.index(model_choice)]
    else:
        model_names  = [OPENROUTER_MODELS[m] for m in OPENROUTER_MODEL_NAMES]
        model_ids    = OPENROUTER_MODEL_NAMES
        current_idx  = model_ids.index(st.session_state.openrouter_model) \
                        if st.session_state.openrouter_model in model_ids else 0
        model_choice = st.selectbox("Modello", model_names, index=current_idx,
                                    label_visibility="visible")
        st.session_state.openrouter_model = model_ids[model_names.index(model_choice)]

    # ── Mode ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">Modalità</div>', unsafe_allow_html=True)
    mode = st.radio(
        "mode",
        MODES,
        index=MODES.index(st.session_state.mode),
        label_visibility="collapsed",
    )
    st.session_state.mode = mode

    # ── Language selectors ────────────────────────────────────────────────────
    if mode == "Translate":
        st.markdown('<div class="sidebar-section">Lingua sorgente</div>',
                    unsafe_allow_html=True)
        src_idx = LANGUAGE_NAMES.index(st.session_state.source_lang) \
                  if st.session_state.source_lang in LANGUAGE_NAMES else 0
        src_lang = st.selectbox("src", LANGUAGE_NAMES, index=src_idx,
                                label_visibility="collapsed")
        st.session_state.source_lang = src_lang

        st.markdown('<div class="sidebar-section">Lingua target</div>',
                    unsafe_allow_html=True)
        tgt_options = [l for l in LANGUAGE_NAMES if l != "Auto-detect"]
        tgt_idx     = tgt_options.index(st.session_state.target_lang) \
                      if st.session_state.target_lang in tgt_options else \
                      tgt_options.index("English")
        tgt_lang = st.selectbox("tgt", tgt_options, index=tgt_idx,
                                label_visibility="collapsed")
        st.session_state.target_lang = tgt_lang
    else:
        st.markdown('<div class="sidebar-section">Lingua output (opzionale)</div>',
                    unsafe_allow_html=True)
        out_options = ["Stessa lingua"] + [l for l in LANGUAGE_NAMES if l != "Auto-detect"]
        out_idx     = out_options.index(st.session_state.output_lang) \
                      if st.session_state.output_lang in out_options else 0
        out_lang = st.selectbox("out", out_options, index=out_idx,
                                label_visibility="collapsed")
        st.session_state.output_lang = out_lang

    # ── Settings expander ─────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">⚙ Impostazioni API</div>',
                unsafe_allow_html=True)

    with st.expander("Configura chiavi API", expanded=False):

        st.markdown("**Gemini API Key**")
        g_key = st.text_input(
            "gemini_key",
            value=st.session_state.gemini_api_key,
            type="password",
            placeholder="Incolla la tua Gemini API key",
            label_visibility="collapsed",
        )
        st.markdown(
            '<a href="https://aistudio.google.com/apikey" target="_blank" '
            'style="color:#6366f1;font-size:0.75rem;">→ Ottieni chiave gratuita</a>',
            unsafe_allow_html=True,
        )

        st.markdown("**OpenRouter API Key**")
        or_key = st.text_input(
            "or_key",
            value=st.session_state.openrouter_api_key,
            type="password",
            placeholder="Incolla la tua OpenRouter API key",
            label_visibility="collapsed",
        )
        st.markdown(
            '<a href="https://openrouter.ai/keys" target="_blank" '
            'style="color:#6366f1;font-size:0.75rem;">→ Ottieni chiave</a>',
            unsafe_allow_html=True,
        )

        if st.button("💾 Salva in sessione", key="save_keys"):
            st.session_state.gemini_api_key    = g_key.strip()
            st.session_state.openrouter_api_key = or_key.strip()
            st.success("Chiavi salvate per questa sessione.")

    # ── Config file: Export ───────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">📁 File di configurazione</div>',
                unsafe_allow_html=True)

    cfg_json = json.dumps(_session_to_config(), indent=2, ensure_ascii=False)
    st.download_button(
        label="⬇ Scarica config.json",
        data=cfg_json,
        file_name="ai_translator_config.json",
        mime="application/json",
        help="Salva le tue preferenze e chiavi localmente — nessun dato va sul server.",
        use_container_width=True,
    )

    # ── Config file: Import ───────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Carica config.json",
        type=["json"],
        help="Il file viene letto solo localmente, nulla viene caricato su server.",
        label_visibility="visible",
    )
    if uploaded is not None:
        try:
            cfg_loaded = json.loads(uploaded.read().decode("utf-8"))
            _load_config(cfg_loaded)
            st.success("Configurazione caricata!")
            st.rerun()
        except Exception as e:
            st.error(f"Errore nel file: {e}")

    # ── History ───────────────────────────────────────────────────────────────
    if st.session_state.history:
        st.markdown('<div class="sidebar-section">🕒 Cronologia</div>',
                    unsafe_allow_html=True)
        for i, h in enumerate(reversed(st.session_state.history[-10:])):
            with st.expander(f"{h['mode']} – {h['ts']}", expanded=False):
                st.markdown(
                    f"<div class='hist-meta'>{h['provider']} · {h.get('lang_info','')}</div>"
                    f"<div class='hist-text'><b>Input:</b> {h['source'][:120]}…</div>"
                    f"<div class='hist-text' style='color:#a5b4fc'><b>Output:</b> {h['result'][:120]}…</div>",
                    unsafe_allow_html=True,
                )
        if st.button("🗑 Cancella cronologia", key="clear_hist"):
            st.session_state.history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════

mode     = st.session_state.mode
provider = st.session_state.provider

# ── Mode pill header ──────────────────────────────────────────────────────────
mode_icons = {"Translate": "🌐", "Summarize": "📝", "Improve": "✨"}
mode_descs = {
    "Translate": "Traduci testo tra più di 55 lingue",
    "Summarize": "Sintetizza testi lunghi nei punti chiave",
    "Improve":   "Migliora chiarezza, grammatica e stile",
}

st.markdown(f"""
<div style="margin-bottom:1.25rem">
    <div style="font-size:1.05rem;font-weight:700;color:#f1f5f9;margin-bottom:3px">
        {mode_icons[mode]} {mode}
    </div>
    <div style="font-size:0.8rem;color:#64748b">{mode_descs[mode]}</div>
</div>
""", unsafe_allow_html=True)

# ── Two-column layout ─────────────────────────────────────────────────────────
col_src, col_tgt = st.columns([1, 1], gap="medium")

with col_src:
    # Panel header
    src_title = "Testo sorgente" if mode == "Translate" else "Testo originale"
    source_text = st.session_state.source_text
    char_n = len(source_text)

    st.markdown(f"""
    <div class="panel-header" style="background:#141720;border:1px solid #1e2433;
         border-bottom:none;border-radius:12px 12px 0 0;margin-bottom:0">
        <span class="panel-title">{src_title}</span>
        <span class="char-count">{char_n:,} caratteri</span>
    </div>
    """, unsafe_allow_html=True)

    new_text = st.text_area(
        "source",
        value=source_text,
        height=280,
        placeholder={
            "Translate": "Inserisci il testo da tradurre…\n\nSuggerimento: fai clic su Traduci o premi il pulsante qui sotto.",
            "Summarize": "Inserisci il testo da riassumere…",
            "Improve":   "Inserisci il testo da migliorare…",
        }[mode],
        label_visibility="collapsed",
        key="source_input",
    )
    st.session_state.source_text = new_text

with col_tgt:
    tgt_title = {
        "Translate": "Traduzione",
        "Summarize": "Riassunto",
        "Improve":   "Testo migliorato",
    }[mode]

    res = st.session_state.result_text
    res_chars = len(res) if res else 0

    st.markdown(f"""
    <div class="panel-header" style="background:#141720;border:1px solid #1e2433;
         border-bottom:none;border-radius:12px 12px 0 0;margin-bottom:0">
        <span class="panel-title">{tgt_title}</span>
        <span class="char-count">{res_chars:,} caratteri</span>
    </div>
    """, unsafe_allow_html=True)

    if res:
        st.markdown(f'<div class="result-box">{res}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="result-box result-placeholder">'
            f'Il {tgt_title.lower()} apparirà qui…</div>',
            unsafe_allow_html=True,
        )

# ── Action row ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

btn_label = {"Translate": "🌐  Traduci", "Summarize": "📝  Riassumi", "Improve": "✨  Migliora"}[mode]

col_btn, col_copy, col_clear = st.columns([2, 1, 1], gap="small")

with col_btn:
    run_clicked = st.button(btn_label, use_container_width=True, key="run_btn")

with col_copy:
    if st.session_state.result_text:
        # Streamlit doesn't have native clipboard API; offer download as fallback
        st.download_button(
            "⎘  Copia (salva)",
            data=st.session_state.result_text,
            file_name="output.txt",
            mime="text/plain",
            use_container_width=True,
            key="copy_btn",
        )

with col_clear:
    if st.button("✕  Cancella", use_container_width=True, key="clear_btn"):
        st.session_state.source_text = ""
        st.session_state.result_text = ""
        st.rerun()

# ── Run translation ───────────────────────────────────────────────────────────
if run_clicked:
    text = st.session_state.source_text.strip()
    if not text:
        st.markdown(
            f'<div class="status-info">⬅ Inserisci del testo prima di procedere.</div>',
            unsafe_allow_html=True,
        )
    else:
        gemini_key    = st.session_state.gemini_api_key
        or_key        = st.session_state.openrouter_api_key
        gemini_model  = st.session_state.gemini_model
        or_model      = st.session_state.openrouter_model
        src_lang      = st.session_state.source_lang
        tgt_lang      = st.session_state.target_lang
        out_lang_raw  = st.session_state.output_lang
        out_lang      = "" if out_lang_raw == "Stessa lingua" else out_lang_raw

        # Quick key check before calling API
        if provider == "Gemini" and not gemini_key:
            st.markdown(
                '<div class="status-error">⚠ Gemini API key mancante. '
                'Aprire ⚙ Impostazioni nella barra laterale.</div>',
                unsafe_allow_html=True,
            )
            st.stop()
        if provider == "OpenRouter" and not or_key:
            st.markdown(
                '<div class="status-error">⚠ OpenRouter API key mancante. '
                'Aprire ⚙ Impostazioni nella barra laterale.</div>',
                unsafe_allow_html=True,
            )
            st.stop()

        spinner_msg = {
            "Translate": "Traduzione in corso…",
            "Summarize": "Riassunto in corso…",
            "Improve":   "Miglioramento in corso…",
        }[mode]

        with st.spinner(spinner_msg):
            try:
                result = process(
                    text=text,
                    mode=mode,
                    provider=provider,
                    gemini_key=gemini_key,
                    openrouter_key=or_key,
                    gemini_model=gemini_model,
                    openrouter_model=or_model,
                    source_lang=src_lang,
                    target_lang=tgt_lang,
                    output_lang=out_lang,
                )
                st.session_state.result_text = result

                # Add to history
                lang_info = (
                    f"{src_lang} → {tgt_lang}" if mode == "Translate"
                    else (f"→ {out_lang}" if out_lang else "stessa lingua")
                )
                st.session_state.history.append({
                    "ts":       datetime.datetime.now().strftime("%H:%M"),
                    "mode":     mode,
                    "provider": provider,
                    "lang_info": lang_info,
                    "source":   text,
                    "result":   result,
                })

                st.rerun()   # refresh UI with result

            except TranslationError as exc:
                short = str(exc).splitlines()[0][:120]
                st.markdown(
                    f'<div class="status-error">⚠ Errore: {short}</div>',
                    unsafe_allow_html=True,
                )
            except Exception as exc:
                st.markdown(
                    f'<div class="status-error">⚠ Errore inatteso: {exc}</div>',
                    unsafe_allow_html=True,
                )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-top:2.5rem;padding-top:1rem;
     border-top:1px solid #1e2433;font-size:0.72rem;color:#334155">
    Le chiavi API vengono salvate <strong style="color:#475569">solo nella tua sessione browser</strong>
    o nel file config.json locale — nessun dato viene inviato a server diversi da Gemini / OpenRouter.
</div>
""", unsafe_allow_html=True)
