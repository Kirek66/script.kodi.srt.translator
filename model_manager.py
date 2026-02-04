import os
import json
import xbmcvfs
import xbmcgui

# =========================
# DOSTĘPNE MODELE (Stan na 2026)
# =========================

MODELS = {
    "gpt-4o": {
        "name": "GPT-4o (Zalecany)",
        "description": "Najlepszy balans między jakością a szybkością."
    },
    "gpt-4.1": {
        "name": "GPT-4.1 (Premium)",
        "description": "Najwyższa precyzja języka i kontekstu."
    },
    "gpt-5-mini": {
        "name": "GPT-5 Mini (Szybki)",
        "description": "Tani i błyskawiczny, idealny do prostych dialogów."
    }
}

# Zmieniam na GPT-4o jako bezpieczniejszy domyślny, 
# ale możesz tu wpisać dowolny klucz z powyższej listy.
DEFAULT_MODEL = "gpt-4o"

# =========================
# ŚCIEŻKI DANYCH
# =========================

ADDON_DATA_PATH = xbmcvfs.translatePath(
    "special://profile/addon_data/script.kodi.srt.translator/"
)

MODEL_FILE = os.path.join(ADDON_DATA_PATH, "model.json")


def ensure_data_dir():
    """Tworzy katalog danych, jeśli nie istnieje."""
    if not os.path.exists(ADDON_DATA_PATH):
        try:
            os.makedirs(ADDON_DATA_PATH)
        except Exception:
            pass


# =========================
# ODCZYT / ZAPIS MODELU
# =========================

def load_model_key():
    """Odczytuje zapisany klucz modelu z pliku konfiguracyjnego."""
    ensure_data_dir()
    if not os.path.exists(MODEL_FILE):
        return DEFAULT_MODEL
    try:
        with open(MODEL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            key = data.get("model")
            # Sprawdzamy, czy model nadal istnieje w definicjach
            return key if key in MODELS else DEFAULT_MODEL
    except (json.JSONDecodeError, Exception):
        return DEFAULT_MODEL


def save_model_key(model_key):
    """Zapisuje wybrany klucz modelu do pliku."""
    ensure_data_dir()
    try:
        with open(MODEL_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"model": model_key},
                f,
                indent=2,
                ensure_ascii=False
            )
    except Exception:
        pass


# =========================
# GUI – WYBÓR MODELU
# =========================

def choose_model(dialog):
    """Wyświetla okno wyboru modelu w Kodi."""
    keys = list(MODELS.keys())
    # Formatowanie listy do wyświetlenia w GUI
    names = [
        f"{MODELS[k]['name']}\n[COLOR grey]{MODELS[k]['description']}[/COLOR]"
        for k in keys
    ]

    current = load_model_key()
    try:
        preselect = keys.index(current)
    except ValueError:
        preselect = 0

    idx = dialog.select(
        "Wybierz model silnika AI",
        names,
        preselect=preselect
    )

    # Jeśli użytkownik zamknął okno bez wyboru (idx -1)
    if idx == -1:
        return False

    selected = keys[idx]
    save_model_key(selected)
    return True