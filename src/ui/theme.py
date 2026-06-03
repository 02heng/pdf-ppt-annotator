"""应用设计系统：紫白渐变、间距、圆角、字体（CustomTkinter + Web）"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


class UITheme:
    # —— 色板 ——
    BG = "#F4F0FA"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#FAF8FF"
    SURFACE_ELEVATED = "#FFFFFF"
    BORDER = "#E8E0F5"
    BORDER_FOCUS = "#C4B5FD"

    PURPLE_950 = "#4C1D95"
    PURPLE_900 = "#5B21B6"
    PURPLE_800 = "#6D28D9"
    PURPLE_700 = "#7C3AED"
    PURPLE_600 = "#8B5CF6"
    PURPLE_500 = "#A78BFA"
    PURPLE_400 = "#C4B5FD"
    PURPLE_200 = "#DDD6FE"
    PURPLE_100 = "#EDE9FE"
    PURPLE_50 = "#F5F3FF"

    GRADIENT_START = "#A78BFA"
    GRADIENT_END = "#5B21B6"

    TEXT = "#1E1633"
    TEXT_SECONDARY = "#4A3F63"
    TEXT_MUTED = "#7C7194"
    TEXT_ON_PURPLE = "#FFFFFF"

    # 品牌主色（与顶栏一致）
    BRAND = "#6F32C9"
    BRAND_HOVER = "#5B2AB5"
    ACCENT = BRAND
    ACCENT_HOVER = BRAND_HOVER

    SUCCESS = "#059669"
    SUCCESS_HOVER = "#047857"

    DANGER = PURPLE_900
    DANGER_HOVER = PURPLE_950
    DANGER_SOFT_BG = PURPLE_50
    DANGER_SOFT_BORDER = PURPLE_400

    TOOLBAR_BTN = "#FFFFFF"
    TOOLBAR_BTN_HOVER = "#F5F3FF"
    TOOLBAR_BTN_TEXT = "#5B21B6"
    TOOLBAR_BTN_BORDER = "#DDD6FE"
    TOOLBAR_BTN_GHOST = "#6D28D9"
    TOOLBAR_BTN_GHOST_HOVER = "#7C3AED"
    TOOLBAR_BTN_OUTLINE = "#EDE9FE"
    TOOLBAR_DIVIDER = "#9F7AEA"

    # 滚动条（淡紫圆角，全局统一）
    SCROLLBAR_FG = PURPLE_100
    SCROLLBAR_BUTTON = PURPLE_400
    SCROLLBAR_BUTTON_HOVER = PURPLE_500
    SCROLLBAR_CORNER_RADIUS = 10
    SCROLLBAR_WIDTH = 12

    FILE_LIST_BG = PURPLE_50

    # 批注
    MARKER_FILL = "#EDE9FE"
    MARKER_OUTLINE_DEFAULT = "#7C3AED"
    POPUP_BG = "#FFFFFF"
    POPUP_SHADOW = "#DDD6FE"
    POPUP_TEXT = "#1E1633"

    ANNOTATION_COLOR_DEFAULT = "#7C3AED"

    ANNOTATION_COLORS = [
        "#7C3AED",
        "#8B5CF6",
        "#EC4899",
        "#06B6D4",
        "#10B981",
        "#F59E0B",
        "#000000",
        "#FFFFFF",
        "#78350F",
        "#2563EB",
    ]

    # —— 布局 ——
    PAD = 14
    PAD_SM = 8
    PAD_LG = 18
    RADIUS = 10
    RADIUS_LG = 14
    RADIUS_SM = 6
    BTN_HEIGHT = 36
    BTN_HEIGHT_SM = 32

    FONT_FAMILY = "Microsoft YaHei UI"

    @classmethod
    def font_title(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=15, weight="bold")

    @classmethod
    def font_section(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=13, weight="bold")

    @classmethod
    def font_body(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=12)

    @classmethod
    def font_caption(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=11)

    @classmethod
    def font_toolbar_brand(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.FONT_FAMILY, size=16, weight="bold")

    @classmethod
    def install(cls) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

    @classmethod
    def _btn_defaults(cls, btn: ctk.CTkButton) -> None:
        btn.configure(
            height=cls.BTN_HEIGHT,
            corner_radius=cls.RADIUS,
            font=cls.font_body(),
        )

    @classmethod
    def style_card(cls, frame: ctk.CTkFrame, *, elevated: bool = True) -> None:
        frame.configure(
            fg_color=cls.SURFACE_ELEVATED if elevated else cls.SURFACE_ALT,
            border_color=cls.BORDER,
            border_width=1,
            corner_radius=cls.RADIUS_LG,
        )

    @classmethod
    def style_primary(cls, btn: ctk.CTkButton) -> None:
        cls._btn_defaults(btn)
        btn.configure(
            fg_color=cls.ACCENT,
            hover_color=cls.ACCENT_HOVER,
            text_color=cls.TEXT_ON_PURPLE,
            border_width=0,
        )

    @classmethod
    def style_secondary(cls, btn: ctk.CTkButton) -> None:
        cls._btn_defaults(btn)
        btn.configure(
            fg_color=cls.SURFACE,
            hover_color=cls.PURPLE_50,
            text_color=cls.PURPLE_800,
            border_color=cls.BORDER,
            border_width=1,
        )

    @classmethod
    def style_ghost(cls, btn: ctk.CTkButton) -> None:
        cls._btn_defaults(btn)
        btn.configure(
            fg_color="transparent",
            hover_color=cls.PURPLE_100,
            text_color=cls.PURPLE_800,
            border_width=0,
        )

    @classmethod
    def style_soft_danger(cls, btn: ctk.CTkButton) -> None:
        """删除类按钮：浅紫底 + 深紫字，与品牌色一致（不用粉红/纯蓝）。"""
        cls._btn_defaults(btn)
        btn.configure(
            height=cls.BTN_HEIGHT_SM,
            fg_color=cls.PURPLE_100,
            hover_color=cls.PURPLE_200,
            text_color=cls.PURPLE_900,
            border_color=cls.PURPLE_400,
            border_width=1,
        )

    @classmethod
    def style_icon_dismiss(cls, btn: ctk.CTkButton) -> None:
        cls._btn_defaults(btn)
        btn.configure(
            height=28,
            width=30,
            corner_radius=cls.RADIUS_SM,
            fg_color=cls.PURPLE_100,
            hover_color=cls.PURPLE_200,
            text_color=cls.PURPLE_800,
            border_width=0,
        )

    @classmethod
    def style_option_menu(cls, menu: ctk.CTkOptionMenu) -> None:
        menu.configure(
            height=cls.BTN_HEIGHT_SM,
            corner_radius=cls.RADIUS_SM,
            font=cls.font_caption(),
            fg_color=cls.ACCENT,
            button_color=cls.ACCENT_HOVER,
            button_hover_color=cls.PURPLE_900,
            dropdown_fg_color=cls.SURFACE,
            dropdown_hover_color=cls.PURPLE_50,
            dropdown_text_color=cls.TEXT,
            text_color=cls.TEXT_ON_PURPLE,
        )

    @classmethod
    def style_combo(cls, combo: ctk.CTkComboBox) -> None:
        combo.configure(
            height=cls.BTN_HEIGHT_SM,
            corner_radius=cls.RADIUS_SM,
            font=cls.font_caption(),
            fg_color=cls.SURFACE,
            border_color=cls.BORDER,
            border_width=1,
            button_color=cls.ACCENT,
            button_hover_color=cls.ACCENT_HOVER,
            dropdown_fg_color=cls.SURFACE,
            dropdown_hover_color=cls.PURPLE_50,
            dropdown_text_color=cls.TEXT,
            text_color=cls.TEXT,
        )

    @classmethod
    def style_success(cls, btn: ctk.CTkButton) -> None:
        cls._btn_defaults(btn)
        btn.configure(
            fg_color=cls.SUCCESS,
            hover_color=cls.SUCCESS_HOVER,
            text_color=cls.TEXT_ON_PURPLE,
            border_width=0,
        )

    @classmethod
    def style_danger(cls, btn: ctk.CTkButton) -> None:
        cls.style_soft_danger(btn)

    @classmethod
    def style_toolbar_brand(cls, label: ctk.CTkLabel) -> None:
        label.configure(
            text_color=cls.TEXT_ON_PURPLE,
            font=cls.font_toolbar_brand(),
        )

    @classmethod
    def style_toolbar_button(cls, btn: ctk.CTkButton, *, primary: bool = False) -> None:
        cls._btn_defaults(btn)
        if primary:
            btn.configure(
                fg_color=cls.TOOLBAR_BTN,
                hover_color=cls.TOOLBAR_BTN_HOVER,
                text_color=cls.TOOLBAR_BTN_TEXT,
                border_color=cls.TOOLBAR_BTN_BORDER,
                border_width=1,
            )
        else:
            btn.configure(
                fg_color=cls.TOOLBAR_BTN_GHOST,
                hover_color=cls.TOOLBAR_BTN_GHOST_HOVER,
                text_color=cls.TEXT_ON_PURPLE,
                border_color=cls.TOOLBAR_BTN_OUTLINE,
                border_width=1,
            )

    @classmethod
    def style_toolbar_divider(cls, frame: ctk.CTkFrame) -> None:
        frame.configure(fg_color=cls.TOOLBAR_DIVIDER, width=1, corner_radius=0)

    @classmethod
    def style_segmented(cls, seg: ctk.CTkSegmentedButton) -> None:
        """顶栏等深紫底：选中白底 + 深紫字，未选中紫底 + 白字"""
        seg.configure(
            height=cls.BTN_HEIGHT_SM,
            corner_radius=cls.RADIUS,
            font=cls.font_caption(),
            fg_color=cls.PURPLE_900,
            selected_color=cls.TOOLBAR_BTN,
            selected_hover_color=cls.TOOLBAR_BTN_HOVER,
            unselected_color=cls.PURPLE_800,
            unselected_hover_color=cls.PURPLE_700,
            text_color=cls.TOOLBAR_BTN_TEXT,
            text_color_disabled=cls.PURPLE_400,
        )

    @classmethod
    def style_segmented_panel(cls, seg: ctk.CTkSegmentedButton) -> None:
        """侧栏/设置页：选中品牌紫 + 白字，未选中浅紫底 + 深紫字"""
        seg.configure(
            height=cls.BTN_HEIGHT_SM,
            corner_radius=cls.RADIUS,
            font=cls.font_body(),
            fg_color=cls.PURPLE_100,
            selected_color=cls.ACCENT,
            selected_hover_color=cls.ACCENT_HOVER,
            unselected_color=cls.SURFACE,
            unselected_hover_color=cls.PURPLE_50,
            text_color=cls.TEXT,
            text_color_disabled=cls.TEXT_MUTED,
        )

    @classmethod
    def style_entry(cls, entry: ctk.CTkEntry) -> None:
        entry.configure(
            height=cls.BTN_HEIGHT_SM,
            corner_radius=cls.RADIUS_SM,
            font=cls.font_caption(),
            fg_color=cls.SURFACE,
            border_color=cls.BORDER,
            text_color=cls.TEXT,
        )

    @classmethod
    def style_tabview(cls, tabview: ctk.CTkTabview) -> None:
        tabview.configure(
            fg_color=cls.SURFACE,
            segmented_button_fg_color=cls.PURPLE_100,
            segmented_button_selected_color=cls.PURPLE_700,
            segmented_button_selected_hover_color=cls.PURPLE_800,
            segmented_button_unselected_color=cls.SURFACE_ALT,
            segmented_button_unselected_hover_color=cls.PURPLE_50,
            text_color=cls.TEXT,
        )

    @classmethod
    def truncate_filename(cls, name: str, max_chars: int = 32) -> str:
        if len(name) <= max_chars:
            return name
        return name[: max_chars - 1] + "…"

    @classmethod
    def bind_tooltip(cls, widget, text: str) -> None:
        """悬停显示完整文本（用于被截断的文件名等）"""
        if not text:
            return
        tip = {"win": None}

        def show(event) -> None:
            if tip["win"]:
                return
            tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_attributes("-topmost", True)
            tk.Label(
                tw,
                text=text,
                justify="left",
                bg=cls.PURPLE_900,
                fg=cls.TEXT_ON_PURPLE,
                font=(cls.FONT_FAMILY, 10),
                padx=10,
                pady=6,
            ).pack()
            tw.wm_geometry(f"+{event.x_root + 14}+{event.y_root + 14}")
            tip["win"] = tw

        def hide(_event=None) -> None:
            if tip["win"]:
                tip["win"].destroy()
                tip["win"] = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)
        widget.bind("<ButtonPress>", hide)

    @classmethod
    def scrollable_frame_kwargs(cls) -> dict:
        return {
            "scrollbar_fg_color": cls.SCROLLBAR_FG,
            "scrollbar_button_color": cls.SCROLLBAR_BUTTON,
            "scrollbar_button_hover_color": cls.SCROLLBAR_BUTTON_HOVER,
        }

    @classmethod
    def style_scrollbar(cls, sb: ctk.CTkScrollbar) -> None:
        orient = str(sb.cget("orientation")).lower()
        opts = {
            "fg_color": cls.SCROLLBAR_FG,
            "button_color": cls.SCROLLBAR_BUTTON,
            "button_hover_color": cls.SCROLLBAR_BUTTON_HOVER,
            "corner_radius": cls.SCROLLBAR_CORNER_RADIUS,
        }
        if orient == "vertical":
            opts["width"] = cls.SCROLLBAR_WIDTH
        else:
            opts["height"] = cls.SCROLLBAR_WIDTH
        sb.configure(**opts)

    @classmethod
    def style_scrollable_frame(cls, frame: ctk.CTkScrollableFrame) -> None:
        frame.configure(**cls.scrollable_frame_kwargs())
        sb = getattr(frame, "_scrollbar", None)
        if sb is not None:
            cls.style_scrollbar(sb)

    @classmethod
    def style_textbox(cls, box: ctk.CTkTextbox) -> None:
        box.configure(
            font=cls.font_body(),
            fg_color=cls.SURFACE,
            text_color=cls.TEXT,
            border_color=cls.BORDER,
            border_width=1,
            corner_radius=cls.RADIUS,
            scrollbar_button_color=cls.SCROLLBAR_BUTTON,
            scrollbar_button_hover_color=cls.SCROLLBAR_BUTTON_HOVER,
        )
        for attr in ("_x_scrollbar", "_y_scrollbar"):
            sb = getattr(box, attr, None)
            if sb is not None:
                cls.style_scrollbar(sb)

    @classmethod
    def style_nav_bar(cls, frame: ctk.CTkFrame) -> None:
        frame.configure(
            fg_color=cls.SURFACE,
            border_color=cls.BORDER,
            border_width=1,
            corner_radius=cls.RADIUS_LG,
        )

    @classmethod
    def style_nav_button(cls, btn: ctk.CTkButton) -> None:
        cls._btn_defaults(btn)
        btn.configure(
            height=cls.BTN_HEIGHT_SM,
            fg_color=cls.PURPLE_100,
            hover_color=cls.PURPLE_200,
            text_color=cls.PURPLE_800,
            border_width=0,
        )

    @classmethod
    def annotation_color_swatch_params(cls, hex_color: str) -> dict:
        """批注颜色圆钮参数（白色需描边以便在浅底上可见）。"""
        params = {"fg_color": hex_color, "hover_color": hex_color}
        if (hex_color or "").strip().upper() in ("#FFFFFF", "#FFF"):
            params["border_width"] = 1
            params["border_color"] = cls.BORDER
        return params

    @classmethod
    def style_annotation_row(cls, frame: ctk.CTkFrame, *, selected: bool = False) -> None:
        frame.configure(
            fg_color=cls.PURPLE_100 if selected else cls.SURFACE_ALT,
            border_color=cls.BORDER_FOCUS if selected else cls.BORDER,
            border_width=1,
            corner_radius=cls.RADIUS,
        )

    @classmethod
    def apply_root(cls, window: ctk.CTk) -> None:
        window.configure(fg_color=cls.BG)

    @classmethod
    def muted_label(cls, label: ctk.CTkLabel) -> None:
        label.configure(text_color=cls.TEXT_MUTED, font=cls.font_caption())

    @classmethod
    def title_label(cls, label: ctk.CTkLabel) -> None:
        label.configure(text_color=cls.TEXT, font=cls.font_section())

    @classmethod
    def style_status_bar(cls, frame: ctk.CTkFrame) -> None:
        frame.configure(
            fg_color=cls.SURFACE,
            border_color=cls.BORDER,
            border_width=1,
            corner_radius=cls.RADIUS,
        )

    # 兼容旧 API
    @classmethod
    def style_frame(cls, frame: ctk.CTkFrame, *, alt: bool = False) -> None:
        cls.style_card(frame, elevated=not alt)

    @classmethod
    def style_toolbar(cls, frame: ctk.CTkFrame) -> None:
        frame.configure(fg_color="transparent", border_width=0)
