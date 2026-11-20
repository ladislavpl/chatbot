import os
import time

from extract import extract_data, extract_files
from load import load_to_chroma
from transform import transform_data


def run_etl_pipeline():
    """Spustí kompletní proces: Extract -> Transform -> Load"""
    print("=" * 50)
    print("Spouštím vektorizaci pro AI Chatbota")
    print("=" * 50)

    start_time = time.time()

    # 1. EXTRACT
    # MySQL je volitelné – spustí se jen pokud je nastavena DB_NAME
    db_enabled = bool(os.getenv("DB_NAME", "").strip())
    # Soubory jsou volitelné – spustí se jen pokud je nastavena FILES_DIR
    files_enabled = bool(os.getenv("FILES_DIR", "").strip())

    if not db_enabled and not files_enabled:
        print("Konec: Není nakonfigurován žádný zdroj dat.")
        print("  → Nastavte DB_NAME pro MySQL, FILES_DIR pro PDF/HTML soubory, nebo oboje.")
        return

    raw_data = extract_data() if db_enabled else []
    file_data = extract_files() if files_enabled else []
    all_data = raw_data + file_data

    if not all_data:
        print("Konec: Nebyla nalezena žádná data.")
        return

    print(f"Celkem zdrojů ke zpracování: {len(all_data)} "
          f"(DB: {len(raw_data)}, soubory: {len(file_data)})")

    # 2. TRANSFORM
    chunks = transform_data(all_data)
    if not chunks:
        print("Konec: Nepodařilo se vytvořit žádné bloky textu.")
        return

    # 3. LOAD
    load_to_chroma(chunks)

    end_time = time.time()
    print("=" * 50)
    print(f"Vektorizace úspěšně dokončena za {end_time - start_time:.2f} sekund!")
    print("=" * 50)

if __name__ == "__main__":
    run_etl_pipeline()
