import base64
import os
import sys
import time
import json
import logging
import psutil
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("lcu_core")

def get_config_path() -> str:
    """Returns permanent, user-specific config file path in AppData."""
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    app_dir = os.path.join(appdata, "LoL_AutoPilot")
    try:
        os.makedirs(app_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(app_dir, "config.json")

CONFIG_FILE = get_config_path()

DEFAULT_CONFIG = {
    "auto_accept": True,
    "auto_ban": True,
    "primary_ban_champion": "Zed",
    "secondary_ban_champion": "Yasuo",
    "auto_pick": True,
    "primary_pick_champion": "Yasuo",
    "secondary_pick_champion": "Yone",
    "auto_close_game": True,
    "appear_offline": False,
    "delay_pick_seconds": 0.5
}


class LCUAutoPilot:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or print
        self.port = None
        self.auth_token = None
        self.auth_header = None
        self.is_connected = False
        self.current_phase = "None"
        
        self.config = self.load_config()
        self.champions_map = self.load_champions()
        # Case-insensitive lookup map
        self.champions_lower = {k.strip().lower(): v for k, v in self.champions_map.items()}
        self.id_to_name = {v: k for k, v in self.champions_map.items()}
        
        self.handled_action_ids = set()
        self.game_killed_recently = False
        self.summoner_info = None
        self.is_running = True

    def log(self, text: str):
        if self.log_callback:
            self.log_callback(text)

    def load_config(self) -> dict:
        config_path = get_config_path()
        migrated = False
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    
                    if "ban_champion" in data and "primary_ban_champion" not in data:
                        data["primary_ban_champion"] = data["ban_champion"]
                        migrated = True
                    if "pick_champion" in data and "primary_pick_champion" not in data:
                        data["primary_pick_champion"] = data["pick_champion"]
                        migrated = True
                    
                    cfg.update(data)
                    cfg.pop("auto_freeze_game", None)
                    cfg.pop("freeze_duration_seconds", None)
                    
                    if migrated:
                        try:
                            with open(config_path, "w", encoding="utf-8") as fw:
                                json.dump(cfg, fw, ensure_ascii=False, indent=2)
                        except Exception:
                            pass
                    return cfg
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        config_path = get_config_path()
        try:
            self.config.pop("auto_freeze_game", None)
            self.config.pop("freeze_duration_seconds", None)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"Ayar kaydetme hatası: {e}")

    def load_champions(self) -> dict:
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        champ_file = os.path.join(base_dir, "champions.json")
        if os.path.exists(champ_file):
            try:
                with open(champ_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"Yasuo": 157, "Zed": 238, "Aatrox": 266, "Malphite": 54, "Darius": 122, "Jinx": 222, "Yone": 777}

    def get_champion_id(self, name: str) -> int:
        """Case-insensitive champion ID resolver."""
        if not name:
            return 0
        if name in self.champions_map:
            return self.champions_map[name]
        return self.champions_lower.get(str(name).strip().lower(), 0)

    def find_lcu(self) -> bool:
        """Locates LCU connection using cmdline or lockfile."""
        port = None
        token = None

        # Method 1: Inspect process cmdline
        try:
            for proc in psutil.process_iter(['name', 'cmdline', 'exe']):
                pname = proc.info.get('name', '') or ''
                if 'LeagueClientUx.exe' in pname or 'LeagueClient.exe' in pname:
                    cmdline = proc.info.get('cmdline') or []
                    for arg in cmdline:
                        if arg.startswith('--app-port='):
                            port = int(arg.split('=')[1])
                        elif arg.startswith('--remoting-auth-token='):
                            token = arg.split('=')[1]
                    
                    if not (port and token):
                        try:
                            pexe = proc.info.get('exe') or ''
                            if pexe:
                                pdir = os.path.dirname(pexe)
                                lock_path = os.path.join(pdir, "lockfile")
                                if os.path.exists(lock_path):
                                    with open(lock_path, "r", encoding="utf-8") as lf:
                                        parts = lf.read().strip().split(":")
                                        if len(parts) >= 4:
                                            port = int(parts[2])
                                            token = parts[3]
                        except Exception:
                            pass

                    if port and token:
                        break
        except Exception:
            pass

        # Method 2: Common lockfile paths
        if not (port and token):
            common_paths = [
                r"C:\Riot Games\League of Legends\lockfile",
                r"D:\Riot Games\League of Legends\lockfile",
                r"E:\Riot Games\League of Legends\lockfile",
                r"C:\Program Files\Riot Games\League of Legends\lockfile"
            ]
            for cp in common_paths:
                if os.path.exists(cp):
                    try:
                        with open(cp, "r", encoding="utf-8") as lf:
                            parts = lf.read().strip().split(":")
                            if len(parts) >= 4:
                                port = int(parts[2])
                                token = parts[3]
                                break
                    except Exception:
                        pass

        if port and token:
            self.port = port
            self.auth_token = token
            raw_auth = f"riot:{token}".encode('ascii')
            self.auth_header = f"Basic {base64.b64encode(raw_auth).decode('ascii')}"
            if not self.is_connected:
                self.log(f"🟢 LoL İstemcisine Bağlandı! (Port: {port})")
            self.is_connected = True
            return True

        if self.is_connected:
            self.log("🔴 LoL İstemci Bağlantısı Kesildi.")
        self.is_connected = False
        return False

    def request(self, method: str, endpoint: str, json_data: dict = None):
        """Performs LCU REST API requests."""
        if not self.is_connected or not self.port:
            return None
        url = f"https://127.0.0.1:{self.port}{endpoint}"
        headers = {
            "Authorization": self.auth_header,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.request(method, url, headers=headers, json=json_data, verify=False, timeout=3.5)
            if resp.status_code in [200, 201, 204]:
                return resp.json() if resp.text else {}
            return None
        except requests.exceptions.Timeout:
            return None
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
            if self.is_connected:
                self.log("🔴 LoL İstemci Bağlantısı Kesildi.")
            self.is_connected = False
            return None
        except Exception:
            return None

    def get_summoner_info(self) -> dict:
        """Fetches current summoner name, level, and icon from LCU."""
        if not self.is_connected:
            return None
        res = self.request("GET", "/lol-summoner/v1/current-summoner")
        if res and isinstance(res, dict) and "displayName" in res:
            name = res.get("gameName") or res.get("displayName", "Sihirdar")
            tag = res.get("tagLine", "")
            full_name = f"{name} #{tag}" if tag else name
            icon_id = res.get("profileIconId", 29)
            level = res.get("summonerLevel", 30)
            self.summoner_info = {
                "name": full_name,
                "displayName": name,
                "tagLine": tag,
                "iconId": icon_id,
                "iconUrl": f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/profile-icons/{icon_id}.jpg",
                "level": level
            }
            return self.summoner_info
        return self.summoner_info

    def get_ranked_stats(self) -> dict:
        """Fetches live Solo/Duo and Flex ranked stats."""
        if not self.is_connected:
            return None
        res = self.request("GET", "/lol-ranked/v1/current-ranked-stats")
        if not res or not isinstance(res, dict) or "queues" not in res:
            return None
        
        stats = {
            "solo": {"tier": "UNRANKED", "division": "", "lp": 0, "wins": 0, "losses": 0, "winrate": 0},
            "flex": {"tier": "UNRANKED", "division": "", "lp": 0, "wins": 0, "losses": 0, "winrate": 0}
        }

        for q in res.get("queues", []):
            qtype = q.get("queueType")
            tier = q.get("tier", "UNRANKED")
            div = q.get("division", "")
            if div == "NA":
                div = ""
            lp = q.get("leaguePoints", 0)
            wins = q.get("wins", 0)
            losses = q.get("losses", 0)
            total = wins + losses
            wr = round((wins / total) * 100, 1) if total > 0 else 0

            tier_str = tier.upper() if tier else "UNRANKED"
            data_dict = {
                "tier": tier_str,
                "division": div,
                "lp": lp,
                "wins": wins,
                "losses": losses,
                "winrate": wr,
                "emblemUrl": f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/images/{tier.lower()}.png" if tier_str != "UNRANKED" else ""
            }

            if qtype == "RANKED_SOLO_5x5":
                stats["solo"] = data_dict
            elif qtype == "RANKED_FLEX_SR":
                stats["flex"] = data_dict

        return stats

    def get_top_masteries(self, limit: int = 6) -> list:
        """Fetches player's top champion mastery stats."""
        if not self.is_connected:
            return []
        mastery = self.request("GET", "/lol-champion-mastery/v1/local-player/champion-mastery")
        if not isinstance(mastery, list):
            return []
        
        top = []
        for m in mastery[:limit]:
            cid = m.get("championId")
            cname = self.id_to_name.get(cid, f"ID: {cid}")
            top.append({
                "championId": cid,
                "name": cname,
                "level": m.get("championLevel", 1),
                "points": m.get("championPoints", 0),
                "formattedPoints": f"{m.get('championPoints', 0):,}".replace(",", "."),
                "iconUrl": f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/{cid}.png"
            })
        return top

    def get_champion_skins(self, champion_id: int) -> list:
        """Fetches all skin names, IDs, and valid HD splash URLs for a champion."""
        if not self.is_connected:
            return []
        res = self.request("GET", f"/lol-game-data/assets/v1/champions/{champion_id}.json")
        if res and isinstance(res, dict) and "skins" in res:
            skins = []
            for s in res["skins"]:
                sid = s.get("id")
                sname = s.get("name")
                splash_path = s.get("splashPath") or s.get("uncenteredSplashPath") or ""
                if splash_path:
                    clean = splash_path.replace("/lol-game-data/assets/", "").lower()
                    splash_url = f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/{clean}"
                else:
                    splash_url = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champion_id}_{sid % 1000}.jpg"
                
                skins.append({
                    "id": sid,
                    "name": sname,
                    "splashUrl": splash_url
                })
            return skins
        return []

    def set_profile_background(self, skin_id: int) -> dict:
        """Updates summoner client profile background to any skin ID."""
        if not self.is_connected:
            return {"success": False, "error": "İstemciye bağlı değil"}
        res = self.request("POST", "/lol-summoner/v1/current-summoner/summoner-profile", {"key": "backgroundSkinId", "value": int(skin_id)})
        if res is not None:
            self.log(f"👑 [PROFİL ARKA PLANI] Profil arka planınız güncellendi! (Skin ID: {skin_id})")
            return {"success": True}
        return {"success": False, "error": "Riot API isteği reddetti"}

    def auto_accept(self):
        res = self.request("POST", "/lol-matchmaking/v1/ready-check/accept")
        if res is not None:
            self.log("⚡ [OTOMATİK KABUL] Maç bulundu ve anında kabul edildi!")

    def handle_champ_select(self):
        session = self.request("GET", "/lol-champ-select/v1/session")
        if not session or not isinstance(session, dict):
            return

        local_cell_id = session.get("localPlayerCellId", -1)
        actions = session.get("actions", [])
        my_team = session.get("myTeam", [])
        bans = session.get("bans", {})

        teammate_intents = set()
        for member in my_team:
            if member.get("cellId") != local_cell_id:
                intent_id = member.get("championPickIntent", 0)
                if intent_id and intent_id > 0:
                    teammate_intents.add(intent_id)
                champ_id = member.get("championId", 0)
                if champ_id and champ_id > 0:
                    teammate_intents.add(champ_id)

        banned_ids = set()
        for b in bans.get("myTeamBans", []) + bans.get("theirTeamBans", []):
            if b > 0:
                banned_ids.add(b)

        prim_ban_name = self.config.get("primary_ban_champion", "Zed")
        sec_ban_name = self.config.get("secondary_ban_champion", "Yasuo")
        prim_ban_id = self.get_champion_id(prim_ban_name)
        sec_ban_id = self.get_champion_id(sec_ban_name)

        prim_pick_name = self.config.get("primary_pick_champion", "Yasuo")
        sec_pick_name = self.config.get("secondary_pick_champion", "Yone")
        prim_pick_id = self.get_champion_id(prim_pick_name)
        sec_pick_id = self.get_champion_id(sec_pick_name)

        for action_group in actions:
            for action in action_group:
                act_id = action.get("id")
                actor_id = action.get("actorCellId")
                act_type = action.get("type")
                is_in_progress = action.get("isInProgress", False)
                completed = action.get("completed", False)

                if actor_id == local_cell_id and is_in_progress and not completed:
                    if act_id in self.handled_action_ids:
                        continue

                    if act_type == "ban" and self.config.get("auto_ban", True):
                        target_ban_id = prim_ban_id
                        target_ban_name = prim_ban_name
                        
                        if prim_ban_id in teammate_intents:
                            self.log(f"⚠️ [BAN UYARISI] Ana banın '{prim_ban_name}' takım arkadaşın tarafından gösteriliyor! Banlanmayacak.")
                            if sec_ban_id > 0 and sec_ban_id not in teammate_intents and sec_ban_id not in banned_ids:
                                target_ban_id = sec_ban_id
                                target_ban_name = sec_ban_name
                                self.log(f"🔄 [YEDEK BAN] Yedek ban şampiyonuna geçildi: '{sec_ban_name}'")
                            else:
                                target_ban_id = None
                        elif prim_ban_id in banned_ids:
                            self.log(f"ℹ️ [BAN UYARISI] '{prim_ban_name}' zaten başkası tarafından banlanmış.")
                            if sec_ban_id > 0 and sec_ban_id not in teammate_intents and sec_ban_id not in banned_ids:
                                target_ban_id = sec_ban_id
                                target_ban_name = sec_ban_name
                                self.log(f"🔄 [YEDEK BAN] Yedek ban şampiyonuna geçildi: '{sec_ban_name}'")
                            else:
                                target_ban_id = None

                        if target_ban_id and target_ban_id > 0:
                            self.log(f"🚫 [OTOMATİK BAN] '{target_ban_name}' banlanıyor ve kilitleniyor...")
                            patch_res = self.request(
                                "PATCH",
                                f"/lol-champ-select/v1/session/actions/{act_id}",
                                {"championId": target_ban_id, "completed": True}
                            )
                            if patch_res is not None:
                                self.log(f"✅ [BAŞARILI] '{target_ban_name}' başarıyla banlandı!")
                                self.handled_action_ids.add(act_id)
                        else:
                            self.log("⚠️ [BAN BİLGİSİ] Uygun ban şampiyonu bulunamadı veya ikisi de takım arkadaşı tarafından seçilmiş.")
                            self.handled_action_ids.add(act_id)

                    elif act_type == "pick" and self.config.get("auto_pick", True):
                        target_pick_id = prim_pick_id
                        target_pick_name = prim_pick_name
                        
                        if prim_pick_id in banned_ids:
                            self.log(f"⚠️ [SEÇİM UYARISI] Ana seçimin '{prim_pick_name}' banlanmış!")
                            if sec_pick_id > 0 and sec_pick_id not in banned_ids:
                                target_pick_id = sec_pick_id
                                target_pick_name = sec_pick_name
                                self.log(f"🔄 [YEDEK SEÇİM] Yedek şampiyonuna geçildi: '{sec_pick_name}'")
                            else:
                                target_pick_id = None

                        if target_pick_id and target_pick_id > 0:
                            self.log(f"🎯 [OTOMATİK SEÇİM] '{target_pick_name}' seçiliyor ve kilitleniyor...")
                            patch_res = self.request(
                                "PATCH",
                                f"/lol-champ-select/v1/session/actions/{act_id}",
                                {"championId": target_pick_id, "completed": True}
                            )
                            if patch_res is not None:
                                self.log(f"✅ [BAŞARILI] '{target_pick_name}' başarıyla kilitlendi!")
                                self.handled_action_ids.add(act_id)
                        else:
                            self.log("⚠️ [SEÇİM BİLGİSİ] Uygun seçim şampiyonu bulunamadı veya ikisi de banlanmış.")
                            self.handled_action_ids.add(act_id)

    def check_and_kill_game_process(self):
        """Terminates League of Legends.exe once when game launches."""
        if not self.config.get("auto_close_game", True):
            return

        try:
            for proc in psutil.process_iter(['name', 'pid']):
                pname = proc.info.get('name', '') or ''
                if pname == 'League of Legends.exe':
                    if not self.game_killed_recently:
                        self.log("🚨 [OYUN BAŞLADI] 'League of Legends.exe' tespit edildi! Oyun kapatılıyor...")
                        try:
                            proc.kill()
                            self.log("✅ [BAŞARILI] 'League of Legends.exe' kapatıldı! LoL İstemcisi açık bırakıldı.")
                            self.game_killed_recently = True
                        except Exception as e:
                            self.log(f"Kapatma hatası: {e}")
                    return
        except Exception:
            pass

    def set_offline_mode(self, enabled: bool):
        """Sets summoner chat presence to offline (Deceive mode) or back to online."""
        if not self.is_connected:
            return
        availability = "offline" if enabled else "chat"
        res = self.request("PUT", "/lol-chat/v1/me", {"availability": availability})
        if res is not None:
            if enabled:
                self.log("👻 [DECEIVE / ÇEVRİMDAŞI] Durumunuz 'Çevrimdışı' yapıldı. Arkadaşlarınız sizi kapalı görecek.")
            else:
                self.log("🟢 [ÇEVRİMİÇİ] Durumunuz 'Çevrimiçi' olarak güncellendi.")

    def update_loop(self):
        if not self.find_lcu():
            return

        # Enforce Appear Offline if enabled
        if self.config.get("appear_offline", False):
            me = self.request("GET", "/lol-chat/v1/me")
            if me and isinstance(me, dict) and me.get("availability") not in ["offline", "mobile"]:
                self.request("PUT", "/lol-chat/v1/me", {"availability": "offline"})

        self.check_and_kill_game_process()

        phase_res = self.request("GET", "/lol-gameflow/v1/gameflow-phase")
        if phase_res is not None:
            phase = phase_res if isinstance(phase_res, str) else phase_res.get("text", "None") if isinstance(phase_res, dict) else "None"
            phase = phase.strip('"')
            
            if phase != self.current_phase:
                self.current_phase = phase
                self.log(f"ℹ️ Durum Değişti: {phase}")

                # Reset match triggers on lobby / matchmaking / idle
                if phase in ["None", "Lobby", "Matchmaking"]:
                    self.game_killed_recently = False

            if phase == "ReadyCheck" and self.config.get("auto_accept", True):
                self.auto_accept()
            elif phase == "ChampSelect":
                self.handle_champ_select()
            elif phase == "InProgress":
                self.check_and_kill_game_process()
            else:
                self.handled_action_ids.clear()
