"""
benchmark.py — AMD Radeon ROCm Local Inference Benchmarking Tool
Runs real inference calls against Ollama endpoint and measures:
  - Tokens per second (TPS) for short prompts and RAG-length prompts
  - Latency to first token (TTFT)
  - Reports VRAM via rocm-smi
Writes results to data/benchmark_results.json for the Streamlit dashboard.

Usage (on Radeon Cloud instance with Ollama running):
    python benchmark.py
"""

import json
import os
import time
import subprocess
import requests
import re
from datetime import datetime, timezone
from pathlib import Path

OLLAMA_URL = "http://localhost:11434"
OUTPUT_FILE = Path(__file__).resolve().parent / "data" / "benchmark_results.json"

# Models to benchmark (Ollama tag format)
# Note: qwen2.5:7b-instruct default = Q4_K_M (4.7 GB)
# FP16 and Q8_0 use explicit size tags if available; benchmark gracefully
# skips models that aren't pulled.
MODELS = [
    {"quantization": "Q4_K_M (4-bit Quantized - Active)", "tag": "qwen2.5:7b-instruct"},
    {"quantization": "Q8_0 (8-bit Quantized)",            "tag": "qwen2.5:7b-instruct-q8_0"},
    {"quantization": "FP16 (Unquantized)",                "tag": "qwen2.5:7b-instruct-fp16"},
]

SHORT_PROMPT = "What is the minimum headway buffer required between consecutive trains?"

RAG_PROMPT = """
You are a railway traffic controller copilot. Using the following standard operating procedures:
SECTION 4: TRAIN PRIORITY CLASSES — Express (Class 1) takes precedence over Passenger (Class 2) on single-track bottlenecks.
SECTION 7: PLATFORM REASSIGNMENT — Platform 2 is the designated emergency fallback for Platform 1 maintenance.
Given that 12431 Vande Bharat Express is delayed by 15 minutes and 14307 PRG-BE Passenger is following on the same track,
explain the rescheduling decision in a concise professional summary for the traffic controller.
"""

def get_device_info() -> str:
    """Try to get GPU name from rocm-smi."""
    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname"],
            capture_output=True, text=True, timeout=5
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and "GPU" in l]
        if lines:
            return lines[0]
    except Exception:
        pass
    return "AMD Radeon GPU (ROCm)"

def get_vram_usage_gb(model_tag: str) -> float:
    """Query VRAM usage from rocm-smi after loading a model."""
    try:
        result = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if "Used" in line:
                # rocm-smi includes a GPU index before the byte value; use the
                # final numeric token so GPU[0] is never mistaken for usage.
                values = re.findall(r"\d+", line)
                if values:
                    return round(int(values[-1]) / (1024 * 1024 * 1024), 1)
    except Exception:
        pass
    return 0.0

def benchmark_model(model_tag: str, prompt: str, num_predict: int = 200) -> dict:
    """Run a single inference call and return TPS and TTFT metrics."""
    endpoint = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": model_tag,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": num_predict}
    }
    try:
        start = time.time()
        resp = requests.post(endpoint, json=payload, timeout=120)
        elapsed = time.time() - start

        if resp.status_code != 200:
            return {"tps": 0.0, "ttft_ms": 0}

        data = resp.json()
        eval_count = data.get("eval_count", 0)
        eval_duration_ns = data.get("eval_duration", 1)
        prompt_eval_duration_ns = data.get("prompt_eval_duration", 0)

        tps = round(eval_count / (eval_duration_ns / 1e9), 1) if eval_duration_ns > 0 else 0.0
        ttft_ms = int(prompt_eval_duration_ns / 1e6) if prompt_eval_duration_ns > 0 else int(elapsed * 1000)

        return {"tps": tps, "ttft_ms": ttft_ms}
    except Exception as e:
        print(f"  ERROR: {e}")
        return {"tps": 0.0, "ttft_ms": 0}

def run_benchmark():
    print("=" * 70)
    print("  AMD ROCm LOCAL GPU INFERENCE BENCHMARK")
    print("  Railway Ops Agentic Copilot — Track 2")
    print("=" * 70)

    device = get_device_info()
    print(f"  Device: {device}\n")

    results = []

    for m in MODELS:
        tag = m["tag"]
        quant = m["quantization"]
        print(f"\n  Benchmarking: {quant} ({tag})")

        # Warm-up pass
        print("    [1/3] Warming up model...")
        benchmark_model(tag, SHORT_PROMPT, num_predict=10)

        # Short prompt benchmark
        print("    [2/3] Short prompt benchmark...")
        short = benchmark_model(tag, SHORT_PROMPT, num_predict=200)

        # RAG-stuffed long prompt benchmark
        print("    [3/3] RAG-length prompt benchmark...")
        rag = benchmark_model(tag, RAG_PROMPT, num_predict=200)

        # VRAM check after model load
        vram_gb = get_vram_usage_gb(tag)

        result = {
            "quantization": quant,
            "vram_usage_gb": vram_gb,
            "tps_short_prompt": short["tps"],
            "tps_rag_prompt": rag["tps"],
            "ttft_ms": short["ttft_ms"],
            "status": "Active" if "Q4_K_M" in quant else "Benchmarked"
        }
        results.append(result)

        print(f"    TPS (short): {short['tps']} tok/s | TPS (RAG): {rag['tps']} tok/s | TTFT: {short['ttft_ms']} ms | VRAM: {vram_gb} GB")

    # Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "device": device,
        "model_family": "Qwen2.5-7B-Instruct",
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "benchmarks": results
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Results saved to {OUTPUT_FILE}")
    print("=" * 70)

    # Print final table
    print(f"\n{'Quantization':<35} | {'VRAM':<8} | {'Short TPS':<10} | {'RAG TPS':<10} | {'TTFT (ms)'}")
    print("-" * 75)
    for r in results:
        print(f"{r['quantization']:<35} | {r['vram_usage_gb']:<8} | {r['tps_short_prompt']:<10} | {r['tps_rag_prompt']:<10} | {r['ttft_ms']}")

if __name__ == "__main__":
    run_benchmark()
