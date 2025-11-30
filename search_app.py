from parallel_search import run_search

def main():

    root_directory = "C:\\Users\\tomik\\Downloads\\dataText"

    search_text = "pes"

    num_workers = 2

    allowed_extensions = [".txt", ".log", ".md"]

    run_search(root_directory, search_text, num_workers, allowed_extensions)

if __name__ == "__main__":
    main()
