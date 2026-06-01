"""CustomTkinter 兼容性修复"""


def apply_ctk_patches() -> None:
    """修复 CTkScrollableFrame 在 Windows 上滚轮崩溃的问题"""
    try:
        import customtkinter.windows.widgets.ctk_scrollable_frame as ctk_sf

        original = ctk_sf.CTkScrollableFrame.check_if_master_is_canvas

        def safe_check_if_master_is_canvas(self, widget):
            if not hasattr(widget, "master"):
                return False
            return original(self, widget)

        ctk_sf.CTkScrollableFrame.check_if_master_is_canvas = safe_check_if_master_is_canvas
    except Exception:
        pass
