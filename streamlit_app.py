"""Streamlit Cloud launcher for Pixelle-Video v0.1.15."""

from __future__ import annotations

import json
import os
import runpy
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import yaml

SOURCE_URL = "https://github.com/AIDC-AI/Pixelle-Video/archive/refs/tags/v0.1.15.zip"
APP_DIR = Path(__file__).resolve().parent
CACHE_DIR = APP_DIR / ".pixelle_source"
SOURCE_ROOT = CACHE_DIR / "Pixelle-Video-0.1.15"


def _download_source() -> None:
    if (SOURCE_ROOT / "web" / "app.py").exists():
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = CACHE_DIR / "pixelle-video-v0.1.15.zip"
    if not archive_path.exists():
        urllib.request.urlretrieve(SOURCE_URL, archive_path)

    extract_tmp = CACHE_DIR / "extracting"
    if extract_tmp.exists():
        shutil.rmtree(extract_tmp)
    extract_tmp.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as zf:
        zf.extractall(extract_tmp)

    extracted_roots = [p for p in extract_tmp.iterdir() if p.is_dir()]
    if not extracted_roots:
        raise RuntimeError("Pixelle-Video source archive did not contain a source directory")

    if SOURCE_ROOT.exists():
        shutil.rmtree(SOURCE_ROOT)
    extracted_roots[0].rename(SOURCE_ROOT)
    shutil.rmtree(extract_tmp)


def _streamlit_secrets() -> dict:
    try:
        import streamlit as st

        return {
            key: dict(value) if hasattr(value, "items") else value
            for key, value in st.secrets.items()
        }
    except Exception:
        return {}


def _write_config() -> None:
    secrets = _streamlit_secrets()
    llm = dict(secrets.get("llm", {}))
    comfyui = dict(secrets.get("comfyui", {}))

    llm.setdefault("api_key", os.getenv("PIXELLE_LLM_API_KEY") or os.getenv("OPENAI_API_KEY", ""))
    llm.setdefault("base_url", os.getenv("PIXELLE_LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    llm.setdefault("model", os.getenv("PIXELLE_LLM_MODEL") or os.getenv("OPENAI_MODEL", ""))

    comfyui.setdefault("comfyui_url", os.getenv("PIXELLE_COMFYUI_URL", "http://127.0.0.1:8188"))
    comfyui.setdefault("comfyui_api_key", os.getenv("PIXELLE_COMFYUI_API_KEY", ""))
    comfyui.setdefault("runninghub_api_key", os.getenv("PIXELLE_RUNNINGHUB_API_KEY", ""))
    comfyui.setdefault("runninghub_concurrent_limit", int(os.getenv("PIXELLE_RUNNINGHUB_CONCURRENT_LIMIT", "1")))
    comfyui.setdefault("runninghub_instance_type", os.getenv("PIXELLE_RUNNINGHUB_INSTANCE_TYPE", ""))
    comfyui.setdefault("tts", {
        "inference_mode": "local",
        "local": {"voice": "zh-CN-YunjianNeural", "speed": 1.2},
        "comfyui": {"default_workflow": None},
    })
    comfyui.setdefault("image", {
        "default_workflow": "runninghub/image_flux.json",
        "prompt_prefix": "Minimalist black-and-white matchstick figure style illustration, clean lines, simple sketch style",
    })
    comfyui.setdefault("video", {
        "default_workflow": "runninghub/video_wan2.1_fusionx.json",
        "prompt_prefix": "Minimalist black-and-white matchstick figure style illustration, clean lines, simple sketch style",
    })

    config = {
        "project_name": "Pixelle-Video",
        "llm": llm,
        "comfyui": comfyui,
        "template": {"default_template": "1080x1920/image_default.html"},
    }
    with (SOURCE_ROOT / "config.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)


def _patch_streamlit_page_paths() -> None:
    """Make st.Page paths resolvable from this launcher entrypoint."""
    app_path = SOURCE_ROOT / "web" / "app.py"
    source = app_path.read_text(encoding="utf-8")

    for page_path in (SOURCE_ROOT / "web" / "pages").glob("*.py"):
        relative_literal = json.dumps(f"pages/{page_path.name}", ensure_ascii=False)
        absolute_literal = json.dumps(str(page_path), ensure_ascii=False)
        source = source.replace(relative_literal, absolute_literal)

    app_path.write_text(source, encoding="utf-8")


def main() -> None:
    _download_source()
    _write_config()
    _patch_streamlit_page_paths()
    os.environ.setdefault("PIXELLE_VIDEO_ROOT", str(SOURCE_ROOT))
    os.environ.setdefault("BROWSER_EXECUTABLE_PATH", "/usr/bin/chromium")
    os.environ.setdefault("CHROME_BIN", "/usr/bin/chromium")

    os.chdir(SOURCE_ROOT)
    sys.path.insert(0, str(SOURCE_ROOT))
    runpy.run_path(str(SOURCE_ROOT / "web" / "app.py"), run_name="__main__")


if __name__ == "__main__":
    main()
