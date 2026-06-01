"""PDF.js 悬停批注预览本地服务"""
import json
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
DEFAULT_PORT = 8765


@dataclass
class WebPreviewState:
    pdf_path: str = ""
    current_page: int = 0
    total_pages: int = 0
    zoom_level: float = 1.0
    annotations: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


class WebPreviewServer:
    """本地 HTTP 服务，供 PDF.js 前端读取 PDF 与批注数据"""

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.state = WebPreviewState()
        self._thread: Optional[threading.Thread] = None
        self._app = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        from flask import Flask, jsonify, send_file, send_from_directory

        app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")
        self._app = app

        @app.get("/")
        def index():
            return send_from_directory(WEB_DIR, "index.html")

        @app.get("/api/state")
        def api_state():
            return jsonify(self._build_state())

        @app.get("/api/pdf")
        def api_pdf():
            path = self.state.pdf_path
            if not path or not os.path.isfile(path):
                return jsonify({"error": "no pdf"}), 404
            return send_file(path, mimetype="application/pdf")

        @app.get("/api/annotations")
        def api_annotations():
            return jsonify(
                {
                    "pages": self.state.annotations,
                    "current_page": self.state.current_page,
                    "zoom_level": self.state.zoom_level,
                }
            )

        def run():
            app.run(host="127.0.0.1", port=self.port, threaded=True, use_reloader=False)

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
        }

    def update_from_app(self, app) -> None:
        """从主应用同步 PDF 与批注"""
        pdf_path = ""
        if app.selected_files and 0 <= app.current_file_index < len(app.selected_files):
            pdf_path = app.selected_files[app.current_file_index]

        pages: Dict[str, List[Dict[str, Any]]] = {}
        scale = app.zoom_level * 2

        for page_num, markers in app.annotations.items():
            page_items = []
            for i, marker in enumerate(markers):
                page_items.append(
                    {
                        "index": i + 1,
                        "x": marker.x / scale,
                        "y": marker.y / scale,
                        "text": marker.text,
                        "color": marker.color,
                    }
                )
            pages[str(page_num)] = page_items

        self.state.pdf_path = pdf_path
        self.state.current_page = app.current_page
        self.state.total_pages = app.total_pages
        self.state.zoom_level = app.zoom_level
        self.state.annotations = pages


def markers_to_json(app) -> str:
    """批注转 JSON 字符串"""
    server = WebPreviewServer()
    server.update_from_app(app)
    return json.dumps(server.state.annotations, ensure_ascii=False, indent=2)
