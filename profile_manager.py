import os
import json
import xbmcvfs
import xbmcgui

# Importujemy dane z Twojego pliku z profilami
from prompt_profiles import PROFILES, DEFAULT_PROFILE

# =========================
# ŚCIEŻKI DANYCH
# =========================

ADDON_DATA_PATH = xbmcvfs.translatePath(
    "special://profile/addon_data/script.kodi.srt.translator/"
)

PROFILE_FILE = os.path.join(ADDON_DATA_PATH, "profile.json")


def ensure_data_dir():
    """Upewnia się, że folder na dane dodatku istnieje."""
    if not os.path.exists(ADDON_DATA_PATH):
        try:
            os.makedirs(ADDON_DATA_PATH)
        except Exception:
            pass


# =========================
# ODCZYT / ZAPIS PROFILU
# =========================

def load_profile_key():
    """Odczytuje zapisany klucz profilu z pliku JSON."""
    ensure_data_dir()
    if not os.path.exists(PROFILE_FILE):
        return DEFAULT_PROFILE
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            key = data.get("profile")
            # Sprawdzamy, czy profil nadal istnieje w prompt_profiles.py
            return key if key in PROFILES else DEFAULT_PROFILE
    except (json.JSONDecodeError, Exception):
        return DEFAULT_PROFILE


def save_profile_key(profile_key):
    """Zapisuje wybrany klucz profilu do pliku."""
    ensure_data_dir()
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"profile": profile_key},
                f,
                indent=2,
                ensure_ascii=False
            )
    except Exception:
        pass


# =========================
# GUI – WYBÓR PROFILU
# =========================

def choose_profile(dialog):
    """Wyświetla okno wyboru profilu tłumaczenia w Kodi."""
    # Pobieramy klucze profili (np. 'subtitle_edit', 'pro_translator')
    keys = list(PROFILES.keys())
    
    # Tworzymy listę nazw do wyświetlenia w menu (z name zdefiniowanego w prompt_profiles)
    names = [PROFILES[k]["name"] for k in keys]

    current = load_profile_key()
    try:
        preselect = keys.index(current)
    except ValueError:
        preselect = 0

    # Wyświetlenie okna wyboru w Kodi
    idx = dialog.select(
        "Wybierz profil tłumaczenia",
        names,
        preselect=preselect
    )

    # Jeśli użytkownik zamknął okno (ESC / Cancel)
    if idx == -1:
        return False

    selected_key = keys[idx]
    save_profile_key(selected_key)
    return True