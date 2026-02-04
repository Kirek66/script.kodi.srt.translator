import xbmcgui
import xbmcvfs
import os
import json

from translator import translate_files
from profile_manager import choose_profile
from model_manager import choose_model
from prompt_profiles import DEFAULT_PROFILE

# Wersja skryptu
__version__ = "1.0.1"

ADDON_PATH = xbmcvfs.translatePath(
    "special://home/addons/script.kodi.srt.translator/"
)

SETTINGS_FILE = os.path.join(ADDON_PATH, "settings.json")


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_setting(key, value):
    settings = load_settings()
    settings[key] = value
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def ask_for_api_key(dialog):
    key = dialog.input(
        "Podaj OpenAI API Key",
        type=xbmcgui.INPUT_ALPHANUM
    )
    if key:
        save_setting("api_key", key)
        return key
    return None


def main():
    dialog = xbmcgui.Dialog()
    settings = load_settings()

    # 1. Sprawdzenie API KEY
    api_key = settings.get("api_key")
    if not api_key:
        api_key = ask_for_api_key(dialog)
        if not api_key:
            return

    # 2. Wybór profilu i modelu
    if not choose_profile(dialog):
        if not load_settings().get("profile"):
            save_setting("profile", DEFAULT_PROFILE)
    
    if not choose_model(dialog):
        if not load_settings().get("model"):
            save_setting("model", "gpt-4o")

    # 3. Wybór folderu
    folder = dialog.browse(
        0,
        "Wybierz katalog z plikami SRT",
        "files"
    )
    if not folder:
        return

    # 4. Filtrowanie plików wejściowych
    all_srt_files = [
        f for f in os.listdir(folder)
        if f.lower().endswith(".srt") and not f.lower().endswith(".pl.srt")
    ]

    if not all_srt_files:
        dialog.notification("SRT Translator", "Brak nowych plików do tłumaczenia", xbmcgui.NOTIFICATION_INFO, 3000)
        return

    # 5. Logika sprawdzania istniejących tłumaczeń
    files_to_translate = []
    existing_count = 0

    for f in all_srt_files:
        output_name = f.rsplit('.', 1)[0] + ".PL.srt"
        if os.path.exists(os.path.join(folder, output_name)):
            existing_count += 1
        files_to_translate.append(f)

    if existing_count > 0:
        # Pytamy użytkownika o decyzję
        choice = dialog.yesno(
            f"SRT Translator v{__version__}",
            f"Znaleziono {existing_count} plików, które mają już polskie tłumaczenie.\n"
            "Czy chcesz pominąć istniejące pliki i tłumaczyć tylko brakujące?",
            yeslabel="Pomiń istniejące",
            nolabel="Nadpisz wszystkie"
        )
        
        if choice: # Użytkownik wybrał "Pomiń"
            files_to_translate = [
                f for f in all_srt_files 
                if not os.path.exists(os.path.join(folder, f.rsplit('.', 1)[0] + ".PL.srt"))
            ]

    if not files_to_translate:
        dialog.ok("SRT Translator", "Wszystkie pliki są już przetłumaczone.")
        return

    # 6. Proces tłumaczenia
    progress = xbmcgui.DialogProgress()
    progress.create("Tłumaczenie napisów", "Inicjalizacja...")

    def on_progress(value, text):
        percent = int((value / len(files_to_translate)) * 100)
        progress.update(percent, text)

    try:
        translate_files(api_key, folder, files_to_translate, on_progress)
        progress.close()
        dialog.ok("SRT Translator", f"Zakończono! Przetłumaczono plików: {len(files_to_translate)}")
    except Exception as e:
        progress.close()
        dialog.ok("Błąd", f"Wystąpił problem:\n{str(e)}")


if __name__ == "__main__":
    main()