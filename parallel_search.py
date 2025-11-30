import os
from queue import Queue
from threading import Thread, Lock
def produce_files(root_directory, allowed_extensions, file_queue):


    if not os.path.isdir(root_directory):
        print(f"[PRODUCENT] Složka '{root_directory}' neexistuje.")
        return

    for folder, _, files in os.walk(root_directory):
        for filename in files:
            full_path = os.path.join(folder, filename)

            if allowed_extensions:
                _, ext = os.path.splitext(filename)
                if ext.lower() not in allowed_extensions:
                    continue

            file_queue.put(full_path)

def worker_thread(name, search_text, file_queue, results, results_lock):

    while True:
        file_path = file_queue.get()

        if file_path is None:
            print(f"[{name}] Dostávám sentinel (None), končím.")
            file_queue.task_done()
            break

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
            file_queue.task_done()
            continue

        if matches_in_this_file:
            with results_lock:
                results.append({
                    "type": "matches",
                    "file": file_path,
                    "matches": matches_in_this_file,
                })
            print(f"[{name}] Nalezeny shody v souboru: {file_path}")

        file_queue.task_done()

def run_search(root_directory, search_text, num_workers, allowed_extensions):

    print(f"Složka:        {root_directory}")
    print(f"Hledaný text:  {search_text}")
    print(f"Počet workerů: {num_workers}")

    if not search_text:
        print("Hledaný text je prázdný, program končí.")
        return

    file_queue = Queue()

    results = []
    results_lock = Lock()

    producer = Thread(
        target=produce_files,
        args=(root_directory, allowed_extensions, file_queue),
        name="producer"
    )
    producer.start()

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

    producer.join()

    for _ in workers:
        file_queue.put(None)

    file_queue.join()

    for t in workers:
        t.join()

    print_summary(search_text, results)


def print_summary(search_text, results):
    print("----------------------------------------------")

    print(f" Souhrn výsledků pro hledaný text: '{search_text}'")

    total_matches = 0
    files_with_matches = 0
    print("----------------------------------------------")
    for entry in results:
        if entry["type"] == "error":
            print(f"[CHYBA] Soubor: {entry['file']}")
            print(f"        Zpráva: {entry['message']}")
            print("----------------------------------------------")
        elif entry["type"] == "matches":
            files_with_matches += 1
            print(f"[SOUBOR] {entry['file']}")
            for line_number, line in entry["matches"]:
                total_matches += 1
                print(f"  Řádek {line_number}: {line}")
            print("----------------------------------------------")

    print(f"Počet souborů s výskytem: {files_with_matches}")
    print(f"Celkový počet výskytů:    {total_matches}")
