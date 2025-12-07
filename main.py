import json
import os

from parallel_search import run_search


def load_config(path: str = "config.json") -> dict:
    print(f"[MAIN] Načítám konfiguraci ze souboru: {path}")

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Konfigurační soubor '{path}' neexistuje.")

    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("[MAIN] Konfigurace úspěšně načtena.")
    return config

def main():
    # 1) načtení configu
    try:
        config = load_config("config.json")
    except FileNotFoundError as e:
        print(f"[MAIN] CHYBA: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"[MAIN] CHYBA: config.json není validní JSON: {e}")
        return

    root_directory = config.get("root_directory", ".")
    search_text = config.get("search_text", "")
    num_workers = int(config.get("num_workers", 2))
    allowed_extensions = config.get("allowed_extensions", [".txt"])

    print("[MAIN] Načtené hodnoty z konfigurace:")
    print(f"  root_directory   = {root_directory}")
    print(f"  search_text      = {search_text!r}")
    print(f"  num_workers      = {num_workers}")
    print(f"  allowed_exts     = {allowed_extensions}")
    print("--------------------------------------------------")

    run_search(root_directory, search_text, num_workers, allowed_extensions)

if __name__ == "__main__":
    main()
