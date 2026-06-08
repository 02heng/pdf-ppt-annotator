"""PDF.js 悬停批注预览本地服务"""
import json
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.utils.file_utils import file_key
from src.utils.preview_ink_store import ink_pages_from_json, ink_pages_to_json
from src.utils.runtime import get_web_dir

if TYPE_CHECKING:
    from src.ui.app import App

DEFAULT_PORT = 8765


@dataclass
class WebPreviewState:
    pdf_path: str = ""
    source_file_key: str = ""
    current_page: int = 0
    total_pages: int = 0
    zoom_level: float = 1.0
    annotations: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    ink_pages: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


class WebPreviewServer:
    """本地 HTTP 服务，供 PDF.js 前端读取 PDF 与批注数据"""

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.state = WebPreviewState()
        self._thread: Optional[threading.Thread] = None
        self._app: Optional["App"] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        from flask import Flask, jsonify, request, send_file, send_from_directory

        web_dir = str(get_web_dir())
        flask_app = Flask(__name__, static_folder=web_dir, static_url_path="")
        server = self

        @flask_app.get("/")
        def index():
            return send_from_directory(web_dir, "index.html")

        @flask_app.get("/api/state")
        def api_state():
            return jsonify(server._build_state())

        @flask_app.get("/api/pdf")
        def api_pdf():
            path = server.state.pdf_path
            if not path or not os.path.isfile(path):
                return jsonify({"error": "no pdf"}), 404
            response = send_file(path, mimetype="application/pdf")
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            return response

        @flask_app.get("/api/annotations")
        def api_annotations():
            return jsonify(
                {
                    "pages": server.state.annotations,
                    "current_page": server.state.current_page,
                    "zoom_level": server.state.zoom_level,
                }
            )

        @flask_app.get("/api/ink")
        def api_ink_get():
            return jsonify({"pages": server.state.ink_pages})

        @flask_app.put("/api/ink")
        def api_ink_put():
            body = request.get_json(silent=True) or {}
            pages = ink_pages_from_json(body.get("pages") or {})
            server.state.ink_pages = ink_pages_to_json(pages)
            desktop = server._app
            if desktop and server.state.source_file_key:
                desktop.preview_ink_by_file[server.state.source_file_key] = pages
                desktop.schedule_persist()
            return jsonify({"ok": True, "pages": server.state.ink_pages})

        @flask_app.post("/api/ink/save")
        def api_ink_save():
            desktop = server._app
            if not desktop:
                return jsonify({"error": "桌面应用未就绪"}), 503
            body = request.get_json(silent=True) or {}
            pages = ink_pages_from_json(body.get("pages") or server.state.ink_pages)
            if server.state.source_file_key:
                desktop.preview_ink_by_file[server.state.source_file_key] = pages
                server.state.ink_pages = ink_pages_to_json(pages)
            overwrite = bool(body.get("overwrite", False))
            try:
                out_path = desktop.save_preview_ink_to_document(overwrite=overwrite)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            except OSError as exc:
                return jsonify({"error": str(exc)}), 500
            except Exception as exc:
                return jsonify({"error": str(exc)}), 500
            return jsonify({"ok": True, "path": out_path})

        def run():
            flask_app.run(host="127.0.0.1", port=server.port, threaded=True, use_reloader=False)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"

    def _build_state(self) -> Dict[str, Any]:
        pdf_token = ""
        if self.state.pdf_path and os.path.isfile(self.state.pdf_path):
            pdf_token = f"{self.state.pdf_path}:{os.path.getmtime(self.state.pdf_path)}"

        return {
            "pdf_available": bool(pdf_token),
            "pdf_token": pdf_token,
            "current_page": self.state.current_page,
            "total_pages": self.state.total_pages,
            "zoom_level": self.state.zoom_level,
            "annotations": self.state.annotations,
            "ink_pages": self.state.ink_pages,
        }

    def update_from_app(self, app: "App") -> None:
        """从主应用同步 PDF 与批注"""
        self._app = app
        pdf_path = ""
        source_key = ""
        if app.selected_files and 0 <= app.current_file_index < len(app.selected_files):
            source = app.selected_files[app.current_file_index]
            pdf_path = app.get_render_pdf_path(source)
            source_key = file_key(source)

        pages: Dict[str, List[Dict[str, Any]]] = {}

        for page_num, markers in app.annotations.items():
            page_items = []
            for i, marker in enumerate(markers):
                item = {
                    "index": i + 1,
                    "x": marker.x,
                    "y": marker.y,
                    "text": marker.text,
                    "color": marker.color,
                }
                if getattr(marker, "display_mode", "marker") == "inline":
                    item["display_mode"] = "inline"
                    item["placement"] = getattr(marker, "placement", "right")
                    item["box_width"] = getattr(marker, "box_width", 0)
                    item["box_height"] = getattr(marker, "box_height", 0)
                    from src.utils.block_font_size import (
                        GENERATED_INLINE_FONT_PT,
                        DEFAULT_FONT_PT,
                    )

                    if (getattr(marker, "original_text", "") or "").strip():
                        item["font_size"] = GENERATED_INLINE_FONT_PT
                    else:
                        item["font_size"] = getattr(
                            marker, "font_size", DEFAULT_FONT_PT
                        )
                    orient = getattr(marker, "text_orientation", "horizontal") or "horizontal"
                    if orient != "horizontal":
                        item["text_orientation"] = orient
                page_items.append(item)
            pages[str(page_num)] = page_items

        ink_pages: Dict[int, List[Dict[str, Any]]] = {}
        if source_key:
            ink_pages = dict(app.preview_ink_by_file.get(source_key, {}))

        self.state.pdf_path = pdf_path
        self.state.source_file_key = source_key
        self.state.current_page = app.current_page
        self.state.total_pages = app.total_pages
        self.state.zoom_level = app.zoom_level
        self.state.annotations = pages
        self.state.ink_pages = ink_pages_to_json(ink_pages)


def markers_to_json(app) -> str:
    """批注转 JSON 字符串"""
    server = WebPreviewServer()
    server.update_from_app(app)
    return json.dumps(server.state.annotations, ensure_ascii=False, indent=2)
