import os
import json
import xbmcvfs

from srt_utils import read_srt, write_srt, split_srt_into_chunks
from openai_client import translate_text
from prompt_profiles import PROFILES, DEFAULT_PROFILE
from profile_manager import load_profile_key
from model_manager import load_model_key


# =========================
# ŚCIEŻKI DANYCH
# =========================

# Ścieżka do danych dodatku wewnątrz profilu użytkownika Kodi
ADDON_DATA_PATH = xbmcvfs.translatePath(
    "special://profile/addon_data/script.kodi.srt.translator/"
)

STATE_FILE = os.path.join(ADDON_DATA_PATH, "resume_state.json")


def ensure_data_dir():
    """Upewnia się, że folder na dane dodatku istnieje."""
    if not os.path.exists(ADDON_DATA_PATH):
        try:
            os.makedirs(ADDON_DATA_PATH)
        except Exception:
            pass


# =========================
# STAN (RESUME)
# =========================

def load_state():
    """Wczytuje stan tłumaczenia, aby móc wznowić pracę po błędzie."""
    ensure_data_dir()
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    """Zapisuje aktualny postęp do pliku json."""
    ensure_data_dir()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# =========================
# TŁUMACZENIE
# =========================

def translate_files(api_key, folder, srt_files, progress_callback=None):
    """Główna funkcja zarządzająca procesem tłumaczenia plików."""
    state = load_state()

    # Pobieranie profilu z zabezpieczeniem (jeśli klucz nie istnieje, użyj domyślnego)
    profile_key = load_profile_key() or DEFAULT_PROFILE
    profile = PROFILES.get(profile_key) or PROFILES.get(DEFAULT_PROFILE)
    system_prompt = profile["prompt"]

    model_key = load_model_key()

    for file_index, filename in enumerate(srt_files, start=1):
        input_path = os.path.join(folder, filename)
        # Tworzenie nazwy pliku wyjściowego: film.srt -> film.PL.srt
        output_path = os.path.join(
            folder,
            filename.rsplit('.', 1)[0] + ".PL.srt"
        )

        original_text = read_srt(input_path)
        if not original_text:
            continue

        chunks = split_srt_into_chunks(original_text)
        
        file_state = state.get(filename, {})
        last_chunk = file_state.get("last_chunk", 0)
        translated_chunks = file_state.get("translated_chunks", [])

        total_chunks = len(chunks)

        # Jeśli plik został już w całości przetłumaczony wcześniej (z sesji resume)
        if last_chunk >= total_chunks and total_chunks > 0:
            final_text = "\n\n".join(translated_chunks)
            write_srt(output_path, final_text)
            continue

        for chunk_index in range(last_chunk, total_chunks):
            # Wywołanie API tłumacza
            translated = translate_text(
                api_key,
                chunks[chunk_index],
                system_prompt,
                model_key
            )

            if translated:
                translated_chunks.append(translated)
                
                # Aktualizacja stanu po każdym poprawnym fragmencie
                state[filename] = {
                    "last_chunk": chunk_index + 1,
                    "translated_chunks": translated_chunks
                }
                save_state(state)
            else:
                # Jeśli API zwróci pusty wynik (błąd), przerywamy pracę nad tym plikiem
                # Błąd zostanie obsłużony w main.py przez try...except
                raise Exception(f"Błąd API podczas tłumaczenia fragmentu {chunk_index + 1} w pliku {filename}")

            if progress_callback:
                progress_callback(
                    (file_index - 1) + ((chunk_index + 1) / total_chunks),
                    f"{filename} ({chunk_index + 1}/{total_chunks})"
                )

        # Łączenie przetłumaczonych fragmentów i zapis finalny
        final_text = "\n\n".join(translated_chunks)
        write_srt(output_path, final_text)

        # Usunięcie stanu po udanym zakończeniu tłumaczenia pliku
        if filename in state:
            del state[filename]
            save_state(state)