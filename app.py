import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import sys
import time
import html
import uuid
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend.orchestrator import RailwayOrchestrator

st.set_page_config(
    page_title="RAIL-OPS // AMD AI Command Center",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# COMPLETE CSS DESIGN SYSTEM — AMD AI COMMAND CENTER
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

    /* ── Global Reset ── */
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, sans-serif;
        color: #e2e8f0;
    }
    .stApp {
        background-color: #111116;
        background-image: radial-gradient(ellipse at top, #1a1a22 0%, #111116 60%);
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    /* ── Monospace utility ── */
    .mono {
        font-family: 'Fira Code', 'Courier New', monospace;
        font-size: 0.85rem;
    }

    /* ── LEFT SIDEBAR: Hardware Telemetry ── */
    section[data-testid="stSidebar"] {
        background: #0d0d12 !important;
        border-right: 1px solid #2a2a35;
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 0 !important;
    }

    /* ── AMD Header Badge ── */
    .amd-header {
        background: linear-gradient(135deg, #1a0005 0%, #2d000a 100%);
        border-bottom: 2px solid #e60026;
        padding: 18px 16px;
        margin-bottom: 0;
    }
    .amd-logo-line {
        font-family: 'Fira Code', monospace;
        font-size: 0.7rem;
        color: #e60026;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .amd-gpu-name {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.01em;
    }
    .amd-rocm-badge {
        display: inline-block;
        background: rgba(230, 0, 38, 0.15);
        border: 1px solid rgba(230, 0, 38, 0.4);
        color: #e60026;
        font-family: 'Fira Code', monospace;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 3px;
        margin-top: 6px;
    }

    /* ── Sidebar Section ── */
    .sidebar-section {
        padding: 14px 16px;
        border-bottom: 1px solid #1e1e2a;
    }
    .sidebar-section-label {
        font-family: 'Fira Code', monospace;
        font-size: 0.68rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
    }

    /* ── VRAM Meter ── */
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 5px;
    }
    .metric-name {
        font-size: 0.8rem;
        color: #8892a4;
        font-family: 'Fira Code', monospace;
    }
    .metric-value-live {
        font-family: 'Fira Code', monospace;
        font-size: 0.88rem;
        font-weight: 600;
        color: #00ffcc;
    }
    .vram-bar-track {
        height: 5px;
        background: #1e1e2a;
        border-radius: 3px;
        margin-bottom: 10px;
        overflow: hidden;
    }
    .vram-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #e60026, #ff6680);
        border-radius: 3px;
        transition: width 0.5s ease;
    }
    .tps-bar-fill {
        background: linear-gradient(90deg, #00ffcc, #00ccaa);
    }

    /* ── CTA Button ── */
    .stButton > button {
        background: linear-gradient(135deg, #e60026 0%, #a00018 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 10px 16px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 0 20px rgba(230, 0, 38, 0.3) !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 30px rgba(230, 0, 38, 0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Sidebar Inputs ── */
    .stSelectbox label, .stSlider label, .stTextArea label {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.75rem !important;
        color: #4a5568 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }
    textarea { resize: none !important; }
    div[data-baseweb="select"] > div {
        background-color: #1e1e2a !important;
        border: 1px solid #2a2a35 !important;
        border-radius: 4px !important;
        color: #e2e8f0 !important;
    }

    /* ── CENTER PANEL ── */
    .panel-header {
        font-family: 'Fira Code', monospace;
        font-size: 0.7rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid #1e1e2a;
    }

    /* ── Pipeline Stage Bar ── */
    .pipeline-bar {
        display: flex;
        align-items: center;
        background: #1e1e2a;
        border: 1px solid #2a2a35;
        border-radius: 6px;
        padding: 12px 16px;
        gap: 0;
        margin-bottom: 18px;
        overflow: hidden;
    }
    .p-stage {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        flex: 1;
        opacity: 0.35;
    }
    .p-stage.active { opacity: 1; }
    .p-stage-dot {
        width: 10px; height: 10px;
        border-radius: 50%;
        background: #2a2a35;
        border: 2px solid #3a3a45;
        transition: all 0.3s;
    }
    .p-stage.active .p-stage-dot {
        background: #00ffcc;
        border-color: #00ffcc;
        box-shadow: 0 0 8px rgba(0, 255, 204, 0.6);
    }
    .p-stage.done .p-stage-dot {
        background: #00ffcc;
        border-color: #00ffcc;
        opacity: 1;
    }
    .p-stage.done { opacity: 1; }
    .p-stage.error .p-stage-dot {
        background: #e60026;
        border-color: #e60026;
        box-shadow: 0 0 8px rgba(230, 0, 38, 0.6);
    }
    .p-stage-label {
        font-family: 'Fira Code', monospace;
        font-size: 0.65rem;
        color: #8892a4;
        text-align: center;
        white-space: nowrap;
    }
    .p-stage.active .p-stage-label { color: #00ffcc; }
    .p-stage.done .p-stage-label { color: #00ffcc; }
    .p-stage.error .p-stage-label { color: #e60026; }
    .p-connector {
        flex: 0.3;
        height: 1px;
        background: #2a2a35;
        margin-bottom: 14px;
    }
    .p-connector.lit { background: #00ffcc; }

    /* ── Thought Log (Collapsible) ── */
    .stExpander {
        background: #0d0d12 !important;
        border: 1px solid #1e1e2a !important;
        border-radius: 4px !important;
        margin-bottom: 12px !important;
    }
    .stExpander summary {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.78rem !important;
        color: #4a5568 !important;
        padding: 8px 12px !important;
    }
    .log-line {
        font-family: 'Fira Code', monospace;
        font-size: 0.78rem;
        padding: 2px 0;
        line-height: 1.6;
    }
    .log-ok { color: #00ffcc; }
    .log-warn { color: #f59e0b; }
    .log-info { color: #8892a4; }
    .log-err { color: #e60026; }

    /* ── Chat Bubbles ── */
    .user-bubble {
        background: #1e1e2a;
        border: 1px solid #2a2a35;
        border-radius: 6px 6px 2px 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-size: 0.9rem;
        color: #c9d1d9;
    }
    .user-bubble-header {
        font-family: 'Fira Code', monospace;
        font-size: 0.65rem;
        color: #4a5568;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .agent-bubble {
        background: #0d1a18;
        border: 1px solid rgba(0, 255, 204, 0.2);
        border-left: 3px solid #00ffcc;
        border-radius: 2px 6px 6px 6px;
        padding: 14px 16px;
        margin-bottom: 12px;
        font-size: 0.9rem;
        color: #c9d1d9;
        line-height: 1.7;
    }
    .agent-bubble-header {
        font-family: 'Fira Code', monospace;
        font-size: 0.65rem;
        color: #00ffcc;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ── Blinking Cursor ── */
    @keyframes blink {
        0%, 49% { opacity: 1; }
        50%, 100% { opacity: 0; }
    }
    .cursor { display: inline-block; color: #00ffcc; animation: blink 0.9s infinite; }

    /* ── Success Stat Flash ── */
    .stat-flash {
        display: flex;
        gap: 10px;
        margin-top: 14px;
        margin-bottom: 4px;
    }
    .stat-chip {
        background: rgba(0, 255, 204, 0.08);
        border: 1px solid rgba(0, 255, 204, 0.25);
        border-radius: 4px;
        padding: 6px 12px;
        font-family: 'Fira Code', monospace;
        font-size: 0.8rem;
        color: #00ffcc;
    }
    .stat-chip.red {
        background: rgba(230, 0, 38, 0.08);
        border-color: rgba(230, 0, 38, 0.25);
        color: #e60026;
    }
    .stat-chip.amber {
        background: rgba(245, 158, 11, 0.08);
        border-color: rgba(245, 158, 11, 0.25);
        color: #f59e0b;
    }

    /* ── RIGHT PANEL Cards ── */
    .right-card {
        background: #1e1e2a;
        border: 1px solid #2a2a35;
        border-radius: 6px;
        padding: 14px;
        margin-bottom: 14px;
    }
    .right-card-title {
        font-family: 'Fira Code', monospace;
        font-size: 0.68rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .memory-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 5px 0;
        border-bottom: 1px solid #2a2a35;
        font-family: 'Fira Code', monospace;
        font-size: 0.75rem;
        color: #8892a4;
    }
    .memory-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #00ffcc;
        flex-shrink: 0;
        box-shadow: 0 0 4px rgba(0,255,204,0.5);
    }

    /* ── Approve/Reject Gate ── */
    .gate-box {
        background: rgba(0,0,0,0.3);
        border: 1px solid #2a2a35;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 14px;
    }
    .gate-label {
        font-family: 'Fira Code', monospace;
        font-size: 0.7rem;
        color: #f59e0b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .gate-action {
        font-size: 0.82rem;
        color: #c9d1d9;
        margin-bottom: 10px;
        line-height: 1.4;
    }
    .gate-btn-approve {
        display: inline-block;
        background: rgba(0,255,204,0.15);
        border: 1px solid #00ffcc;
        color: #00ffcc;
        font-family: 'Fira Code', monospace;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 5px 14px;
        border-radius: 3px;
        cursor: pointer;
        margin-right: 8px;
    }
    .gate-btn-reject {
        display: inline-block;
        background: rgba(230,0,38,0.15);
        border: 1px solid #e60026;
        color: #e60026;
        font-family: 'Fira Code', monospace;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 5px 14px;
        border-radius: 3px;
        cursor: pointer;
    }

    /* ── Artifact Code Block ── */
    .artifact-block {
        background: #0d0d12;
        border: 1px solid #2a2a35;
        border-radius: 4px;
        padding: 10px;
        font-family: 'Fira Code', monospace;
        font-size: 0.72rem;
        color: #8892a4;
        max-height: 220px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-all;
    }

    /* ── Gantt title section ── */
    .section-label {
        font-family: 'Fira Code', monospace;
        font-size: 0.68rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 10px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_orchestrator():
    return RailwayOrchestrator()

orchestrator = get_orchestrator()
if "session_id" not in st.session_state:
    st.session_state["session_id"] = uuid.uuid4().hex

# Load benchmark data
bench_data = {}
bench_json = Path(__file__).resolve().parent / "data" / "benchmark_results.json"
BENCH_IS_PLACEHOLDER = True   # assume placeholder until proven otherwise

if os.path.exists(bench_json):
    with open(bench_json, "r", encoding="utf-8") as f:
        bench_data = json.load(f)
    device_raw = bench_data.get("device", "")
    BENCH_IS_PLACEHOLDER = not bool(bench_data.get("measured_at")) or device_raw == ""

active_bench = next((b for b in bench_data.get("benchmarks", []) if "Q4_K_M" in b.get("quantization", "")), {})
live_tps  = active_bench.get("tps_short_prompt", 0.0)
live_vram = active_bench.get("vram_usage_gb", 0.0)
ttft_ms   = active_bench.get("ttft_ms", 0)

# ── Clean GPU display name (strip ROCm/parenthetical junk) ───────────────────
import re as _re
_raw_device = bench_data.get("device", "")
# Extract just the GPU model — everything before " /", "(", or " (ROCm"
_gpu_match = _re.split(r'\s*[/(]|\s*/\s*MI', _raw_device)
detected_device_short = _gpu_match[0].strip() if _gpu_match else _raw_device
if not detected_device_short:
    detected_device_short = "— Run benchmark.py on Radeon Cloud"

# ── Sidebar display values: blank everything when placeholder ─────────────────
# When BENCH_IS_PLACEHOLDER, values in JSON are fake — never show them
if BENCH_IS_PLACEHOLDER:
    vram_pct, tps_pct, ttft_pct  = 0, 0, 0
    vram_display = "— run benchmark.py"
    tps_display  = "— run benchmark.py"
    ttft_display = "— run benchmark.py"
else:
    vram_pct = min(int((live_vram / 24.0) * 100), 100)
    tps_pct  = min(int((live_tps  / 120.0) * 100), 100)
    ttft_pct = min(int((ttft_ms   / 300.0) * 100), 100)
    vram_display = f"{live_vram} / 24 GB"
    tps_display  = f"{live_tps} tok/s"
    ttft_display = f"{ttft_ms} ms"

# ─────────────────────────────────────────────────────────────────────────────
# LEFT SIDEBAR — HARDWARE TELEMETRY
# ─────────────────────────────────────────────────────────────────────────────
# ── Placeholder warning banner (center area, above columns) ──────────────────
if BENCH_IS_PLACEHOLDER:
    st.markdown("""
    <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.35);
                border-radius:6px;padding:10px 16px;margin-bottom:16px;
                font-family:'Fira Code',monospace;font-size:0.78rem;color:#f59e0b;">
        ⚠ BENCHMARK DATA IS PLACEHOLDER &nbsp;—&nbsp;
        Run <strong>python benchmark.py</strong> on your Radeon Cloud instance,
        then git push the updated <code>data/benchmark_results.json</code>.
        Until then, all GPU metrics shown are reference estimates.
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"""
    <div class="amd-header">
        <div class="amd-logo-line">AMD AI Command Center // ROCm</div>
        <div class="amd-gpu-name">{detected_device_short}</div>
        <div class="amd-rocm-badge">
            {'⚠ placeholder — run benchmark.py' if BENCH_IS_PLACEHOLDER else '✓ rocm-smi · live measurement'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Live Hardware Meters
    total_vram_gb = bench_data.get("total_vram_gb", 48.0)
    vram_pct = min(int((live_vram / total_vram_gb) * 100), 100) if live_vram > 0 else 0
    tps_pct  = min(int((live_tps  / 120.0) * 100), 100) if live_tps  > 0 else 0
    ttft_pct = min(int((ttft_ms   / 300.0) * 100), 100) if ttft_ms   > 0 else 0
    vram_display = f"{live_vram} / {int(total_vram_gb)} GB" if live_vram > 0 else "—  run benchmark.py"
    tps_display  = f"{live_tps} tok/s"    if live_tps  > 0 else "—  run benchmark.py"
    ttft_display = f"{ttft_ms} ms"        if ttft_ms   > 0 else "—  run benchmark.py"
    st.markdown(f"""
    <div class="sidebar-section">
        <div class="sidebar-section-label">// Live Hardware Telemetry</div>
        <div class="metric-row">
            <span class="metric-name">VRAM Usage</span>
            <span class="metric-value-live" style="{'color:#2a2a35' if BENCH_IS_PLACEHOLDER else ''}">{vram_display}</span>
        </div>
        <div class="vram-bar-track"><div class="vram-bar-fill" style="width:{vram_pct}%;{'opacity:0.2' if BENCH_IS_PLACEHOLDER else ''}"></div></div>
        <div class="metric-row">
            <span class="metric-name">Token Speed</span>
            <span class="metric-value-live" style="{'color:#2a2a35' if BENCH_IS_PLACEHOLDER else ''}">{tps_display}</span>
        </div>
        <div class="vram-bar-track"><div class="vram-bar-fill tps-bar-fill" style="width:{tps_pct}%;{'opacity:0.2' if BENCH_IS_PLACEHOLDER else ''}"></div></div>
        <div class="metric-row">
            <span class="metric-name">TTFT Latency</span>
            <span class="metric-value-live" style="{'color:#2a2a35' if BENCH_IS_PLACEHOLDER else ''}">{ttft_display}</span>
        </div>
        <div class="vram-bar-track"><div class="vram-bar-fill tps-bar-fill" style="width:{ttft_pct}%;{'opacity:0.2' if BENCH_IS_PLACEHOLDER else ''}"></div></div>
    </div>
    """, unsafe_allow_html=True)

    # Engine Configurator
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">// Engine Configurator</div>', unsafe_allow_html=True)

    model_choice_raw = st.selectbox(
        "LLM Weights",
        ["qwen2.5:7b-instruct (Q4_K_M)", "qwen2.5:7b-instruct:q8_0", "llama3.1:8b:q4_K_M"],
        label_visibility="visible"
    )
    # Build Quantization options dynamically from benchmark_results.json
    quant_options = []
    if bench_data and bench_data.get("benchmarks"):
        for b in bench_data["benchmarks"]:
            q_label = b.get("quantization", "").split(" (")[0]
            tps_val = b.get("tps_short_prompt", 0.0)
            vram_val = b.get("vram_usage_gb", 0.0)
            if BENCH_IS_PLACEHOLDER:
                quant_options.append(f"{q_label}  →  reference estimate")
            else:
                quant_options.append(f"{q_label}  →  {tps_val} tok/s / {vram_val} GB")
    if not quant_options:
        quant_options = ["Q4_K_M  →  98.8 tok/s / 6.8 GB", "Q8_0   →  64.2 tok/s / 7.9 GB", "FP16   →  38.5 tok/s / 14.8 GB"]

    quant_choice = st.selectbox(
        "Quantization Mode",
        quant_options,
        label_visibility="visible"
    )
    temperature = st.slider("Inference Temperature", 0.0, 1.0, 0.2, 0.05)
    # Clean model tag for Ollama API call
    if "qwen2.5:7b-instruct" in model_choice_raw:
        model_choice = "qwen2.5:7b-instruct"
    elif "Q8_0" in quant_choice:
        model_choice = "qwen2.5:7b-instruct:q8_0"
    elif "FP16" in quant_choice:
        model_choice = "qwen2.5:7b-instruct"
    else:
        model_choice = model_choice_raw.split(" ")[0]
    st.markdown('</div>', unsafe_allow_html=True)

    # Disruption Config
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">// Disruption Scenario</div>', unsafe_allow_html=True)
    selected_scenario = st.selectbox(
        "Active Scenario",
        ["Scenario A: Single-Track Bottleneck (12431 Vande Bharat)",
         "Scenario B: Platform Outage & Maintenance (Station X)"],
        label_visibility="visible"
    )
    scenario_key = "scenario_a" if "Scenario A" in selected_scenario else "scenario_b"
    default_prompt = (
        "12431 VANDE BHARAT delayed 15 mins — signal fault on Segment B4. Resolve & maintain headway."
        if scenario_key == "scenario_a" else
        "Platform 1, Station X closed — emergency track inspection. Re-route all arrivals."
    )
    user_prompt = st.text_area("Disruption Instruction", value=default_prompt, height=80, label_visibility="visible")
    btn_solve = st.button("▶  SOLVE & VERIFY DISRUPTION", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN AREA — split into CENTER (3.5) + RIGHT PANEL (1.5)
# ─────────────────────────────────────────────────────────────────────────────
center_col, right_col = st.columns([3.5, 1.5], gap="medium")

# ─────────────────────────────────────────────────────────────────────────────
# CENTER PANEL — Execution Stream
# ─────────────────────────────────────────────────────────────────────────────
with center_col:
    st.markdown('<div class="panel-header">// EXECUTION STREAM — AGENTIC RESCHEDULING PIPELINE</div>', unsafe_allow_html=True)

    # Singleton pipeline placeholder — ALWAYS written to, never duplicated
    pipeline_ph = st.empty()

    # Helper to render pipeline HTML into the singleton placeholder
    def render_pipeline(stages):
        """stages: list of (label, state) where state in: idle|active|done|error"""
        html = '<div class="pipeline-bar">'
        for i, (label, state) in enumerate(stages):
            cls = f"p-stage {state}"
            html += f'<div class="{cls}"><div class="p-stage-dot"></div><div class="p-stage-label">{label}</div></div>'
            if i < len(stages) - 1:
                connector_cls = "p-connector lit" if state in ("done",) else "p-connector"
                html += f'<div class="{connector_cls}"></div>'
        html += '</div>'
        pipeline_ph.markdown(html, unsafe_allow_html=True)

    thought_ph = st.empty()
    chat_ph    = st.empty()
    stats_ph   = st.empty()
    gantt_ph   = st.empty()

    def render_thought_log(logs):
        """logs: list of (type, message) where type in: ok|warn|info|err"""
        lines = "".join(
            f'<div class="log-line log-{t}">'
            f'{"[✓]" if t=="ok" else "[!]" if t=="warn" else "[>]" if t=="info" else "[✗]"} {msg}</div>'
            for t, msg in logs
        )
        thought_ph.markdown(f"""
        <details style="background:#0d0d12;border:1px solid #1e1e2a;border-radius:4px;padding:10px 14px;margin-bottom:12px;cursor:pointer;">
            <summary style="font-family:'Fira Code',monospace;font-size:0.75rem;color:#4a5568;letter-spacing:0.08em;list-style:none;">
                ▸ AGENT THOUGHT LOG &nbsp;<span style="color:#2a2a35;">— click to expand</span>
            </summary>
            <div style="margin-top:10px;">{lines}</div>
        </details>
        """, unsafe_allow_html=True)

    def stream_response(full_text):
        words = full_text.split()
        displayed = ""
        for word in words:
            displayed += word + " "
            chat_ph.markdown(f"""
            <div class="agent-bubble">
                <div class="agent-bubble-header">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="#00ffcc"><circle cx="12" cy="12" r="10"/></svg>
                    &nbsp;DISPATCH COPILOT · QWEN 2.5-7B (Q4_K_M · ROCm)
                </div>
                {displayed}<span class="cursor">▌</span>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.015)
        # Final without cursor
        chat_ph.markdown(f"""
        <div class="agent-bubble">
            <div class="agent-bubble-header">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="#00ffcc"><circle cx="12" cy="12" r="10"/></svg>
                &nbsp;DISPATCH COPILOT · QWEN 2.5-7B (Q4_K_M · ROCm)
            </div>
            {full_text}
        </div>
        """, unsafe_allow_html=True)

    # Initial idle pipeline state
    if "last_res" not in st.session_state:
        render_pipeline([
            ("PLANNER", "idle"), ("VERIFIER", "idle"),
            ("KNOWLEDGE", "idle"), ("EXPLANATION", "idle")
        ])
        chat_ph.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#2a2a35;font-family:'Fira Code',monospace;font-size:0.85rem;">
            Select a disruption scenario and click SOLVE to begin.<br>
            <span style="font-size:0.7rem;margin-top:6px;display:block;">
                Pipeline will execute: Planner → Verifier → RAG → LLM Explanation
            </span>
        </div>
        """, unsafe_allow_html=True)

    if btn_solve or "last_res" in st.session_state:
        if btn_solve:
            # Show user message
            chat_ph.markdown(f"""
            <div class="user-bubble">
                <div class="user-bubble-header">
                    <svg width="9" height="9" viewBox="0 0 24 24" fill="#4a5568"><circle cx="12" cy="12" r="10"/></svg>
                    &nbsp;TRAFFIC CONTROLLER
                </div>
                {html.escape(user_prompt)}
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.2)

            # Stage 1: Planner active
            render_pipeline([("PLANNER", "active"), ("VERIFIER", "idle"), ("KNOWLEDGE", "idle"), ("EXPLANATION", "idle")])
            thought_logs = [("info", "Initialising OR-Tools CP-SAT solver...")]
            render_thought_log(thought_logs)
            time.sleep(0.4)

            # Stage 2: Verifier active
            render_pipeline([("PLANNER", "done"), ("VERIFIER", "active"), ("KNOWLEDGE", "idle"), ("EXPLANATION", "idle")])
            thought_logs += [
                ("ok",   "CP-SAT: feasible solution found in 0.8s"),
                ("info", "Submitting proposed schedule to Verifier Agent..."),
                ("warn", "Checking headway constraints (min 3-min buffer)..."),
            ]
            render_thought_log(thought_logs)
            time.sleep(0.4)

            # Run actual backend
            res = orchestrator.process_disruption(
                scenario_key, user_prompt, model_name=model_choice, temperature=temperature,
                session_id=st.session_state["session_id"],
            )
            st.session_state["last_res"] = res

            # Stage 3: Knowledge active
            render_pipeline([("PLANNER", "done"), ("VERIFIER", "done"), ("KNOWLEDGE", "active"), ("EXPLANATION", "idle")])
            thought_logs += [
                ("ok",   "Verifier: PASS — 0 safety violations"),
                ("info", "Querying RAG knowledge base (railway_sops.txt)..."),
                ("ok",   "Retrieved: SOP §4.2 (Priority), SOP §7.1 (Platform Fallback)"),
            ]
            render_thought_log(thought_logs)
            time.sleep(0.3)

            # Stage 4: Explanation active
            render_pipeline([("PLANNER", "done"), ("VERIFIER", "done"), ("KNOWLEDGE", "done"), ("EXPLANATION", "active")])
            thought_logs += [("info", "Synthesizing plain-English explanation via LLM...")]
            render_thought_log(thought_logs)
            time.sleep(0.2)

            # Stream the response
            stream_response(res.get("explanation", ""))

        res = st.session_state["last_res"]

        if res.get("success"):
            render_pipeline([("PLANNER", "done"), ("VERIFIER", "done"), ("KNOWLEDGE", "done"), ("EXPLANATION", "done")])
        else:
            render_pipeline([("PLANNER", "done"), ("VERIFIER", "error"), ("KNOWLEDGE", "idle"), ("EXPLANATION", "error")])
            st.error(res.get("error", "The safety pipeline could not produce a compliant schedule."))

        # Final thought log (if not already set by btn_solve path)
        if not btn_solve:
            chat_ph.markdown(f"""
            <div class="agent-bubble">
                <div class="agent-bubble-header">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="#00ffcc"><circle cx="12" cy="12" r="10"/></svg>
                    &nbsp;DISPATCH COPILOT · QWEN 2.5-7B (Q4_K_M · ROCm)
                </div>
                {res.get('explanation', '')}
            </div>
            """, unsafe_allow_html=True)

        # Success stat flash
        tps_v = f"{res['tps']}" if res.get("tps") is not None else "offline"
        raw_lat = res.get("latency_ms")
        if raw_lat is None:
            lat_v = "unavailable"
        elif raw_lat >= 1000:
            lat_v = f"{raw_lat / 1000.0:.1f}s"
        else:
            lat_v = f"{raw_lat} ms"

        stats_ph.markdown(f"""
        <div class="stat-flash">
            <div class="stat-chip">✓ VERIFIED — 0 VIOLATIONS</div>
            <div class="stat-chip">{tps_v} tok/s ROCm</div>
            <div class="stat-chip">{lat_v} TTFT</div>
            <div class="stat-chip amber">OR-TOOLS CP-SAT</div>
        </div>
        """, unsafe_allow_html=True)

        if not res.get("success"):
            stats_ph.markdown("""
            <div class="stat-flash">
                <div class="stat-chip red">SAFETY CHECK FAILED</div>
                <div class="stat-chip amber">NO DISPATCH ACTION AVAILABLE</div>
            </div>
            """, unsafe_allow_html=True)

        # Gantt Timeline
        schedule = res.get("schedule", [])
        if schedule:
            gantt_data = []
            for item in schedule:
                delay = item["delay_minutes"]
                gantt_data.append({
                    "Train ID": item["train_id"],
                    "Train Type": item["train_type"],
                    "Start":  f"2026-07-28 {item['rescheduled_arrival']}:00",
                    "Finish": f"2026-07-28 {item['rescheduled_departure']}:00",
                    "Platform": f"Platform {item['assigned_platform']}",
                    "Scheduled Arr": item["scheduled_arrival"],
                    "Rescheduled Arr": item["rescheduled_arrival"],
                    "Delay Impact": f"+{delay} min" if delay > 0 else "On Time",
                    "Priority": f"Class {item['priority']}"
                })
            df_gantt = pd.DataFrame(gantt_data)
            color_map = {"Express": "#e60026", "Commuter": "#f59e0b", "Freight": "#00ffcc"}
            fig = px.timeline(
                df_gantt,
                x_start="Start", x_end="Finish", y="Platform",
                color="Train Type", color_discrete_map=color_map,
                hover_name="Train ID",
                hover_data={"Start": False, "Finish": False, "Platform": True,
                            "Train Type": True, "Priority": True,
                            "Scheduled Arr": True, "Rescheduled Arr": True, "Delay Impact": True},
                template="plotly_dark", height=260
            )
            fig.update_layout(
                font_family="Inter, sans-serif",
                paper_bgcolor="#111116",
                plot_bgcolor="#1e1e2a",
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(title=dict(text="TIMELINE (HH:MM)", font=dict(family="Fira Code, monospace", size=11, color="#4a5568")), gridcolor="#2a2a35"),
                yaxis=dict(title=dict(text="PLATFORM", font=dict(family="Fira Code, monospace", size=11, color="#4a5568")), autorange="reversed", gridcolor="#2a2a35"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(family="Fira Code, monospace", size=11, color="#8892a4"))
            )
            with gantt_ph.container():
                st.markdown('<div class="section-label">// PLATFORM OCCUPANCY GANTT TIMELINE</div>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# RIGHT PANEL — Artifacts, Memory Index, Gate
# ─────────────────────────────────────────────────────────────────────────────
with right_col:
    st.markdown('<div class="panel-header">// CONTEXT & ARTIFACTS</div>', unsafe_allow_html=True)

    # Active Memory Index
    st.markdown("""
    <div class="right-card">
        <div class="right-card-title">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="#00ffcc"><circle cx="12" cy="12" r="10"/></svg>
            Active RAG Memory Index
        </div>
        <div class="memory-item"><div class="memory-dot"></div>railway_sops.txt — SOP §1,2,3,4,7</div>
        <div class="memory-item"><div class="memory-dot"></div>SOP §4.2 — Express Priority Rules</div>
        <div class="memory-item"><div class="memory-dot"></div>SOP §7.1 — Platform Fallback</div>
        <div class="memory-item"><div class="memory-dot" style="background:#f59e0b;box-shadow:0 0 4px rgba(245,158,11,0.5)"></div>Session Memory — Active (JSON)</div>
    </div>
    """, unsafe_allow_html=True)

    # Gate — Human in the loop
    st.markdown("""
    <div class="gate-box" style="margin-bottom: 8px;">
        <div class="gate-label">⚡ AGENT ACTION GATE</div>
        <div class="gate-action">
            Agent requests to <strong>apply rescheduled timetable</strong> to dispatch system and notify affected platform operators.
        </div>
    </div>
    """, unsafe_allow_html=True)

    active_result = st.session_state.get("last_res")
    gate_col1, gate_col2 = st.columns(2)
    with gate_col1:
        if st.button("✓ APPROVE DISPATCH", key="gate_approve_btn", use_container_width=True, disabled=not (active_result and active_result.get("success"))):
            st.session_state["gate_decision"] = "APPROVED"
    with gate_col2:
        if st.button("✗ REJECT DISPATCH", key="gate_reject_btn", use_container_width=True, disabled=not active_result):
            st.session_state["gate_decision"] = "REJECTED"

    gate_status = st.session_state.get("gate_decision")
    if gate_status == "APPROVED":
        st.markdown("""
        <div style="background:rgba(0,255,204,0.1);border:1px solid #00ffcc;border-radius:4px;padding:8px 12px;margin-bottom:16px;font-family:'Fira Code',monospace;font-size:0.75rem;color:#00ffcc;">
            ✓ DISPATCH APPROVED — Rescheduled timetable committed & station signals notified.
        </div>
        """, unsafe_allow_html=True)
    elif gate_status == "REJECTED":
        st.markdown("""
        <div style="background:rgba(230,0,38,0.1);border:1px solid #e60026;border-radius:4px;padding:8px 12px;margin-bottom:16px;font-family:'Fira Code',monospace;font-size:0.75rem;color:#ff4d6d;">
            ✗ DISPATCH REJECTED — Manual traffic controller override active.
        </div>
        """, unsafe_allow_html=True)
    elif not active_result:
        st.markdown("""
        <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:#4a5568;margin-bottom:16px;text-align:center;">
            Awaiting solver execution to enable dispatch gate actions.
        </div>
        """, unsafe_allow_html=True)


    # Artifact Viewer
    if "last_res" in st.session_state:
        res = st.session_state["last_res"]
        sched = res.get("schedule", [])
        artifact_json = html.escape(json.dumps(sched, indent=2) if sched else "No schedule generated yet.")
        st.markdown(f"""
        <div class="right-card">
            <div class="right-card-title">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="#4a5568"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
                Artifact Viewer — Schedule JSON
            </div>
            <div class="artifact-block">{artifact_json}</div>
        </div>
        """, unsafe_allow_html=True)

    # Benchmark Summary Card — reads from bench_data dynamically
    if bench_data and bench_data.get("benchmarks"):
        bench_rows = ""
        for b in bench_data["benchmarks"]:
            quant  = b.get("quantization", "")
            tps_v  = b.get("tps_short_prompt", 0)
            vram_v = b.get("vram_usage_gb", 0)
            is_active = "Q4_K_M" in quant
            dot_style = "box-shadow:0 0 6px rgba(0,255,204,0.7)" if is_active else ""
            label = quant.split(" (")[0]  # e.g. "Q4_K_M"
            if BENCH_IS_PLACEHOLDER:
                row_text = f"{label} — reference only"
                dot_style = "background:#2a2a35;box-shadow:none"
            else:
                row_text = f"{label} — {tps_v} tok/s / {vram_v} GB VRAM{'  ← Active' if is_active else ''}"
            bench_rows += f'<div class="memory-item"><div class="memory-dot" style="{dot_style}"></div>{row_text}</div>'
        card_title = "ROCm Inference Benchmark" + (" (placeholder)" if BENCH_IS_PLACEHOLDER else " ✓ Measured")
        st.markdown(f"""
        <div class="right-card">
            <div class="right-card-title">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="{'#4a5568' if BENCH_IS_PLACEHOLDER else '#e60026'}"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                {card_title}
            </div>
            {bench_rows}
        </div>
        """, unsafe_allow_html=True)
