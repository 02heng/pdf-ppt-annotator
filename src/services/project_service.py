"""工程与会话持久化"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.ui.app import App, AnnotationMarker

PROJECT_VERSION = 1
PROJECT_EXT = ".topdf"
SESSION_FILENAME = "session.json"


def get_user_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.path.expanduser("~/.local/share")
    path = Path(base) / "TO PDF"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_session_path() -> Path:
    return get_user_data_dir() / SESSION_FILENAME


def _marker_to_dict(marker: "AnnotationMarker") -> Dict[str, Any]:
    return {
        "x": marker.x,
        "y": marker.y,
        "text": marker.text,
        "color": marker.color,
    }


def _dict_to_marker(data: Dict[str, Any]) -> "AnnotationMarker":
    from src.ui.app import AnnotationMarker

    return AnnotationMarker(
        x=int(data.get("x", 0)),
        y=int(data.get("y", 0)),
        text=str(data.get("text", "")),
        color=str(data.get("color", "#FF6B6B")),
    )


def _annotations_to_json(annotations_by_file: Dict[str, Dict[int, List["AnnotationMarker"]]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    result: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for file_path, pages in annotations_by_file.items():
        page_map: Dict[str, List[Dict[str, Any]]] = {}
        for page_num, markers in pages.items():
            page_map[str(page_num)] = [_marker_to_dict(m) for m in markers]
        result[file_path] = page_map
    return result


def _annotations_from_json(data: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> Dict[str, Dict[int, List["AnnotationMarker"]]]:
    result: Dict[str, Dict[int, List["AnnotationMarker"]]] = {}
    for file_path, pages in data.items():
        page_map: Dict[int, List["AnnotationMarker"]] = {}
        for page_key, markers in pages.items():
            page_map[int(page_key)] = [_dict_to_marker(item) for item in markers]
        result[file_path] = page_map
    return result


def build_snapshot(app: "App") -> Dict[str, Any]:
    app._persist_current_file_annotations()
    existing_files = [f for f in app.selected_files if os.path.isfile(f)]
    annotations = _annotations_to_json(app.annotations_by_file)
    filtered_annotations = {
        path: pages for path, pages in annotations.items() if path in existing_files
    }

    return {
        "version": PROJECT_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "files": existing_files,
        "current_file_index": app.current_file_index,
        "current_page": app.current_page,
        "zoom_level": app.zoom_level,
        "annotations_by_file": filtered_annotations,
        "project_path": app.project_file_path or "",
    }


def save_session(app: "App") -> None:
    if not app.settings.app.auto_save:
        return
    if not app.selected_files and not app.annotations_by_file:
        return

    snapshot = build_snapshot(app)
    session_path = get_session_path()
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)


def load_session() -> Optional[Dict[str, Any]]:
    session_path = get_session_path()
    if not session_path.is_file():
        return None
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") != PROJECT_VERSION:
            return None
        return data
    except (OSError, json.JSONDecodeError):
        return None


def apply_snapshot(app: "App", data: Dict[str, Any], *, project_root: str = "") -> bool:
    files = data.get("files") or []
    valid_files: List[str] = []

    for entry in files:
        if project_root and not os.path.isabs(entry):
            path = os.path.normpath(os.path.join(project_root, entry))
        else:
            path = os.path.normpath(entry)
        if os.path.isfile(path):
            valid_files.append(path)

    if not valid_files:
        return False

    annotations_data = data.get("annotations_by_file") or {}
    remapped_annotations: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    if project_root:
        for old_key, pages in annotations_data.items():
            if os.path.isabs(old_key):
                name = os.path.basename(old_key)
                match = next((f for f in valid_files if os.path.basename(f) == name), None)
                key = match or old_key
            else:
                key = os.path.normpath(os.path.join(project_root, old_key))
            remapped_annotations[key] = pages
        annotations_data = remapped_annotations
    else:
        remapped_annotations = {}
        for old_key, pages in annotations_data.items():
            if old_key in valid_files:
                remapped_annotations[old_key] = pages
            elif os.path.basename(old_key):
                match = next(
                    (f for f in valid_files if os.path.basename(f) == os.path.basename(old_key)),
                    None,
                )
                if match:
                    remapped_annotations[match] = pages
        annotations_data = remapped_annotations

    app.selected_files = valid_files
    app.annotations_by_file = _annotations_from_json(annotations_data)

    index = data.get("current_file_index", 0)
    app.current_file_index = max(0, min(index, len(valid_files) - 1))
    app.current_page = max(0, int(data.get("current_page", 0)))
    app.zoom_level = float(data.get("zoom_level", 1.0))
    app.project_file_path = data.get("project_path") or None

    file_path = valid_files[app.current_file_index]
    app.update_file_list(valid_files)
    app._load_file_content(file_path, page=app.current_page)
    app._restore_file_annotations(file_path)
    app._render_page()
    app._update_annotation_list()
    app.sync_web_preview()

    saved_at = data.get("saved_at", "")
    app.update_status(f"已恢复工程（{len(valid_files)} 个文件）")
    return True


def restore_session(app: "App") -> bool:
    data = load_session()
    if not data:
        return False
    return apply_snapshot(app, data)


def save_project(app: "App", project_path: str) -> None:
    project_path = os.path.abspath(project_path)
    if not project_path.lower().endswith(PROJECT_EXT):
        project_path += PROJECT_EXT

    app._persist_current_file_annotations()

    temp_dir = tempfile.mkdtemp(prefix="topdf_project_")
    try:
        assets_dir = os.path.join(temp_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        relative_files: List[str] = []
        path_map: Dict[str, str] = {}

        for i, src in enumerate(app.selected_files):
            if not os.path.isfile(src):
                continue
            base_name = os.path.basename(src)
            dest_rel = f"assets/{i}_{base_name}"
            dest_abs = os.path.join(temp_dir, dest_rel.replace("/", os.sep))
            shutil.copy2(src, dest_abs)
            relative_files.append(dest_rel.replace("\\", "/"))
            path_map[src] = dest_rel.replace("\\", "/")

        remapped: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for abs_path, pages in _annotations_to_json(app.annotations_by_file).items():
            rel_file = path_map.get(abs_path)
            if rel_file:
                remapped[rel_file] = pages

        manifest = {
            "version": PROJECT_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "files": relative_files,
            "current_file_index": app.current_file_index,
            "current_page": app.current_page,
            "zoom_level": app.zoom_level,
            "annotations_by_file": remapped,
            "project_path": project_path,
        }

        manifest_path = os.path.join(temp_dir, "project.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        with zipfile.ZipFile(project_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(temp_dir):
                for name in files:
                    full_path = os.path.join(root, name)
                    arcname = os.path.relpath(full_path, temp_dir).replace("\\", "/")
                    zf.write(full_path, arcname)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    app.project_file_path = project_path


def load_project(app: "App", project_path: str) -> None:
    project_path = os.path.abspath(project_path)
    extract_dir = os.path.splitext(project_path)[0] + "_data"
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(project_path, "r") as zf:
        zf.extractall(extract_dir)

    manifest_path = os.path.join(extract_dir, "project.json")
    if not os.path.isfile(manifest_path):
        raise ValueError("工程文件无效：缺少 project.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["project_path"] = project_path
    if not apply_snapshot(app, data, project_root=extract_dir):
        raise ValueError("工程文件中没有可用的 PDF")
