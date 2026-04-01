# Kirek SRT Translator GPT (v1.0.3)

W miarę profesjonalne narzędzie do tłumaczenia napisów SRT z języka angielskiego na polski wewnątrz ekosystemu Kodi, wykorzystujące zaawansowane modele językowe OpenAI GPT-4, GPT-5 i GPT-5.4. odatek skupia się na naturalności języka polskiego, poprawnym doborze płci gramatycznej oraz odpowiednim tłumaczeniu idiomów filmowych.
W wersji 1.0.3 dodane zostały jako możliwość wyboru najnowsze modele OpenAI: GPT-5.4, GPT-5.4-mini, GPT-5.4-nano.

## 🚀 Kluczowe Funkcje
- **Profil Profesjonalny:** Unikalny zestaw instrukcji dla AI, który eliminuje kalki językowe (np. nadużywanie zaimków "Ty", "Mój") i dba o filmowy styl dialogów.
- **Kontekst Płci:** Model analizuje poprzednie linie, aby poprawnie dopasować końcówki czasowników (on/ona).
- **Inteligentny Chunking:** Automatyczne dzielenie napisów na optymalne bloki (5000 znaków), co zapewnia duży kontekst dla AI bez ryzyka błędów API.
- **System Resume:** Możliwość wznowienia tłumaczenia od miejsca, w którym zostało przerwane (np. przy braku internetu).
- **Oszczędność Tokenów:** Opcja pomijania plików, które zostały już wcześniej przetłumaczone.

## 🛠 Instalacja
1. Pobierz plik `.zip` z najnowszą wersją dodatku.
2. W Kodi przejdź do **Dodatki** -> **Zainstaluj z pliku zip**.
3. Po instalacji znajdziesz program w sekcji **Dodatki** -> **Programy**.

## ⚙️ Konfiguracja (API Key)
Do działania dodatku wymagany jest własny klucz API od OpenAI:
1. Zaloguj się na [platform.openai.com](https://platform.openai.com/).
2. Utwórz nowy klucz (Secret Key) w sekcji API Keys.
3. Przy pierwszym uruchomieniu dodatku w Kodi zostaniesz poproszony o wpisanie tego klucza. Zostanie on zapisany lokalnie na Twoim urządzeniu.

## 📖 Sposób użycia
1. Uruchom dodatek.
2. Wybierz profil (zalecany: **Profesjonalny (Kontekst i Styl)**).
3. Wybierz model AI.
4. Wskaż folder z plikami `.srt`.
5. Dodatek utworzy nowe pliki z końcówką `.PL.srt` w tym samym folderze.

## ⚠️ Ważne informacje
- **Koszty:** Tłumaczenie odbywa się za pośrednictwem Twojego płatnego konta OpenAI. Koszt tłumaczenia jednego filmu to zazwyczaj kilka-kilkanaście groszy (zależnie od wybranego modelu).
- **Prywatność:** Twój klucz API jest przechowywany wyłącznie lokalnie w folderze `addon_data` Twojego urządzenia Kodi.

---
*Autor: Ireneusz Kutrzuba. Kompatybilność: Kodi 21 (Omega) oraz starsze wersje z Python 3.*