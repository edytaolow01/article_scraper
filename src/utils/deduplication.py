import json

def remove_duplicates_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"Unexpected data format in {file_path}")
            return

        seen_urls = set()
        unique_data = []
        removed_urls = []

        for entry in data:
            url = entry.get("url")
            if url:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_data.append(entry)
                else:
                    removed_urls.append(url)

        if removed_urls:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)
            print(f"Removed {len(removed_urls)} duplicates from {file_path}")
            print("Removed URLs:")
            for url in removed_urls:
                print(f"  - {url}")
        else:
            print("No duplicates found.")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    import os

    # Specify the path to the file you want to process
    test_file = os.path.join("data", "raw", "onet_pl_output.json")  # example file path

    remove_duplicates_from_file(test_file)
