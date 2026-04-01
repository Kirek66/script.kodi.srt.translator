import os
import json
import xbmc
import xbmcvfs

from srt_utils import (
    read_srt, write_srt, split_srt_into_chunks,
    has_polish_chars, clean_sdh, remove_song_lines,
    remove_speaker_prefix, clean_markdown, fix_srt_format
)
from openai_client import translate_text
from prompt_profiles import PROFILES, DEFAULT_PROFILE
from profile_manager import load_profile_key
from model_manager import load_model_key


# ─────────────────────────────────────────
# ŚCIEŻKI DANYCH
# ─────────────────────────────────────────

ADDON_DATA_PATH = xbmcvfs.translatePath(
    "special://profile/addon_data/script.kodi.srt.translator/"
)

STATE_FILE = os.path.join(ADDON_DATA_PATH, "resume_state.json")


def log(msg):
    xbmc.log(f"[SRT Translator] {msg}", xbmc.LOGINFO)


def ensure_data_dir():
    if not os.path.exists(ADDON_DATA_PATH):
        try:
            os.makedirs(ADDON_DATA_PATH)
        except Exception:
            pass


# ─────────────────────────────────────────
# STAN (RESUME)
# ─────────────────────────────────────────

def load_state():
    """Wczytuje stan tłumaczenia, by móc wznowić po błędzie."""
    ensure_data_dir()
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    ensure_data_dir()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ─────────────────────────────────────────
# TŁUMACZENIE
# ─────────────────────────────────────────

def translate_files(api_key, folder, srt_files, progress_callback=None):
    """Główna funkcja tłumacząca listę plików SRT."""
    state = load_state()

    profile_key = load_profile_key() or DEFAULT_PROFILE
    profile = PROFILES.get(profile_key) or PROFILES.get(DEFAULT_PROFILE)
    system_prompt = profile["prompt"]

    model_key = load_model_key()
    log(f"Model: {model_key} | Profil: {profile_key}")

    for file_index, filename in enumerate(srt_files, start=1):
        input_path = os.path.join(folder, filename)
        output_path = os.path.join(
            folder,
            filename.rsplit('.', 1)[0] + ".PL.srt"
        )

        original_text = read_srt(input_path)
        if not original_text:
            log(f"Pominięto (pusty plik): {filename}")
            continue

        # Sprawdzenie czy plik nie jest już po polsku
        if has_polish_chars(original_text):
            log(f"Pominięto (wykryto polski): {filename}")
            continue

        # ── Czyszczenie przed tłumaczeniem ──────────────────────
        original_text = clean_sdh(original_text)
        original_text = remove_song_lines(original_text)
        original_text = remove_speaker_prefix(original_text)
        # ────────────────────────────────────────────────────────

        chunks = split_srt_into_chunks(original_text)
        if not chunks:
            log(f"Pominięto (brak chunków po czyszczeniu): {filename}")
            continue

        file_state = state.get(filename, {})
        last_chunk = file_state.get("last_chunk", 0)
        translated_chunks = file_state.get("translated_chunks", [])
        total_chunks = len(chunks)

        log(f"Tłumaczę: {filename} ({total_chunks} chunków, zaczynam od {last_chunk})")

        # Plik już w całości przetłumaczony (resume)
        if last_chunk >= total_chunks > 0:
            final_text = fix_srt_format("\n\n".join(translated_chunks))
            write_srt(output_path, final_text)
            log(f"Gotowe (resume): {filename}")
            continue

        for chunk_index in range(last_chunk, total_chunks):
            translated = None

            for attempt in range(3):
                try:
                    translated = translate_text(
                        api_key,
                        chunks[chunk_index],
                        system_prompt,
                        model_key
                    )
                    if translated:
                        break
                except Exception as e:
                    log(f"BŁĄD API (próba {attempt + 1}/{3}) chunk {chunk_index + 1}: {e}")
                    import time
                    time.sleep(2)

            if not translated:
                raise Exception(
                    f"Błąd API: nie udało się przetłumaczyć fragmentu "
                    f"{chunk_index + 1}/{total_chunks} w pliku {filename}"
                )

            # Czyszczenie markdown z odpowiedzi modelu
            translated_chunks.append(clean_markdown(translated))

            # Zapis stanu po każdym chunku
            state[filename] = {
                "last_chunk": chunk_index + 1,
                "translated_chunks": translated_chunks
            }
            save_state(state)

            if progress_callback:
                progress_callback(
                    (file_index - 1) + ((chunk_index + 1) / total_chunks),
                    f"{filename} ({chunk_index + 1}/{total_chunks})"
                )

        # Finalny zapis z formatowaniem
        final_text = fix_srt_format("\n\n".join(translated_chunks))
        write_srt(output_path, final_text)
        log(f"Zapisano: {output_path}")

        # Usuń stan po sukcesie
        if filename in state:
            del state[filename]
            save_state(state)
