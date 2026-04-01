import re

MAX_LINE_LENGTH = 38

# ─────────────────────────────────────────
# ROZPOZNAWANIE JĘZYKA
# ─────────────────────────────────────────

def has_polish_chars(text):
    """Zwraca True jeśli tekst zawiera polskie znaki – plik już przetłumaczony."""
    return any(c in text for c in "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")


# ─────────────────────────────────────────
# CZYSZCZENIE TEKSTU
# ─────────────────────────────────────────

def clean_markdown(text):
    """Usuwa znaczniki markdown (```srt ... ```) które model może dodać do odpowiedzi."""
    return text.replace("```srt", "").replace("```", "").strip()


def strip_html(text):
    """Usuwa tagi HTML/XML z tekstu (np. <i>, <b>, <font>)."""
    return re.sub(r'<[^>]*>', '', text)


def clean_sdh(text):
    """
    Usuwa opisy dla niesłyszących (SDH):
    - [MUZYKA W TLE], [ŚMIECH], (puka do drzwi) itp.
    """
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\(.*?\)", "", text)
    return text.strip()


def remove_song_lines(text):
    """
    Usuwa linie z tekstami piosenek:
    - linie zawierające symbole muzyczne ♪ ♫ ♬ ♩
    - linie zaczynające się od #
    - linie CAPS w nawiasach okrągłych np. (SINGING)
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if re.search(r"[♪♫♬♩]", stripped):
            continue
        if stripped.startswith("#"):
            continue
        if re.match(r"^\(.*\)$", stripped) and stripped.upper() == stripped:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def remove_speaker_prefix(text):
    """
    Usuwa prefiksy mówiącego:
    - "JOHN: " (caps)
    - "Anna: " (imię z dużej litery)
    """
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = re.sub(r"^[A-ZŁŚŻŹĆŃÓ][A-Za-zŁŚŻŹĆŃÓąćęłńóśźż\-']{1,20}:\s*", "", line)
        line = re.sub(r"^[A-Z ]{2,20}:\s*", "", line)
        cleaned.append(line)
    return "\n".join(cleaned)


def clean_empty_dialogues(text):
    """
    Usuwa bloki SRT które:
    - zawierają adresy www / .org (reklamy napisane w napisach)
    - nie zawierają żadnej litery ani cyfry po oczyszczeniu z HTML
    """
    blocks = text.strip().split("\n\n")
    cleaned_blocks = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            body = "\n".join(lines[2:])
            if "www." in body.lower() or ".org" in body.lower():
                continue
            if re.search(r'[a-zA-Z0-9]', strip_html(body)):
                cleaned_blocks.append(block)
    return "\n\n".join(cleaned_blocks)


# ─────────────────────────────────────────
# ZAWIJANIE LINII
# ─────────────────────────────────────────

def wrap_line(line, max_len=MAX_LINE_LENGTH):
    """
    Dzieli długą linię napisów na maksymalnie 2 linie po max_len znaków.
    Zasady:
    - nie zostawia jednoliterowych sierot (i, a, o, u, w, z) na końcu linii
    - preferuje cięcie przy spójnikach (że, ale, bo, więc...)
    - preferuje cięcie przy przecinku
    - fallback: twarde zawijanie słowo po słowie
    """
    words = line.split()
    if not words:
        return line

    full_text = " ".join(words)
    if len(full_text) <= max_len:
        return full_text

    preferred_words = {
        "że", "ale", "bo", "więc", "żeby",
        "który", "która", "które", "którzy",
        "gdy", "kiedy", "jeśli", "choć", "ponieważ"
    }
    orphans = {"i", "a", "o", "u", "w", "z"}

    best_split = None
    best_balance = None

    for i in range(1, len(words)):
        left_words = words[:i]
        last_word_clean = left_words[-1].lower().strip(",.!?;:")

        if last_word_clean in orphans:
            continue

        left = " ".join(left_words)
        right = " ".join(words[i:])

        if len(left) <= max_len and len(right) <= max_len:
            score = abs(len(left) - len(right))
            if left.endswith(","):
                score -= 5
            if last_word_clean in preferred_words:
                score -= 3
            if best_split is None or score < best_balance:
                best_split = (left, right)
                best_balance = score

    if best_split:
        return best_split[0] + "\n" + best_split[1]

    # Fallback: twarde zawijanie
    result_lines = []
    current = ""
    for w in words:
        if not current:
            current = w
        elif len(current) + len(w) + 1 <= max_len:
            current += " " + w
        else:
            last_word_clean = current.split()[-1].lower().strip(",.!?;:")
            if last_word_clean in orphans and result_lines:
                prev_words = current.split()
                orphan = prev_words.pop()
                result_lines.append(" ".join(prev_words))
                current = orphan + " " + w
            else:
                result_lines.append(current)
                current = w
        if len(result_lines) == 2:
            break

    if current and len(result_lines) < 2:
        result_lines.append(current)

    return "\n".join(result_lines[:2])


# ─────────────────────────────────────────
# FORMATOWANIE SRT
# ─────────────────────────────────────────

def fix_srt_format(text):
    """
    Porządkuje przetłumaczony tekst SRT:
    - usuwa tagi HTML
    - usuwa puste bloki
    - poprawia '--' na '...'
    - zawija linie do MAX_LINE_LENGTH znaków
    - renumeruje bloki od 1
    """
    text = strip_html(text)
    blocks = text.split("\n\n")
    fixed = []
    counter = 1

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        num, time = lines[0], lines[1]
        body = " ".join(lines[2:])

        # Pomijamy bloki bez treści
        if not re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ0-9]', body):
            continue

        body = clean_sdh(body)
        body = body.replace("--", "...")
        body = re.sub(r"—+", "...", body)
        body = re.sub(r"\.{4,}", "...", body)
        body = wrap_line(body.strip())

        if not body.strip():
            continue

        fixed.append("\n".join([str(counter), time] + body.split("\n")))
        counter += 1

    return "\n\n".join(fixed)


# ─────────────────────────────────────────
# ODCZYT / ZAPIS PLIKU SRT
# ─────────────────────────────────────────

def read_srt(path):
    """Odczytuje plik SRT z obsługą BOM (UTF-8-SIG) i normalizacją końców linii."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            return content.replace('\r\n', '\n').strip()
    except Exception:
        return ""


def write_srt(path, content):
    """Zapisuje napisy SRT w UTF-8."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
    except Exception:
        pass


# ─────────────────────────────────────────
# PODZIAŁ NA CHUNKI
# ─────────────────────────────────────────

def split_srt_into_chunks(srt_text, max_chars=5000):
    """
    Dzieli napisy na paczki do wysłania do API.
    Nie rozbija pojedynczych bloków SRT.
    Przed podziałem czyści tekst z reklam i pustych bloków.
    """
    if not srt_text:
        return []

    srt_text = clean_empty_dialogues(srt_text)
    blocks = srt_text.strip().split("\n\n")

    chunks = []
    current_blocks = []
    current_length = 0

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if current_length + len(block) + 2 > max_chars and current_blocks:
            chunks.append("\n\n".join(current_blocks))
            current_blocks = [block]
            current_length = len(block)
        else:
            current_blocks.append(block)
            current_length += len(block) + 2

    if current_blocks:
        chunks.append("\n\n".join(current_blocks))

    return chunks
