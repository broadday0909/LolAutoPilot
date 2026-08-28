import os
import sys
import json
import time
import threading
import webbrowser
import requests
import webview
from lcu_core import LCUAutoPilot, get_config_path

CURRENT_VERSION = "1.0.0"
GITHUB_REPO = "broadday0909/LolAutoPilot"

# Resolve base dir for PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pilot = LCUAutoPilot()

class JSApi:
    def __init__(self):
        self.logs = []

    def get_initial_data(self):
        return {
            "version": CURRENT_VERSION,
            "config": pilot.config,
            "champions": pilot.champions_map,
            "connected": pilot.is_connected,
            "phase": pilot.current_phase,
            "summoner": pilot.get_summoner_info() if pilot.is_connected else None,
            "ranked": pilot.get_ranked_stats() if pilot.is_connected else None,
            "mastery": pilot.get_top_masteries(6) if pilot.is_connected else [],
            "logs": self.logs.copy()
        }

    def check_for_updates(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            headers = {"User-Agent": "LoLAutoPilot-App"}
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                tag = data.get("tag_name", "").lstrip("vV").strip()
                curr = CURRENT_VERSION.lstrip("vV").strip()
                
                def parse_v(v):
                    p = []
                    for x in v.split('.'):
                        try:
                            p.append(int(x))
                        except ValueError:
                            p.append(0)
                    return p
                
                has_update = parse_v(tag) > parse_v(curr)
                return {
                    "has_update": has_update,
                    "current_version": CURRENT_VERSION,
                    "latest_version": data.get("tag_name", tag),
                    "release_url": data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases"),
                    "release_notes": data.get("body", "")
                }
        except Exception as e:
            return {"has_update": False, "error": str(e), "current_version": CURRENT_VERSION}
        return {"has_update": False, "current_version": CURRENT_VERSION}

    def open_url(self, url):
        try:
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_config(self, new_config):
        pilot.config.update(new_config)
        pilot.save_config()
        if "appear_offline" in new_config:
            pilot.set_offline_mode(new_config["appear_offline"])
        return {"success": True}

    def get_status(self):
        return {
            "connected": pilot.is_connected,
            "phase": pilot.current_phase,
            "appear_offline": pilot.config.get("appear_offline", False),
            "summoner": pilot.get_summoner_info() if pilot.is_connected else None,
            "ranked": pilot.get_ranked_stats() if pilot.is_connected else None,
            "mastery": pilot.get_top_masteries(6) if pilot.is_connected else []
        }

    def get_champion_skins(self, champion_id):
        return pilot.get_champion_skins(int(champion_id))

    def set_profile_background(self, skin_id):
        return pilot.set_profile_background(int(skin_id))

    def clear_logs(self):
        self.logs.clear()
        return {"success": True}

js_api = JSApi()

def gui_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "text": msg}
    js_api.logs.append(entry)
    # Prevent memory leak on Python side (keep last 100 logs)
    if len(js_api.logs) > 100:
        js_api.logs = js_api.logs[-100:]
    try:
        if window:
            window.evaluate_js(f"window.onNewLog({json.dumps(entry)})")
    except Exception:
        pass

pilot.log_callback = gui_log

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LoL AutoPilot PRO</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-main: #0a0e17;
      --bg-sidebar: #101522;
      --bg-card: #141b2d;
      --bg-card-elevated: #1a233a;
      
      --accent-cyan: #00f2fe;
      --accent-purple: #c471ed;
      --accent-pink: #ff416c;
      --accent-green: #00f260;
      --accent-gold: #ffb300;
      --accent-discord: #5865F2;
      
      --text-main: #ffffff;
      --text-muted: #94a3b8;
      --text-dark: #090d16;
      
      --border-subtle: rgba(255, 255, 255, 0.1);
      --radius-lg: 18px;
      --radius-md: 12px;
      --radius-sm: 8px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
    }

    body {
      font-family: 'Outfit', sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      height: 100vh;
      overflow: hidden;
      display: flex;
      -webkit-font-smoothing: antialiased;
    }

    /* SIDEBAR */
    .sidebar {
      width: 230px;
      background-color: var(--bg-sidebar);
      padding: 22px 14px;
      display: flex;
      flex-direction: column;
      justifyContent: space-between;
      border-right: 1px solid var(--border-subtle);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-left: 6px;
      margin-bottom: 20px;
    }

    .brand-logo-img {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      object-fit: cover;
      border: 1.5px solid rgba(255, 65, 108, 0.4);
      box-shadow: 0 4px 16px rgba(255, 65, 108, 0.35);
    }

    .brand-text {
      font-size: 15.5px;
      font-weight: 900;
      letter-spacing: 0.5px;
      color: #ffffff;
    }

    .nav-list {
      display: flex;
      flex-direction: column;
      gap: 5px;
      flex: 1;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 14px;
      border-radius: var(--radius-md);
      font-size: 13px;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s ease;
      background: transparent;
      border: none;
      width: 100%;
      text-align: left;
    }

    .nav-item:hover {
      color: #ffffff;
      background: rgba(255, 255, 255, 0.07);
    }

    .nav-item.active {
      background: #ffffff;
      color: var(--text-dark);
      font-weight: 800;
      box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
    }

    /* Summoner Profile Badge */
    .sidebar-user {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 12px;
      background: rgba(0, 0, 0, 0.4);
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }

    .avatar-wrapper {
      position: relative;
      width: 40px;
      height: 40px;
      flex-shrink: 0;
    }

    .user-avatar-img {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 2px solid var(--accent-cyan);
      object-fit: cover;
      display: none;
      box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);
    }

    .user-avatar-fallback {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #1e283d;
      border: 2px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: #94a3b8;
    }

    .user-info {
      display: flex;
      flex-direction: column;
      overflow: hidden;
      gap: 2px;
    }

    .user-name-row {
      display: flex;
      align-items: center;
      gap: 6px;
      overflow: hidden;
    }

    .user-name {
      font-size: 13px;
      font-weight: 800;
      color: #ffffff;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }

    .user-level-badge {
      font-size: 10px;
      font-weight: 800;
      background: rgba(0, 242, 254, 0.2);
      color: var(--accent-cyan);
      padding: 2px 6px;
      border-radius: 5px;
      display: none;
      border: 1px solid rgba(0, 242, 254, 0.3);
    }

    .user-status {
      font-size: 11px;
      color: #ff416c;
      font-weight: 700;
    }

    /* MAIN CONTENT */
    .main-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 22px 28px;
      overflow: hidden;
    }

    .top-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }

    .page-title {
      font-size: 20px;
      font-weight: 900;
      letter-spacing: -0.3px;
      color: #ffffff;
    }

    .status-pill {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 7px 15px;
      border-radius: 24px;
      font-size: 12px;
      font-weight: 800;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .status-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #ff416c;
    }

    .status-dot.online {
      background: var(--accent-green);
      box-shadow: 0 0 10px var(--accent-green);
    }

    /* VIEW PANELS */
    .view-panel {
      display: none;
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      padding-right: 4px;
    }

    .view-panel.active {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .card {
      background: var(--bg-card);
      border-radius: var(--radius-lg);
      padding: 22px 24px;
      border: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
    }

    .card-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }

    .card-title {
      font-size: 17px;
      font-weight: 900;
      display: flex;
      align-items: center;
      gap: 10px;
      color: #ffffff;
      letter-spacing: -0.2px;
    }

    .card-subtitle {
      font-size: 12.5px;
      font-weight: 500;
      color: var(--text-muted);
      margin-top: 3px;
      line-height: 1.4;
    }

    /* Modern Toggle Switches */
    .toggle-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    }

    .toggle-row:last-child {
      border-bottom: none;
    }

    .switch-label-group {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }

    .switch-label {
      font-size: 14px;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.1px;
    }

    .switch-desc {
      font-size: 12px;
      font-weight: 500;
      color: var(--text-muted);
    }

    .switch {
      position: relative;
      display: inline-block;
      width: 48px;
      height: 26px;
      flex-shrink: 0;
    }

    .switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: #334155;
      transition: .2s ease;
      border-radius: 26px;
    }

    .slider:before {
      position: absolute;
      content: "";
      height: 20px;
      width: 20px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: .2s ease;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.35);
    }

    input:checked + .slider {
      background: linear-gradient(135deg, #00f2fe 0%, #0072ff 100%);
    }

    input:checked + .slider.pink {
      background: linear-gradient(135deg, #ff416c 0%, #c471ed 100%);
    }

    input:checked + .slider.green {
      background: linear-gradient(135deg, #00f260 0%, #0575e6 100%);
    }

    input:checked + .slider:before {
      transform: translateX(22px);
    }

    /* Dropdowns Container */
    .select-group {
      display: flex;
      gap: 16px;
      margin: 16px 0;
      transition: opacity 0.2s ease;
    }

    .select-group.disabled {
      opacity: 0.3;
      pointer-events: none;
    }

    .select-box {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .select-label {
      font-size: 11.5px;
      font-weight: 800;
      color: #cbd5e1;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    select {
      width: 100%;
      background: #0d121c;
      border: 1.5px solid rgba(255, 255, 255, 0.12);
      color: #ffffff;
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      font-family: inherit;
      font-size: 13.5px;
      font-weight: 700;
      outline: none;
      cursor: pointer;
      transition: all 0.2s;
    }

    select:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 12px rgba(0, 242, 254, 0.25);
    }

    /* Info Badge Box */
    .info-box {
      padding: 13px 15px;
      border-radius: var(--radius-md);
      font-size: 12.5px;
      font-weight: 500;
      line-height: 1.5;
    }

    /* STATS & MASTERY STYLES */
    .ranked-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .ranked-card {
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px 18px;
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .ranked-emblem {
      width: 60px;
      height: 60px;
      object-fit: contain;
      filter: drop-shadow(0 0 10px rgba(0, 242, 254, 0.3));
    }

    .ranked-meta {
      display: flex;
      flex-direction: column;
      gap: 3px;
      flex: 1;
    }

    .ranked-qname {
      font-size: 11.5px;
      font-weight: 800;
      color: #94a3b8;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .ranked-tier {
      font-size: 16px;
      font-weight: 900;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .ranked-lp {
      font-size: 12.5px;
      font-weight: 700;
      color: var(--accent-cyan);
    }

    .ranked-wr {
      font-size: 11.5px;
      font-weight: 600;
      color: #cbd5e1;
    }

    .mastery-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-top: 10px;
    }

    .mastery-card {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px 14px;
      display: flex;
      align-items: center;
      gap: 12px;
      transition: all 0.2s;
    }

    .mastery-card:hover {
      border-color: var(--accent-cyan);
      transform: translateY(-2px);
    }

    .mastery-icon {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      border: 2px solid var(--accent-gold);
      object-fit: cover;
    }

    .mastery-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
      overflow: hidden;
    }

    .mastery-name {
      font-size: 13.5px;
      font-weight: 800;
      color: #ffffff;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }

    .mastery-lvl {
      font-size: 11px;
      font-weight: 800;
      color: var(--accent-gold);
    }

    .mastery-pts {
      font-size: 11px;
      font-weight: 600;
      color: #94a3b8;
    }

    /* PROFILE BACKGROUND STYLES */
    .splash-preview-card {
      width: 100%;
      height: 180px;
      border-radius: var(--radius-md);
      background-size: cover;
      background-position: center top;
      border: 1.5px solid var(--border-subtle);
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: flex-end;
      padding: 16px;
      margin: 14px 0;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }

    .splash-overlay {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: linear-gradient(to top, rgba(10, 14, 23, 0.95) 0%, rgba(10, 14, 23, 0.1) 60%);
    }

    .splash-title-box {
      position: relative;
      z-index: 2;
    }

    .splash-skin-name {
      font-size: 18px;
      font-weight: 900;
      color: #ffffff;
      text-shadow: 0 2px 8px rgba(0,0,0,0.8);
    }

    .splash-skin-id {
      font-size: 11.5px;
      font-weight: 700;
      color: var(--accent-cyan);
    }

    .apply-bg-btn {
      background: linear-gradient(135deg, #00f2fe 0%, #0072ff 100%);
      border: none;
      color: #ffffff;
      font-family: inherit;
      font-size: 14px;
      font-weight: 800;
      padding: 12px 20px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      box-shadow: 0 4px 18px rgba(0, 242, 254, 0.35);
    }

    .apply-bg-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 22px rgba(0, 242, 254, 0.5);
    }

    /* Credits Styles */
    .credits-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 10px;
    }

    .credits-card {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .credits-label {
      font-size: 11px;
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .credits-value {
      font-size: 14.5px;
      font-weight: 800;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .discord-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(88, 101, 242, 0.18);
      border: 1px solid rgba(88, 101, 242, 0.4);
      color: #7289da;
      padding: 5px 10px;
      border-radius: 8px;
      font-size: 13.5px;
      font-weight: 800;
    }

    .copy-btn {
      background: var(--accent-discord);
      border: none;
      color: #ffffff;
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 700;
      cursor: pointer;
      transition: opacity 0.2s;
    }

    .copy-btn:hover {
      opacity: 0.85;
    }

    /* Terminal Console */
    .terminal-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }

    .terminal-title {
      font-size: 13px;
      font-weight: 800;
      color: #94a3b8;
      letter-spacing: 0.5px;
    }

    .terminal-logs {
      flex: 1;
      overflow-y: auto;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: #e2e8f0;
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding-right: 6px;
    }

    .log-line {
      display: flex;
      gap: 10px;
      line-height: 1.5;
    }

    .log-time {
      color: #64748b;
      font-weight: 600;
    }

    /* Update Notification Banner */
    .update-banner {
      background: linear-gradient(135deg, rgba(0, 242, 96, 0.12), rgba(0, 242, 254, 0.08));
      border: 1px solid rgba(0, 242, 96, 0.4);
      border-radius: var(--radius-md);
      padding: 12px 18px;
      margin-bottom: 16px;
      box-shadow: 0 4px 20px rgba(0, 242, 96, 0.15);
      animation: fadeInDown 0.3s ease;
    }

    .update-banner-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
    }

    .update-icon {
      font-size: 24px;
    }

    .update-text {
      flex: 1;
    }

    .update-title {
      font-size: 13.5px;
      font-weight: 800;
      color: #00f260;
      margin-bottom: 2px;
    }

    .update-subtitle {
      font-size: 11.5px;
      color: #94a3b8;
    }

    .update-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-update-now {
      background: linear-gradient(135deg, #00f260, #0575e6);
      color: #ffffff;
      border: none;
      border-radius: 8px;
      padding: 7px 14px;
      font-size: 12px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 2px 10px rgba(0, 242, 96, 0.3);
      transition: all var(--transition-fast);
    }

    .btn-update-now:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(0, 242, 96, 0.45);
    }

    .btn-update-close {
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-muted);
      border: none;
      border-radius: 8px;
      width: 28px;
      height: 28px;
      cursor: pointer;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--transition-fast);
    }

    .btn-update-close:hover {
      background: rgba(255, 75, 75, 0.2);
      color: #ff4b4b;
    }
  </style>
</head>
<body>

  <!-- Left Sidebar -->
  <div class="sidebar">
    <div>
      <div class="brand">
        <img class="brand-logo-img" src="https://ddragon.leagueoflegends.com/cdn/img/champion/tiles/Talon_5.jpg" onerror="this.src='https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/assets/characters/talon/skins/skin05/images/talon_splash_tile_5.jpg'" alt="LoL AutoPilot" />
        <div class="brand-text">LoLAutoPilot</div>
      </div>

      <div class="nav-list">
        <button class="nav-item active" id="btn-automations" onclick="switchView('automations')">
          <span>⚡</span> Hızlı Ayarlar
        </button>
        <button class="nav-item" id="btn-stats" onclick="switchView('stats')">
          <span>🏆</span> İstatistik & Ustalık
        </button>
        <button class="nav-item" id="btn-profile-bg" onclick="switchView('profile-bg')">
          <span>👑</span> Özel Profil Splash
        </button>
        <button class="nav-item" id="btn-ban" onclick="switchView('ban')">
          <span>🚫</span> Ban Sistemi
        </button>
        <button class="nav-item" id="btn-pick" onclick="switchView('pick')">
          <span>🎯</span> Şampiyon Seçimi
        </button>
        <button class="nav-item" id="btn-deceive" onclick="switchView('deceive')">
          <span>👻</span> Deceive (Hayalet)
        </button>
        <button class="nav-item" id="btn-logs" onclick="switchView('logs')">
          <span>📋</span> Canlı Loglar
        </button>
        <button class="nav-item" id="btn-credits" onclick="switchView('credits')">
          <span>ℹ️</span> Geliştirici & Bilgi
        </button>
      </div>
    </div>

    <!-- User LCU Status & Summoner Profile at Bottom -->
    <div class="sidebar-user">
      <div class="avatar-wrapper">
        <img id="userAvatarImg" class="user-avatar-img" src="" alt="Icon" />
        <div id="userAvatarFallback" class="user-avatar-fallback">👤</div>
      </div>
      <div class="user-info">
        <div class="user-name-row">
          <span class="user-name" id="summonerName">LoL Client</span>
          <span class="user-level-badge" id="summonerLevel">Lv. 30</span>
        </div>
        <div class="user-status" id="sidebarStatus">İstemci Bekleniyor</div>
      </div>
    </div>
  </div>

  <!-- Main Content Area -->
  <div class="main-wrapper">
    <!-- Top Header -->
    <div class="top-header">
      <div class="page-title" id="pageTitle">Hızlı Otomasyon Ayarları</div>
      <div class="status-pill">
        <div class="status-dot" id="statusDot"></div>
        <span id="headerStatusText">🔴 İstemci Bekleniyor</span>
      </div>
    </div>

    <!-- Update Notification Banner (Hidden by default) -->
    <div id="updateBanner" class="update-banner" style="display: none;">
      <div class="update-banner-content">
        <span class="update-icon">🚀</span>
        <div class="update-text">
          <div class="update-title" id="updateBannerTitle">Yeni Sürüm Mevcut! (v1.0.1)</div>
          <div class="update-subtitle" id="updateBannerSubtitle">LoL AutoPilot PRO için yeni bir güncelleme yayınlandı.</div>
        </div>
        <div class="update-actions">
          <button class="btn-update-now" id="btnUpdateNow" onclick="openReleasePage()">📥 Hemen İndir</button>
          <button class="btn-update-close" onclick="closeUpdateBanner()">✕</button>
        </div>
      </div>
    </div>

    <!-- TAB 1: FAST AUTOMATIONS -->
    <div class="view-panel active" id="view-automations">
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #00f2fe;">⚡ Otomasyon & Taktik Anahtarları</div>
            <div class="card-subtitle">İstemci ve oyun içi tüm süreçleri tek tıkla otomatikleştirin</div>
          </div>
        </div>

        <div class="toggle-row">
          <div class="switch-label-group">
            <span class="switch-label">Otomatik Maç Kabul (Auto-Accept)</span>
            <span class="switch-desc">Sıra geldiğinde maçı milisaniyeler içinde anında kabul eder.</span>
          </div>
          <label class="switch">
            <input type="checkbox" id="swAccept" onchange="onConfigChange()">
            <span class="slider green"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div class="switch-label-group">
            <span class="switch-label">👻 Çevrimdışı Görün (Deceive Ghost Mode)</span>
            <span class="switch-desc">Arkadaş listenizde tamamen çevrimdışı (kapalı) görünürsünüz.</span>
          </div>
          <label class="switch">
            <input type="checkbox" id="swOffline" onchange="onOfflineToggle('swOffline')">
            <span class="slider pink"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div class="switch-label-group">
            <span class="switch-label">🚨 Oyun Başlayınca 'League of Legends.exe'yi Kapat (Game Killer)</span>
            <span class="switch-desc">Şampiyon seçimi bitip oyun açıldığı an oyunu kapatır, istemciyi açık bırakır. Oyuncuları yükleme ekranında bekletir ve oyunun geç başlamasını sağlar (4-5 dakika içerisinde oyun başlar, bu yüzden istemciden tekrar bağlanmanız gerekir. Sigara molaları için ideal 😄).</span>
          </div>
          <label class="switch">
            <input type="checkbox" id="swKillGame" onchange="onConfigChange()">
            <span class="slider"></span>
          </label>
        </div>
      </div>
    </div>

    <!-- TAB 2: LIVE STATS & MASTERY SHOWCASE -->
    <div class="view-panel" id="view-stats">
      <!-- Ranked Cards -->
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #ffb300;">🏆 Canlı Dereceli İstatistikleri</div>
            <div class="card-subtitle">Mevcut liginiz, LP dereceniz ve galibiyet oranlarınız</div>
          </div>
        </div>

        <div class="ranked-grid">
          <!-- Solo/Duo -->
          <div class="ranked-card">
            <img id="soloEmblem" class="ranked-emblem" src="https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/images/unranked.png" alt="Emblem" />
            <div class="ranked-meta">
              <span class="ranked-qname">Tekli / Çiftli Dereceli</span>
              <span class="ranked-tier" id="soloTier">UNRANKED</span>
              <span class="ranked-lp" id="soloLp">0 LP</span>
              <span class="ranked-wr" id="soloWr">0G 0M (%0 WR)</span>
            </div>
          </div>

          <!-- Flex -->
          <div class="ranked-card">
            <img id="flexEmblem" class="ranked-emblem" src="https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/images/unranked.png" alt="Emblem" />
            <div class="ranked-meta">
              <span class="ranked-qname">Esnek (Flex) Dereceli</span>
              <span class="ranked-tier" id="flexTier">UNRANKED</span>
              <span class="ranked-lp" id="flexLp">0 LP</span>
              <span class="ranked-wr" id="flexWr">0G 0M (%0 WR)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Masteries -->
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #00f2fe;">👑 En Yüksek Şampiyon Ustalıkları</div>
            <div class="card-subtitle">En çok oynadığınız şampiyonların ustalık seviyeleri ve puanları</div>
          </div>
        </div>

        <div class="mastery-grid" id="masteryGrid">
          <div style="grid-column: 1 / -1; text-align: center; color: #94a3b8; font-size: 13px; padding: 20px;">
            İstemciye bağlanıldığında ustalık vitrini yüklenecek...
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: CUSTOM PROFILE BACKGROUND SETTER -->
    <div class="view-panel" id="view-profile-bg">
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #c471ed;">👑 Özel Profil Arka Planı (Splash) Ayarlayıcı</div>
            <div class="card-subtitle">İstediğiniz şampiyon ve kostümün görselini tek tıkla LoL profil arka planınız yapın</div>
          </div>
        </div>

        <div class="select-group" style="margin-top: 0;">
          <div class="select-box">
            <span class="select-label">1. Şampiyon Seçin</span>
            <select id="selBgChamp" onchange="onBgChampChange()"></select>
          </div>
          <div class="select-box">
            <span class="select-label">2. Kostüm / Splash Seçin</span>
            <select id="selBgSkin" onchange="onBgSkinChange()"></select>
          </div>
        </div>

        <!-- Splash Art Preview -->
        <div class="splash-preview-card" id="splashPreviewCard">
          <div class="splash-overlay"></div>
          <div class="splash-title-box">
            <div class="splash-skin-name" id="splashSkinName">Kanlı Ay Talon</div>
            <div class="splash-skin-id" id="splashSkinId">Skin ID: 91005</div>
          </div>
        </div>

        <button class="apply-bg-btn" onclick="applyProfileBackground()">
          <span>👑</span> Bu Görseli Profil Arka Planı Yap
        </button>

        <div class="info-box" style="background: rgba(196, 113, 237, 0.08); border: 1px solid rgba(196, 113, 237, 0.25); color: #c471ed; margin-top: 14px;">
          💡 <strong>Nasıl Çalışır?</strong> Sahip olmadığınız kostümler dahil dilediğiniz kostümü profil arka planına yerleştirebilirsiniz. Değişiklik LoL istemcinizin Profil sekmesinde anında görünür.
        </div>
      </div>
    </div>

    <!-- TAB 4: BAN MATRIX -->
    <div class="view-panel" id="view-ban">
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #ff416c;">🚫 Akıllı Şampiyon Ban Sistemi</div>
            <div class="card-subtitle">Sıranız geldiğinde otomatik banlar. Takım arkadaşınız şampiyonu göstermişse banlamaz.</div>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span id="banStatusLabel" style="font-size: 13.5px; font-weight: 900; color: #ff416c;">AKTİF</span>
            <label class="switch">
              <input type="checkbox" id="swBan" onchange="onBanToggle()">
              <span class="slider pink"></span>
            </label>
          </div>
        </div>

        <div class="select-group" id="banSelectGroup">
          <div class="select-box">
            <span class="select-label">1. Tercih (Ana Ban Şampiyonu)</span>
            <select id="selPrimBan" onchange="onConfigChange()"></select>
          </div>
          <div class="select-box">
            <span class="select-label">2. Tercih (Yedek Ban Şampiyonu)</span>
            <select id="selSecBan" onchange="onConfigChange()"></select>
          </div>
        </div>

        <div class="info-box" style="background: rgba(0, 242, 254, 0.08); border: 1px solid rgba(0, 242, 254, 0.25); color: #00f2fe;">
          🛡️ <strong>Akıllı Koruma:</strong> Takım arkadaşınız 1. ban tercihinizi oynamak istiyorsa (Hover/Intent), sistem takım arkadaşınızı trollememek için otomatik olarak 2. ban tercihinize geçer.
        </div>
      </div>
    </div>

    <!-- TAB 5: PICK MATRIX -->
    <div class="view-panel" id="view-pick">
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #00f260;">🎯 Akıllı Şampiyon Seçim & Kilitleme</div>
            <div class="card-subtitle">Sıra size geldiğinde otomatik seçip kilitler. Banlanmışsa yedek şampiyonu alır.</div>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span id="pickStatusLabel" style="font-size: 13.5px; font-weight: 900; color: #00f260;">AKTİF</span>
            <label class="switch">
              <input type="checkbox" id="swPick" onchange="onPickToggle()">
              <span class="slider green"></span>
            </label>
          </div>
        </div>

        <div class="select-group" id="pickSelectGroup">
          <div class="select-box">
            <span class="select-label">1. Tercih (Ana Şampiyon)</span>
            <select id="selPrimPick" onchange="onConfigChange()"></select>
          </div>
          <div class="select-box">
            <span class="select-label">2. Tercih (Yedek Şampiyon)</span>
            <select id="selSecPick" onchange="onConfigChange()"></select>
          </div>
        </div>

        <div class="info-box" style="background: rgba(0, 242, 96, 0.08); border: 1px solid rgba(0, 242, 96, 0.25); color: #00f260;">
          🔄 <strong>Otomatik Yedekleme:</strong> Sıranız geldiğinde 1. şampiyonunuz banlanmışsa veya başka bir oyuncu tarafından seçilmişse vakit kaybetmeden 2. şampiyonunuz kilitlenir.
        </div>
      </div>
    </div>

    <!-- TAB 6: DECEIVE GHOST FOCUS -->
    <div class="view-panel" id="view-deceive">
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #c471ed;">👻 Deceive Çevrimdışı / Hayalet Modu</div>
            <div class="card-subtitle">Arkadaş listenizdeki herkese çevrimdışı görünerek tek başınıza rahatça oynayın.</div>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span id="deceiveStatusLabel" style="font-size: 13.5px; font-weight: 900; color: #c471ed;">KAPALI</span>
            <label class="switch">
              <input type="checkbox" id="swOffline2" onchange="onOfflineToggle('swOffline2')">
              <span class="slider pink"></span>
            </label>
          </div>
        </div>

        <div class="info-box" style="background: rgba(196, 113, 237, 0.08); border: 1px solid rgba(196, 113, 237, 0.25); color: #c471ed; margin-top: 10px;">
          💡 <strong>Nasıl Çalışır?</strong> Bu modu açtığınızda Riot sohbet sunucusu durumunuzu 'offline' olarak kilitler. Arkadaşlarınız sizi lobi davetlerinde veya oyunda göremez. Tekrar çevrimiçi olmak için anahtarı kapatmanız yeterlidir.
        </div>
      </div>
    </div>

    <!-- TAB 7: FULL LIVE LOGS -->
    <div class="view-panel" id="view-logs">
      <div class="card" style="background: #080c14; flex: 1; min-height: 0;">
        <div class="terminal-head">
          <span class="terminal-title">📋 CANLI İŞLEM GÜNLÜĞÜ</span>
          <button onclick="clearLogs()" style="background: transparent; border: 1px solid var(--border-subtle); color: #94a3b8; font-size: 12px; font-weight: 700; padding: 6px 14px; border-radius: 6px; cursor: pointer;">Temizle</button>
        </div>
        <div class="terminal-logs" id="terminalLogsFull"></div>
      </div>
    </div>

    <!-- TAB 8: DEVELOPER & CREDITS INFO -->
    <div class="view-panel" id="view-credits">
      <div class="card">
        <div class="card-header-row">
          <div>
            <div class="card-title" style="color: #ffb300;">ℹ️ Geliştirici & Uygulama Bilgileri</div>
            <div class="card-subtitle">LoL AutoPilot PRO • Challenger Tactical Suite</div>
          </div>
          <span id="creditsVersionBadge" style="background: rgba(0, 242, 96, 0.15); border: 1px solid rgba(0, 242, 96, 0.4); color: #00f260; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 800;">v1.0.0</span>
        </div>

        <div class="credits-grid">
          <div class="credits-card">
            <span class="credits-label">👑 GELİŞTİRİCİ</span>
            <span class="credits-value">broadday0909</span>
          </div>

          <div class="credits-card">
            <span class="credits-label">💬 DISCORD TOPLULUĞU</span>
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
              <div class="discord-badge">
                <svg width="18" height="14" viewBox="0 0 127.14 96.36" fill="currentColor"><path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,45.91,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,45.91,96.12,53,91.08,65.69,84.69,65.69Z"/></svg>
                <span>discord.gg/MXXEttvfs</span>
              </div>
              <button class="copy-btn" id="copyBtn" onclick="copyDiscord()">Kopyala</button>
            </div>
          </div>

          <div class="credits-card">
            <span class="credits-label">📦 OTOMATİK GÜNCELLEME</span>
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <span id="updateStatusText" class="credits-value" style="color: #00f260; font-size: 13.5px;">v1.0.0 (En Güncel)</span>
              <button class="copy-btn" id="btnManualCheck" onclick="manualCheckUpdates()" style="background: linear-gradient(135deg, #00f260, #0575e6);">Kontrol Et</button>
            </div>
          </div>

          <div class="credits-card">
            <span class="credits-label">⚡ MOTOR ALTYAPISI</span>
            <span class="credits-value" style="color: #00f2fe; font-size: 13.5px;">Riot LCU & Deceive Protocol</span>
          </div>
        </div>

        <div class="info-box" style="background: rgba(0, 242, 96, 0.06); border: 1px solid rgba(0, 242, 96, 0.25); color: #cbd5e1; margin-top: 14px; line-height: 1.6;">
          🛡️ <strong>Geliştirici Notu & Güvenlik Güvencesi:</strong> Bu yazılım oyun dosyalarına, DirectX işlemlerine veya oyun belleğine (RAM) <u>kesinlikle müdahale etmez</u> ve belleğe kod enjekte etmez (DLL Injection / Memory Hooking içermez). Sadece Riot Games'in resmi istemci arayüzü (LCU REST API) ve Deceive protokolü üzerinden çalışır. Bu sayede Riot Vanguard anti-hile sistemine takılmaz ve ban riski oluşturmaz; <strong>%100 güvenlidir</strong>.
        </div>
      </div>
    </div>

  </div>

  <script>
    let championsMap = {};
    let currentSkinsList = [];

    window.addEventListener('pywebviewready', async () => {
      const data = await window.pywebview.api.get_initial_data();
      championsMap = data.champions || {};
      
      // Populate select dropdowns
      populateSelect('selPrimBan', data.config.primary_ban_champion || 'Zed');
      populateSelect('selSecBan', data.config.secondary_ban_champion || 'Yasuo');
      populateSelect('selPrimPick', data.config.primary_pick_champion || 'Yasuo');
      populateSelect('selSecPick', data.config.secondary_pick_champion || 'Yone');

      // Populate BG Champ select
      populateSelect('selBgChamp', 'Talon');
      onBgChampChange();

      // Set switches
      document.getElementById('swAccept').checked = data.config.auto_accept !== false;
      
      const isOffline = data.config.appear_offline === true;
      document.getElementById('swOffline').checked = isOffline;
      document.getElementById('swOffline2').checked = isOffline;
      updateOfflineUI(isOffline);

      document.getElementById('swKillGame').checked = data.config.auto_close_game !== false;
      
      const isBanActive = data.config.auto_ban !== false;
      document.getElementById('swBan').checked = isBanActive;
      updateBanUI(isBanActive);

      const isPickActive = data.config.auto_pick !== false;
      document.getElementById('swPick').checked = isPickActive;
      updatePickUI(isPickActive);

      // Render stats if available
      if (data.ranked) updateRankedUI(data.ranked);
      if (data.mastery) updateMasteryUI(data.mastery);

      // Replay all buffered initial logs
      if (data.logs && data.logs.length > 0) {
        data.logs.forEach(log => window.onNewLog(log));
      }

      // Status polling every 2.0s
      setInterval(pollStatus, 2000);
      pollStatus();

      // Check for updates in background (1.5s after launch)
      setTimeout(() => checkForUpdates(true), 1500);
    });

    function updateRankedUI(ranked) {
      if (!ranked) return;

      // Solo
      if (ranked.solo) {
        const s = ranked.solo;
        const tierText = s.division ? `${s.tier} ${s.division}` : s.tier;
        document.getElementById('soloTier').textContent = tierText;
        document.getElementById('soloLp').textContent = `${s.lp} LP`;
        document.getElementById('soloWr').textContent = `${s.wins}G ${s.losses}M (%${s.winrate} WR)`;
        if (s.emblemUrl) document.getElementById('soloEmblem').src = s.emblemUrl;
      }

      // Flex
      if (ranked.flex) {
        const f = ranked.flex;
        const tierText = f.division ? `${f.tier} ${f.division}` : f.tier;
        document.getElementById('flexTier').textContent = tierText;
        document.getElementById('flexLp').textContent = `${f.lp} LP`;
        document.getElementById('flexWr').textContent = `${f.wins}G ${f.losses}M (%${f.winrate} WR)`;
        if (f.emblemUrl) document.getElementById('flexEmblem').src = f.emblemUrl;
      }
    }

    function updateMasteryUI(masteries) {
      const grid = document.getElementById('masteryGrid');
      if (!grid || !masteries || masteries.length === 0) return;

      grid.innerHTML = '';
      masteries.forEach(m => {
        const card = document.createElement('div');
        card.className = 'mastery-card';
        card.innerHTML = `
          <img class="mastery-icon" src="${m.iconUrl}" onerror="this.src='https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/profile-icons/29.jpg'" alt="${m.name}" />
          <div class="mastery-info">
            <span class="mastery-name">${m.name}</span>
            <span class="mastery-lvl">⭐ Seviye ${m.level}</span>
            <span class="mastery-pts">${m.formattedPoints} Puan</span>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    async function onBgChampChange() {
      const cname = document.getElementById('selBgChamp').value;
      const cid = championsMap[cname] || 91;
      const skins = await window.pywebview.api.get_champion_skins(cid);
      currentSkinsList = skins || [];

      const skinSel = document.getElementById('selBgSkin');
      skinSel.innerHTML = '';
      currentSkinsList.forEach((s, idx) => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = s.name;
        // Default to Blood Moon Talon if Talon
        if (cname === 'Talon' && s.name.includes('Kanlı Ay')) {
          opt.selected = true;
        }
        skinSel.appendChild(opt);
      });

      onBgSkinChange();
    }

    function onBgSkinChange() {
      const sid = parseInt(document.getElementById('selBgSkin').value);
      const skin = currentSkinsList.find(s => s.id === sid);
      if (skin) {
        document.getElementById('splashPreviewCard').style.backgroundImage = `url('${skin.splashUrl}')`;
        document.getElementById('splashSkinName').textContent = skin.name;
        document.getElementById('splashSkinId').textContent = `Skin ID: ${skin.id}`;
      }
    }

    async function applyProfileBackground() {
      const sid = parseInt(document.getElementById('selBgSkin').value);
      const res = await window.pywebview.api.set_profile_background(sid);
      if (res && res.success) {
        alert('🎉 Profil arka planınız başarıyla güncellendi!');
      } else {
        alert('⚠️ Hata: ' + (res.error || 'İstemciye ulaşılamadı'));
      }
    }

    function updateBanUI(active) {
      const lbl = document.getElementById('banStatusLabel');
      const grp = document.getElementById('banSelectGroup');
      if (lbl) {
        lbl.textContent = active ? 'AKTİF' : 'KAPALI';
        lbl.style.color = active ? '#ff416c' : '#94a3b8';
      }
      if (grp) grp.classList.toggle('disabled', !active);
    }

    function updatePickUI(active) {
      const lbl = document.getElementById('pickStatusLabel');
      const grp = document.getElementById('pickSelectGroup');
      if (lbl) {
        lbl.textContent = active ? 'AKTİF' : 'KAPALI';
        lbl.style.color = active ? '#00f260' : '#94a3b8';
      }
      if (grp) grp.classList.toggle('disabled', !active);
    }

    function updateOfflineUI(active) {
      const lbl = document.getElementById('deceiveStatusLabel');
      if (lbl) {
        lbl.textContent = active ? 'AKTİF' : 'KAPALI';
        lbl.style.color = active ? '#c471ed' : '#94a3b8';
      }
    }

    function onBanToggle() {
      const active = document.getElementById('swBan').checked;
      updateBanUI(active);
      onConfigChange();
    }

    function onPickToggle() {
      const active = document.getElementById('swPick').checked;
      updatePickUI(active);
      onConfigChange();
    }

    function onOfflineToggle(srcId) {
      const active = document.getElementById(srcId).checked;
      document.getElementById('swOffline').checked = active;
      document.getElementById('swOffline2').checked = active;
      updateOfflineUI(active);
      onConfigChange();
    }

    function populateSelect(id, selectedVal) {
      const el = document.getElementById(id);
      if (!el) return;
      el.innerHTML = '';
      const names = Object.keys(championsMap).sort();
      names.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        if (name === selectedVal) opt.selected = true;
        el.appendChild(opt);
      });
    }

    async function onConfigChange() {
      const config = {
        auto_accept: document.getElementById('swAccept').checked,
        appear_offline: document.getElementById('swOffline').checked,
        auto_close_game: document.getElementById('swKillGame').checked,
        auto_ban: document.getElementById('swBan').checked,
        primary_ban_champion: document.getElementById('selPrimBan').value,
        secondary_ban_champion: document.getElementById('selSecBan').value,
        auto_pick: document.getElementById('swPick').checked,
        primary_pick_champion: document.getElementById('selPrimPick').value,
        secondary_pick_champion: document.getElementById('selSecPick').value
      };

      await window.pywebview.api.save_config(config);
    }

    async function pollStatus() {
      try {
        const st = await window.pywebview.api.get_status();
        const dot = document.getElementById('statusDot');
        const headerTxt = document.getElementById('headerStatusText');
        const sidebarTxt = document.getElementById('sidebarStatus');

        const avatarImg = document.getElementById('userAvatarImg');
        const avatarFallback = document.getElementById('userAvatarFallback');
        const summonerName = document.getElementById('summonerName');
        const levelBadge = document.getElementById('summonerLevel');

        if (st.connected) {
          dot.className = 'status-dot online';
          const phaseMap = {
            'None': 'Boşta',
            'Lobby': 'Lobi',
            'Matchmaking': 'Sırada',
            'ReadyCheck': '⚡ Maç Bulundu!',
            'ChampSelect': '🎯 Şampiyon Seçimi',
            'InProgress': '🎮 Oyun Başladı',
            'WaitingForStats': 'Maç Sonu'
          };
          const ph = phaseMap[st.phase] || st.phase;
          const offTag = st.appear_offline ? ' (👻 Çevrimdışı)' : '';
          headerTxt.textContent = `🟢 LoL Bağlı (${ph})${offTag}`;
          sidebarTxt.textContent = `🟢 Bağlandı (${ph})`;
          sidebarTxt.style.color = '#00f260';

          if (st.summoner) {
            summonerName.textContent = st.summoner.name;
            levelBadge.textContent = `Lv. ${st.summoner.level}`;
            levelBadge.style.display = 'inline-block';
            if (st.summoner.iconUrl) {
              avatarImg.src = st.summoner.iconUrl;
              avatarImg.style.display = 'block';
              avatarFallback.style.display = 'none';
            }
          }

          if (st.ranked) updateRankedUI(st.ranked);
          if (st.mastery) updateMasteryUI(st.mastery);

        } else {
          dot.className = 'status-dot';
          headerTxt.textContent = '🔴 İstemci Bekleniyor';
          sidebarTxt.textContent = '🔴 İstemci Bekleniyor';
          sidebarTxt.style.color = '#ff416c';
          summonerName.textContent = 'LoL Client';
          levelBadge.style.display = 'none';
          avatarImg.style.display = 'none';
          avatarFallback.style.display = 'flex';
        }
      } catch (e) {}
    }

    window.onNewLog = function(log) {
      const logsContainer = document.getElementById('terminalLogsFull');
      if (logsContainer) {
        const row = document.createElement('div');
        row.className = 'log-line';
        row.innerHTML = `<span class="log-time">[${log.time}]</span> <span>${log.text}</span>`;
        logsContainer.appendChild(row);

        // Limit to max 100 log lines
        if (logsContainer.children.length > 100) {
          logsContainer.removeChild(logsContainer.firstChild);
        }
        logsContainer.scrollTop = logsContainer.scrollHeight;
      }
    };

    async function clearLogs() {
      const el = document.getElementById('terminalLogsFull');
      if (el) el.innerHTML = '';
      await window.pywebview.api.clear_logs();
    }

    function copyDiscord() {
      navigator.clipboard.writeText('https://discord.gg/MXXEttvfs');
      const btn = document.getElementById('copyBtn');
      btn.textContent = 'Kopyalandı! ✓';
      btn.style.background = '#00f260';
      btn.style.color = '#090d16';
      setTimeout(() => {
        btn.textContent = 'Kopyala';
        btn.style.background = '#5865F2';
        btn.style.color = '#ffffff';
      }, 2000);
    }

    let latestReleaseUrl = 'https://github.com/broadday0909/LolAutoPilot/releases';

    async function checkForUpdates(silent = true) {
      try {
        const res = await window.pywebview.api.check_for_updates();
        if (res && res.has_update) {
          latestReleaseUrl = res.release_url || latestReleaseUrl;
          const banner = document.getElementById('updateBanner');
          const title = document.getElementById('updateBannerTitle');
          const sub = document.getElementById('updateBannerSubtitle');
          if (title) title.textContent = `🚀 Yeni Sürüm Mevcut! (${res.latest_version})`;
          if (sub) sub.textContent = `Mevcut Sürüm: ${res.current_version} • Yeni özellikler ve geliştirmeler yayınlandı.`;
          if (banner) banner.style.display = 'block';

          const updateStatusText = document.getElementById('updateStatusText');
          if (updateStatusText) {
            updateStatusText.textContent = `⚠️ ${res.latest_version} Mevcut!`;
            updateStatusText.style.color = '#ffb300';
          }
        } else {
          if (!silent) {
            const updateStatusText = document.getElementById('updateStatusText');
            if (updateStatusText) {
              updateStatusText.textContent = `✓ ${res.current_version || 'v1.0.0'} (En Güncel)`;
              updateStatusText.style.color = '#00f260';
            }
            alert(`Tebrikler! En güncel sürümü (${res.current_version || 'v1.0.0'}) kullanıyorsunuz.`);
          }
        }
      } catch (e) {
        console.error('Update check failed:', e);
      }
    }

    async function manualCheckUpdates() {
      const btn = document.getElementById('btnManualCheck');
      if (btn) {
        btn.textContent = 'Kontrol Ediliyor...';
        btn.disabled = true;
      }
      await checkForUpdates(false);
      if (btn) {
        btn.textContent = 'Kontrol Et';
        btn.disabled = false;
      }
    }

    function openReleasePage() {
      window.pywebview.api.open_url(latestReleaseUrl);
    }

    function closeUpdateBanner() {
      const banner = document.getElementById('updateBanner');
      if (banner) banner.style.display = 'none';
    }

    function switchView(viewName) {
      document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById(`btn-${viewName}`);
      if (activeBtn) activeBtn.classList.add('active');

      document.querySelectorAll('.view-panel').forEach(panel => panel.classList.remove('active'));
      const targetPanel = document.getElementById(`view-${viewName}`);
      if (targetPanel) targetPanel.classList.add('active');

      const titles = {
        'automations': 'Hızlı Otomasyon Ayarları',
        'stats': '🏆 Canlı İstatistikler & Ustalık Vitrini',
        'profile-bg': '👑 Özel Profil Arka Planı Ayarlayıcı',
        'ban': '🚫 Akıllı Ban Sistemi',
        'pick': '🎯 Akıllı Şampiyon Seçimi',
        'deceive': '👻 Deceive Çevrimdışı Mod',
        'logs': '📋 Canlı İşlem Günlüğü',
        'credits': 'ℹ️ Geliştirici & Uygulama Bilgisi'
      };
      document.getElementById('pageTitle').textContent = titles[viewName] || 'Nexus AutoPilot';
    }
  </script>
</body>
</html>
"""

def start_poller():
    while pilot.is_running:
        try:
            pilot.update_loop()
        except Exception as e:
            gui_log(f"⚠️ Kritik Döngü Hatası: {e}")
        time.sleep(0.8)

def main():
    poller_thread = threading.Thread(target=start_poller, daemon=True)
    poller_thread.start()

    icon_path = os.path.join(BASE_DIR, "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = None

    global window
    window = webview.create_window(
        title="LoL AutoPilot PRO",
        html=HTML_CONTENT,
        js_api=js_api,
        width=960,
        height=620,
        min_size=(900, 580),
        background_color='#0a0e17',
        text_select=False
    )
    webview.start(icon=icon_path)

if __name__ == "__main__":
    main()
