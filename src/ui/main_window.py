import threading
import customtkinter as ctk
from tkinter import messagebox, Canvas
import time
import math

SOURCE_ICONS = {
    "Chrome":       "🌐",
    "Brave":        "🦁",
    "Edge":         "🔷",
    "Opera":        "🎠",
    "Opera GX":     "🎮",
    "Vivaldi":      "🎶",
    "Yandex":       "🔍",
    "Chromium":     "🌀",
    "Firefox":      "🦊",
    "Discord":      "💬",
    "Discord PTB":  "🔬",
    "Discord Canary": "🐤",
    "Discord Dev":  "🛠️",
}

COLORS = {
    "bg":           "#f7fbff",
    "surface":      "#ffffff",
    "card":         "#ffffff",
    "card_hover":   "#f1f7ff",
    "border":       "#e2e8f0",
    "purple":       "#3b82f6",
    "purple_light": "#7ec3ff",
    "blue":         "#3b82f6",
    "text":         "#0f172a",
    "muted":        "#334155",
    "green":        "#10b981",
    "red":          "#ef4444",
}


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Token Helper")
        self.geometry("900x620")
        self.minsize(700, 500)
        self.configure(fg_color=COLORS["bg"])

        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 900) // 2
        y = (sh - 620) // 2
        self.geometry(f"900x620+{x}+{y}")

        self._tokens = []
        
        self._build_ui()
        self.attributes("-alpha", 0)

    def start_fade_in(self):
        self._fade_in(0)

    def _fade_in(self, alpha):
        if alpha <= 1.0:
            try:
                self.attributes("-alpha", alpha)
                self.after(20, lambda: self._fade_in(round(alpha + 0.07, 2)))
            except Exception:
                pass

    def _build_ui(self):
        header = ctk.CTkFrame(self, height=70, fg_color=COLORS["surface"], corner_radius=0)
        header.pack(fill="x", side="top")

        ctk.CTkLabel(
            header, text="⚿  Token Helper",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left", padx=24, pady=18)

        self.badge = ctk.CTkLabel(
            header, text="0 tokens valides",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["purple"], corner_radius=8,
            text_color="white", padx=10, pady=4
        )
        self.badge.pack(side="left", padx=8)

        self.refresh_btn = ctk.CTkButton(
            header, text="↻  Actualiser",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
            border_color=COLORS["border"], border_width=1,
            text_color=COLORS["purple_light"], corner_radius=8,
            width=120, height=34,
            command=self._refresh
        )
        self.refresh_btn.pack(side="right", padx=24)

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=0, pady=0)

        sidebar = ctk.CTkScrollableFrame(body, width=220, fg_color=COLORS["surface"], corner_radius=0)
        sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            sidebar, text="SOURCES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["muted"]
        ).pack(padx=16, pady=(20, 8), anchor="w")

        self.source_list_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.source_list_frame.pack(fill="x", padx=8)

        ctk.CTkFrame(sidebar, width=1, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=20)

        login_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        login_frame.pack(padx=12, pady=(0, 20), fill="x")

        ctk.CTkLabel(
            login_frame, text="🚀 Web Login (Manuel)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))

        self.custom_token_entry = ctk.CTkEntry(
            login_frame,
            placeholder_text="Colle un token ici...",
            font=ctk.CTkFont(size=10),
            height=28
        )
        self.custom_token_entry.pack(fill="x", pady=(0, 8))

        self.login_btn = ctk.CTkButton(
            login_frame, text="Se connecter",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS["green"], hover_color="#059669",
            text_color="white", height=32,
            command=self._do_web_login
        )
        self.login_btn.pack(fill="x")

        info = ctk.CTkFrame(sidebar, fg_color="#f1f7ff", corner_radius=10,
                            border_color="#7ec3ff", border_width=1)
        info.pack(padx=12, pady=8, fill="x")
        ctk.CTkLabel(
            info, text="ℹ️  Infos",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#2563eb"
        ).pack(padx=12, pady=(10, 4), anchor="w")
        ctk.CTkLabel(
            info,
            text="• Seuls les tokens\nvalides sont affichés.\n\n• Le pseudo Discord\nest récupéré via\nl'API officielle.",
            font=ctk.CTkFont(size=10),
            text_color="#3b82f6",
            justify="left"
        ).pack(padx=12, pady=(0, 12), anchor="w")

        main_area = ctk.CTkFrame(body, fg_color="transparent")
        main_area.pack(side="left", fill="both", expand=True, padx=0)

        self.scroll = ctk.CTkScrollableFrame(
            main_area, fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["purple"]
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)

        self.empty_label = ctk.CTkLabel(
            self.scroll,
            text="🔍\n\nAucun token valide trouvé\n\nLance un scan ou verifie\nton compte Discord.",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["muted"],
            justify="center"
        )
        self.empty_label.pack(expand=True, pady=80)

    def load_tokens(self, tokens: list):
        self._tokens = tokens
        self._render_tokens()

    def _render_tokens(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        tokens = self._tokens
        count = len(tokens)
        
        self.badge.configure(
            text=f"{count} token{'s' if count != 1 else ''} valide{'s' if count != 1 else ''}",
            fg_color=COLORS["green"] if count > 0 else COLORS["muted"]
        )

        if not tokens:
            self.empty_label.pack(expand=True, pady=80)
            return

        for w in self.source_list_frame.winfo_children():
            w.destroy()

        sources = {}
        for t in tokens:
            s = t["source"]
            sources[s] = sources.get(s, 0) + 1

        for src, cnt in sorted(sources.items()):
            icon = SOURCE_ICONS.get(src, "•")
            row = ctk.CTkFrame(self.source_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{icon}  {src}", font=ctk.CTkFont(size=11)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=str(cnt), font=ctk.CTkFont(size=10, weight="bold"),
                         fg_color=COLORS["purple"], corner_radius=6, text_color="white", padx=6, pady=2).pack(side="right", padx=4)

        for i, token_data in enumerate(tokens):
            self._make_card(token_data, i)

    def _make_card(self, token_data: dict, index: int):
        token = token_data["token"]
        source = token_data["source"]
        username = token_data.get("username", "Inconnu")
        icon = SOURCE_ICONS.get(source, "•")

        card = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=12,
                            border_color=COLORS["border"], border_width=1)
        card.pack(fill="x", pady=6, padx=4)

        def on_enter(e, c=card): c.configure(border_color=COLORS["purple"])
        def on_leave(e, c=card): c.configure(border_color=COLORS["border"])
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        icon_f = ctk.CTkFrame(inner, width=44, height=44, corner_radius=10, fg_color="#f1f7ff")
        icon_f.pack(side="left", padx=(0, 12), anchor="center")
        icon_f.pack_propagate(False)
        ctk.CTkLabel(icon_f, text=icon, font=ctk.CTkFont(size=22)).pack(expand=True)

        info_f = ctk.CTkFrame(inner, fg_color="transparent")
        info_f.pack(side="left", anchor="center")
        ctk.CTkLabel(info_f, text=f"{source} — {username}", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(info_f, text=f"Token #{index + 1}", font=ctk.CTkFont(size=10), text_color=COLORS["muted"]).pack(anchor="w")

        entry = ctk.CTkEntry(inner, font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                             text_color=COLORS["blue"], fg_color="transparent", border_width=0)
        entry.insert(0, token[:20] + "...")
        entry.configure(state="readonly")
        entry.pack(side="left", padx=16, fill="x", expand=True, anchor="center")

        btn_f = ctk.CTkFrame(inner, fg_color="transparent")
        btn_f.pack(side="right", anchor="center")

        auto_btn = ctk.CTkButton(btn_f, text="🚀  Connect", font=ctk.CTkFont(size=11, weight="bold"),
                                 fg_color=COLORS["green"], hover_color="#059669", corner_radius=8, width=90, height=34)
        auto_btn.configure(command=lambda t=token, b=auto_btn: self._do_inline_web_login(t, b))
        auto_btn.pack(side="left", padx=(0, 6))

        copy_btn = ctk.CTkButton(btn_f, text="📋  Copier", font=ctk.CTkFont(size=11, weight="bold"),
                                 fg_color=COLORS["purple"], hover_color="#2563eb", corner_radius=8, width=90, height=34)
        copy_btn.configure(command=lambda t=token, b=copy_btn: self._copy_token(t, b))
        copy_btn.pack(side="left")

    def _do_inline_web_login(self, token: str, btn: ctk.CTkButton):
        btn.configure(state="disabled", text="Ouverture...")
        from login import start_web_login
        start_web_login(token, self, btn)

    def _copy_token(self, token: str, btn: ctk.CTkButton):
        dialog = WarningDialog(self, token, btn)
        dialog.grab_set()

    def _refresh(self):
        self.refresh_btn.configure(state="disabled", text="⏳ Scan…")
        for w in self.scroll.winfo_children(): w.destroy()
        ctk.CTkLabel(self.scroll, text="🔄\n\nScan & Validation en cours…", font=ctk.CTkFont(size=14),
                     text_color=COLORS["muted"]).pack(expand=True, pady=80)

        def run():
            from scanner import scan_all
            res = scan_all(lambda msg, p: self.after(0, lambda: self.refresh_btn.configure(text=f"⏳ {int(p*100)}%")))
            self.after(0, lambda: self._on_refresh_done(res))
        threading.Thread(target=run, daemon=True).start()

    def _on_refresh_done(self, tokens):
        self._tokens = tokens
        self._render_tokens()
        self.refresh_btn.configure(state="normal", text="↻  Actualiser")

    def _do_web_login(self):
        token = self.custom_token_entry.get().strip()
        if not token:
            messagebox.showerror("Erreur", "Entre un token d'abord !")
            return

        self.login_btn.configure(state="disabled", text="Vérification...")
        
        def validate_and_start():
            from scanner import check_token_validity
            username = check_token_validity(token)
            if username:
                self.after(0, lambda: self.login_btn.configure(text="Ouverture..."))
                from login import start_web_login
                start_web_login(token, self, self.login_btn)
            else:
                self.after(0, lambda: messagebox.showerror("Token Invalide", "Ce token ne fonctionne pas ou a expiré."))
                self.after(0, lambda: self.login_btn.configure(state="normal", text="Se connecter"))
        
        threading.Thread(target=validate_and_start, daemon=True).start()

class WarningDialog(ctk.CTkToplevel):
    def __init__(self, parent, token, copy_btn):
        super().__init__(parent)
        self.token = token
        self.copy_btn = copy_btn
        self.parent = parent
        self.title("⚠️  Danger")
        self.geometry("480x380")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["surface"])
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - 480) // 2
        py = parent.winfo_y() + (parent.winfo_height() - 380) // 2
        self.geometry(f"480x380+{px}+{py}")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="⚠️", font=ctk.CTkFont(size=42)).pack(pady=(28, 0))
        ctk.CTkLabel(self, text="Sécurité du Compte", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ef4444").pack(pady=(8, 0))
        box = ctk.CTkFrame(self, fg_color="#fff1f2", corner_radius=10, border_color="#fecdd3", border_width=1)
        box.pack(fill="x", padx=24, pady=14)
        ctk.CTkLabel(box, text="Attention : Ne partage jamais ton token.\nIl donne un accès total à ton compte Discord.",
                     font=ctk.CTkFont(size=11), text_color="#be123c", justify="left").pack(padx=14, pady=12)
        
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=8)
        ctk.CTkButton(row, text="Annuler", width=140, height=38, command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(row, text="✅  Copier", fg_color=COLORS["purple"], width=180, height=38, command=self._confirm).pack(side="left", padx=8)

    def _confirm(self):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.token)
        self.copy_btn.configure(text="✅  Copié !", fg_color=COLORS["green"])
        self.after(2000, lambda: self.copy_btn.configure(text="📋  Copier", fg_color=COLORS["purple"]))
        self.destroy()
