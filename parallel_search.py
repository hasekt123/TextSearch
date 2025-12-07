import os
from queue import Queue
from threading import Thread, Lock


def produce_files(root_directory, allowed_extensions, file_queue):
    """
    PRODUCENT:
    Projde složku a přidá všechny vhodné soubory do fronty.
    """
    print(f"[PRODUCENT] Procházím složku: {root_directory}")

    if not os.path.isdir(root_directory):
        print(f"[PRODUCENT] Složka '{root_directory}' neexistuje.")
        return

    # Přípony pro jistotu na malá písmena
    allowed_extensions = [ext.lower() for ext in allowed_extensions]

    files_count = 0

    for folder, _, files in os.walk(root_directory):
        for filename in files:
            full_path = os.path.join(folder, filename)

            if allowed_extensions:
                _, ext = os.path.splitext(filename)
                if ext.lower() not in allowed_extensions:
                    # soubor s jinou příponou přeskočíme
                    continue

            file_queue.put(full_path)
            files_count += 1
            print(f"[PRODUCENT] Přidávám soubor do fronty: {full_path}")

    print(f"[PRODUCENT] Hotovo – do fronty vloženo {files_count} souborů.")


def worker_thread(name, search_text, file_queue, results, results_lock):
    """
    WORKER (konsument):
    Bere soubory z fronty, hledá v nich text a ukládá výsledky.
    """
    print(f"[{name}] Startuji.")

    while True:
        file_path = file_queue.get()

        # sentinel = signál k ukončení
        if file_path is None:
            print(f"[{name}] Dostávám sentinel (None), končím.")
            file_queue.task_done()
            break

        print(f"[{name}] Zpracovávám soubor: {file_path}")
        matches_in_this_file = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_number, line in enumerate(f, start=1):
                    if search_text in line:
                        matches_in_this_file.append((line_number, line.rstrip("\n")))
        except OSError as e:
            with results_lock:
                results.append({
                    "type": "error",
                    "file": file_path,
                    "message": str(e),
                })
            print(f"[{name}] CHYBA při čtení souboru {file_path}: {e}")
            file_queue.task_done()
            continue

        if matches_in_this_file:
            with results_lock:
                results.append({
                    "type": "matches",
                    "file": file_path,
                    "matches": matches_in_this_file,
                })
            print(f"[{name}] Nalezeny shody v souboru: {file_path} "
                  f"({len(matches_in_this_file)} řádků)")
        else:
            print(f"[{name}] V souboru {file_path} nebyly nalezeny žádné shody.")

        file_queue.task_done()

    print(f"[{name}] Ukončuji se.")


def run_search(root_directory, search_text, num_workers, allowed_extensions):
    """
    Hlavní funkce:
    - vytvoří frontu a sdílená data,
    - spustí PRODUCENTA,
    - spustí WORKERY,
    - počká na dokončení a vypíše souhrn.
    """

    print("==================================================")
    print(" Paralelní vyhledávač textu v souborech – START")
    print("==================================================")
    print(f"[MAIN] Složka:        {root_directory}")
    print(f"[MAIN] Hledaný text:  {search_text!r}")
    print(f"[MAIN] Počet workerů: {num_workers}")
    print(f"[MAIN] Přípony:       {allowed_extensions}")
    print("--------------------------------------------------")

    if not search_text:
        print("[MAIN] Hledaný text je prázdný, program končí.")
        return

    file_queue = Queue()

    results = []
    results_lock = Lock()

    # PRODUCENT
    print("[MAIN] Spouštím producenta...")
    producer = Thread(
        target=produce_files,
        args=(root_directory, allowed_extensions, file_queue),
        name="producer"
    )
    producer.start()

    # WORKERY
    print("[MAIN] Spouštím workery...")
    workers = []
    for i in range(num_workers):
        worker_name = f"worker-{i + 1}"
        t = Thread(
            target=worker_thread,
            args=(worker_name, search_text, file_queue, results, results_lock),
            name=worker_name
        )
        t.start()
        workers.append(t)

    # čekáme na producenta
    producer.join()
    print("[MAIN] Producent skončil – žádné další soubory se přidávat nebudou.")

    # posíláme sentinel pro každého workera
    print("[MAIN] Posílám sentinel hodnoty workerům...")
    for _ in workers:
        file_queue.put(None)

    # čekáme, až fronta zpracuje všechny úkoly
    file_queue.join()
    print("[MAIN] Všechny úkoly ve frontě jsou zpracované.")

    # čekáme na ukončení všech workerů
    for t in workers:
        t.join()
    print("[MAIN] Všechna worker vlákna jsou ukončená.")

    # souhrn
    print_summary(search_text, results)
    print("==================================================")
    print(" Paralelní vyhledávač textu v souborech – KONEC")
    print("==================================================")


def print_summary(search_text, results):
    print("--------------------------------------------------")
    print(f"[SUMMARY] Souhrn výsledků pro hledaný text: {search_text!r}")
    print("--------------------------------------------------")

    total_matches = 0
    files_with_matches = 0

    for entry in results:
        if entry["type"] == "error":
            print(f"[CHYBA] Soubor: {entry['file']}")
            print(f"        Zpráva: {entry['message']}")
            print("--------------------------------------------------")
        elif entry["type"] == "matches":
            files_with_matches += 1
            print(f"[SOUBOR] {entry['file']}")
            for line_number, line in entry["matches"]:
                total_matches += 1
                print(f"  Řádek {line_number}: {line}")
            print("--------------------------------------------------")

    print(f"[SUMMARY] Počet souborů s výskytem: {files_with_matches}")
    print(f"[SUMMARY] Celkový počet výskytů:    {total_matches}")
