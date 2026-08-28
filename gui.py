import os
import sys
import time
import threading
import customtkinter as ctk
from datetime import datetime

from lcu_core import LCUAutoPilot

# Appearance settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LoLAutoPilotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LoL AutoPilot PRO — Hextech Tactical Suite")
        self.geometry("860x560")
        self.resizable(False, False)

        # Deep Obsidian Hextech Background
        self.configure(fg_color="#03070E")

        # Set Icon (PyInstaller Compatible)
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Backend Core
        self.pilot = LCUAutoPilot(log_callback=self.append_log)
        self.champion_list = sorted(list(self.pilot.champions_map.keys()))

        # Build Modern Hextech UI
        self.setup_ui()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start Background LCU Poller
        self.poller_thread = threading.Thread(target=self.run_poller, daemon=True)
        self.poller_thread.start()

        self.append_log("✨ Hextech Engine başlatıldı. LoL istemcisi taranıyor...")

    def on_closing(self):
        self.save_settings()
        self.pilot.is_running = False
        self.destroy()

    def setup_ui(self):
        # =========================================================================
        # 1. TOP HEADER (Hextech Neon Crystal Bar)
        # =========================================================================
        header = ctk.CTkFrame(
            self, 
            height=62, 
            corner_radius=10, 
            fg_color="#081325", 
            border_width=1, 
            border_color="#C89B3C"
        )
        header.pack(fill="x", padx=16, pady=(12, 8))
        header.pack_propagate(False)

        # Logo & App Title
        left_h = ctk.CTkFrame(header, fg_color="transparent")
        left_h.pack(side="left", padx=16, pady=8)

        title_lbl = ctk.CTkLabel(
            left_h, 
            text="⚡ NEXUS AUTOPILOT", 
            font=ctk.CTkFont(family="Arial Black", size=18, weight="bold"),
            text_color="#F0E6D2"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            left_h, 
            text="CHALLENGER TACTICAL SUITE • DECEIVE GHOST ENGINE", 
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#0AC8B9"
        )
        sub_lbl.pack(anchor="w")

        # Live Status Badges (Right side)
        right_h = ctk.CTkFrame(header, fg_color="transparent")
        right_h.pack(side="right", padx=16, pady=10)

        self.status_badge = ctk.CTkLabel(
            right_h,
            text="🔴 İstemci Bekleniyor",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#E84057",
            fg_color="#02060C",
            corner_radius=8,
            border_width=1,
            border_color="#E84057",
            padx=14,
            pady=6
        )
        self.status_badge.pack(side="right")

        # =========================================================================
        # 2. MAIN 2-COLUMN GRID (NO SCROLLING - 100% CLEAN FIXED FIT)
        # =========================================================================
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=16, pady=0)

        # -------------------------------------------------------------------------
        # LEFT COLUMN: BAN & PICK TACTICAL MATRICES
        # -------------------------------------------------------------------------
        left_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # --- BAN CARD (Crimson Glow) ---
        ban_card = ctk.CTkFrame(
            left_col, 
            corner_radius=8, 
            fg_color="#091428", 
            border_width=1, 
            border_color="#C0392B"
        )
        ban_card.pack(fill="x", pady=(0, 8))

        ban_top = ctk.CTkFrame(ban_card, fg_color="transparent")
        ban_top.pack(fill="x", padx=12, pady=(8, 4))

        self.ban_var = ctk.BooleanVar(value=self.pilot.config.get("auto_ban", True))
        ctk.CTkSwitch(
            ban_top, 
            text="🚫 AKILLI BAN SİSTEMİ", 
            variable=self.ban_var,
            command=self.save_settings,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FF7675",
            progress_color="#E84057"
        ).pack(side="left")

        # Ban Dropdowns Row
        ban_row = ctk.CTkFrame(ban_card, fg_color="transparent")
        ban_row.pack(fill="x", padx=12, pady=(2, 4))

        # 1st Ban
        b1_f = ctk.CTkFrame(ban_row, fg_color="transparent")
        b1_f.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(b1_f, text="1. Tercih (Ana Ban):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F0E6D2").pack(anchor="w")
        self.prim_ban_combo = ctk.CTkComboBox(
            b1_f, 
            values=self.champion_list, 
            command=lambda _: self.save_settings(),
            height=28,
            fg_color="#02060C",
            border_color="#8E1A1A",
            button_color="#580A0A",
            dropdown_fg_color="#0A1428",
            dropdown_text_color="#F0E6D2"
        )
        curr_prim_ban = self.pilot.config.get("primary_ban_champion", "Zed")
        if curr_prim_ban in self.champion_list:
            self.prim_ban_combo.set(curr_prim_ban)
        self.prim_ban_combo.pack(fill="x", pady=(2, 0))

        # 2nd Ban
        b2_f = ctk.CTkFrame(ban_row, fg_color="transparent")
        b2_f.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(b2_f, text="2. Tercih (Yedek Ban):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F0E6D2").pack(anchor="w")
        self.sec_ban_combo = ctk.CTkComboBox(
            b2_f, 
            values=self.champion_list, 
            command=lambda _: self.save_settings(),
            height=28,
            fg_color="#02060C",
            border_color="#8E1A1A",
            button_color="#580A0A",
            dropdown_fg_color="#0A1428",
            dropdown_text_color="#F0E6D2"
        )
        curr_sec_ban = self.pilot.config.get("secondary_ban_champion", "Yasuo")
        if curr_sec_ban in self.champion_list:
            self.sec_ban_combo.set(curr_sec_ban)
        self.sec_ban_combo.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            ban_card,
            text="🛡️ Takım arkadaşın 1. banını oynamak istiyorsa (hover) sistem 2. banını banlar.",
            font=ctk.CTkFont(size=9),
            text_color="#0AC8B9"
        ).pack(anchor="w", padx=12, pady=(2, 8))


        # --- PICK CARD (Hextech Turquoise Glow) ---
        pick_card = ctk.CTkFrame(
            left_col, 
            corner_radius=8, 
            fg_color="#091428", 
            border_width=1, 
            border_color="#0AC8B9"
        )
        pick_card.pack(fill="x", pady=(0, 4))

        pick_top = ctk.CTkFrame(pick_card, fg_color="transparent")
        pick_top.pack(fill="x", padx=12, pady=(8, 4))

        self.pick_var = ctk.BooleanVar(value=self.pilot.config.get("auto_pick", True))
        ctk.CTkSwitch(
            pick_top, 
            text="🎯 AKILLI ŞAMPİYON SEÇİMİ", 
            variable=self.pick_var,
            command=self.save_settings,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#0AC8B9",
            progress_color="#005A82"
        ).pack(side="left")

        # Pick Dropdowns Row
        pick_row = ctk.CTkFrame(pick_card, fg_color="transparent")
        pick_row.pack(fill="x", padx=12, pady=(2, 4))

        # 1st Pick
        p1_f = ctk.CTkFrame(pick_row, fg_color="transparent")
        p1_f.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(p1_f, text="1. Tercih (Ana Şampiyon):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F0E6D2").pack(anchor="w")
        self.prim_pick_combo = ctk.CTkComboBox(
            p1_f, 
            values=self.champion_list, 
            command=lambda _: self.save_settings(),
            height=28,
            fg_color="#02060C",
            border_color="#005A82",
            button_color="#003750",
            dropdown_fg_color="#0A1428",
            dropdown_text_color="#F0E6D2"
        )
        curr_prim_pick = self.pilot.config.get("primary_pick_champion", "Yasuo")
        if curr_prim_pick in self.champion_list:
            self.prim_pick_combo.set(curr_prim_pick)
        self.prim_pick_combo.pack(fill="x", pady=(2, 0))

        # 2nd Pick
        p2_f = ctk.CTkFrame(pick_row, fg_color="transparent")
        p2_f.pack(side="right", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(p2_f, text="2. Tercih (Yedek Şampiyon):", font=ctk.CTkFont(size=10, weight="bold"), text_color="#F0E6D2").pack(anchor="w")
        self.sec_pick_combo = ctk.CTkComboBox(
            p2_f, 
            values=self.champion_list, 
            command=lambda _: self.save_settings(),
            height=28,
            fg_color="#02060C",
            border_color="#005A82",
            button_color="#003750",
            dropdown_fg_color="#0A1428",
            dropdown_text_color="#F0E6D2"
        )
        curr_sec_pick = self.pilot.config.get("secondary_pick_champion", "Yone")
        if curr_sec_pick in self.champion_list:
            self.sec_pick_combo.set(curr_sec_pick)
        self.sec_pick_combo.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            pick_card,
            text="🔄 1. şampiyon banlanmışsa veya alınmışsa anında 2. şampiyon kilitlenir.",
            font=ctk.CTkFont(size=9),
            text_color="#F0E6D2"
        ).pack(anchor="w", padx=12, pady=(2, 8))


        # -------------------------------------------------------------------------
        # RIGHT COLUMN: FAST AUTOMATIONS + DECEIVE + TERMINAL
        # -------------------------------------------------------------------------
        right_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(6, 0))

        # --- FAST SWITCHES CARD ---
        fast_card = ctk.CTkFrame(
            right_col, 
            corner_radius=8, 
            fg_color="#091428", 
            border_width=1, 
            border_color="#1E282D"
        )
        fast_card.pack(fill="x", pady=(0, 8))

        # 1. Auto Accept Switch
        self.accept_var = ctk.BooleanVar(value=self.pilot.config.get("auto_accept", True))
        row_sw1 = ctk.CTkFrame(fast_card, fg_color="transparent")
        row_sw1.pack(fill="x", padx=12, pady=(6, 3))
        
        ctk.CTkSwitch(
            row_sw1, 
            text="⚡ Otomatik Maç Kabul (Auto-Accept)", 
            variable=self.accept_var,
            command=self.save_settings,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F0E6D2",
            progress_color="#0AC8B9"
        ).pack(side="left")

        # 2. Deceive (Appear Offline) Switch
        self.offline_var = ctk.BooleanVar(value=self.pilot.config.get("appear_offline", False))
        row_sw2 = ctk.CTkFrame(fast_card, fg_color="transparent")
        row_sw2.pack(fill="x", padx=12, pady=3)
        
        ctk.CTkSwitch(
            row_sw2, 
            text="👻 Çevrimdışı Görün (Deceive / Hayalet Mod)", 
            variable=self.offline_var,
            command=self.toggle_offline_mode,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#D6A2E8",
            progress_color="#9B59B6"
        ).pack(side="left")

        # 3. LoL Killer Switch
        self.close_game_var = ctk.BooleanVar(value=self.pilot.config.get("auto_close_game", True))
        row_sw3 = ctk.CTkFrame(fast_card, fg_color="transparent")
        row_sw3.pack(fill="x", padx=12, pady=(3, 6))
        
        ctk.CTkSwitch(
            row_sw3, 
            text="🚨 Oyun Başlayınca 'League of Legends.exe'yi Kapat", 
            variable=self.close_game_var,
            command=self.save_settings,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F39C12",
            progress_color="#FFB800"
        ).pack(side="left")

        # --- LIVE TERMINAL CONSOLE CARD ---
        term_card = ctk.CTkFrame(
            right_col, 
            corner_radius=8, 
            fg_color="#02060C", 
            border_width=1, 
            border_color="#1E282D"
        )
        term_card.pack(fill="both", expand=True)

        term_head = ctk.CTkFrame(term_card, fg_color="transparent")
        term_head.pack(fill="x", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            term_head, 
            text="📋 CANLI İŞLEM GÜNLÜĞÜ", 
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#A09B8C"
        ).pack(side="left")

        ctk.CTkButton(
            term_head,
            text="Temizle",
            width=50,
            height=20,
            font=ctk.CTkFont(size=10),
            fg_color="#081325",
            hover_color="#1E282D",
            border_width=1,
            border_color="#785A28",
            command=self.clear_logs
        ).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(
            term_card,
            fg_color="#010408",
            text_color="#F0E6D2",
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # =========================================================================
        # 3. BOTTOM FOOTER STATUS
        # =========================================================================
        footer = ctk.CTkFrame(self, height=24, fg_color="#02060C")
        footer.pack(fill="x", side="bottom", padx=16, pady=(4, 6))

        ctk.CTkLabel(
            footer,
            text="🟢 Arka Plan Motoru Aktif • Ayarlar otomatik kalıcı kaydedilir.",
            font=ctk.CTkFont(size=10),
            text_color="#5B5A56"
        ).pack(side="left", padx=6)

        ctk.CTkLabel(
            footer,
            text="Riot LCU & Deceive Protocol",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#785A28"
        ).pack(side="right", padx=6)

    def toggle_offline_mode(self):
        enabled = self.offline_var.get()
        self.pilot.config["appear_offline"] = enabled
        self.pilot.set_offline_mode(enabled)
        self.save_settings()

    def save_settings(self):
        self.pilot.config["auto_accept"] = self.accept_var.get()
        self.pilot.config["auto_close_game"] = self.close_game_var.get()
        self.pilot.config["appear_offline"] = self.offline_var.get()
        
        self.pilot.config["auto_ban"] = self.ban_var.get()
        self.pilot.config["primary_ban_champion"] = self.prim_ban_combo.get()
        self.pilot.config["secondary_ban_champion"] = self.sec_ban_combo.get()
        
        self.pilot.config["auto_pick"] = self.pick_var.get()
        self.pilot.config["primary_pick_champion"] = self.prim_pick_combo.get()
        self.pilot.config["secondary_pick_champion"] = self.sec_pick_combo.get()
        
        self.pilot.save_config()

    def append_log(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {text}\n"
        
        def _update():
            if hasattr(self, 'log_textbox'):
                self.log_textbox.insert("end", formatted)
                
                # Limit to 100 lines to prevent memory leaks / GUI lag
                try:
                    lines = int(self.log_textbox.index('end-1c').split('.')[0])
                    if lines > 100:
                        self.log_textbox.delete("1.0", "2.0")
                except Exception:
                    pass
                    
                self.log_textbox.see("end")
        
        self.after(0, _update)

    def clear_logs(self):
        self.log_textbox.delete("1.0", "end")

    def run_poller(self):
        while self.pilot.is_running:
            try:
                self.pilot.update_loop()
                
                def _update_badge():
                    if self.pilot.is_connected:
                        phase = self.pilot.current_phase
                        phase_tr = {
                            "None": "Boşta",
                            "Lobby": "Lobi",
                            "Matchmaking": "Sırada",
                            "ReadyCheck": "⚡ Maç Bulundu!",
                            "ChampSelect": "🎯 Şampiyon Seçimi",
                            "InProgress": "🎮 Oyun Başladı",
                            "WaitingForStats": "Maç Sonu"
                        }.get(phase, phase)
                        
                        offline_tag = " [👻 Çevrimdışı]" if self.pilot.config.get("appear_offline") else ""
                        self.status_badge.configure(
                            text=f"🟢 LoL Bağlı ({phase_tr}){offline_tag}",
                            text_color="#20C997",
                            border_color="#20C997"
                        )
                    else:
                        self.status_badge.configure(
                            text="🔴 LoL İstemcisi Bekleniyor",
                            text_color="#E84057",
                            border_color="#E84057"
                        )

                self.after(0, _update_badge)
            except Exception as e:
                self.append_log(f"⚠️ Kritik Döngü Hatası: {e}")
            time.sleep(0.8)

def main():
    app = LoLAutoPilotApp()
    app.mainloop()

if __name__ == "__main__":
    main()
