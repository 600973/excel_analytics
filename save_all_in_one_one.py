# PROJECT_ROOT: save_all_in_one_one.py
import os


def is_text_file(filename, allowed_ext):
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_ext


def save_folder_whole(folder, base_name, output_dir):
    folder_path = os.path.join(os.getcwd(), folder)
    allowed_ext = {
        '.py', '.txt', '.md', '.json', '.csv',
        '.ini', '.cfg', '.html', '.js'
    }

    files_list = []
    for root, _, files in os.walk(folder_path):
        for fname in files:
            if fname.startswith(base_name) and fname.endswith('.txt'):
                continue
            if is_text_file(fname, allowed_ext):
                files_list.append(os.path.join(root, fname))

    files_list.sort()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}.txt")

    with open(output_path, "w", encoding="utf-8") as outfile:
        for fpath in files_list:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as infile:
                    content = infile.readlines()
                rel_path = os.path.relpath(fpath, folder_path)
                outfile.write(f"\n\n===== {rel_path} =====\n")
                outfile.writelines(content)
            except Exception as e:
                print(f"Error reading {fpath}: {e}")


def save_root_files(output_dir, output_filename="main.txt"):
    allowed_ext = {
        '.py', '.txt', '.md', '.json', '.csv',
        '.ini', '.cfg', '.html', '.js'
    }
    files_list = [
        f for f in os.listdir(".")
        if os.path.isfile(f) and is_text_file(f, allowed_ext)
    ]
    files_list.sort()
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as outfile:
        for fname in files_list:
            try:
                with open(fname, "r", encoding="utf-8", errors="ignore") as infile:
                    content = infile.readlines()
                outfile.write(f"\n\n===== {fname} =====\n")
                outfile.writelines(content)
            except Exception as e:
                print(f"Error reading {fname}: {e}")


if __name__ == "__main__":
    output_dir = os.path.join(os.getcwd(), "output_gpt")
    for name in ["bots", "mcp_servers", "src", "prompts"]:
        if os.path.exists(name):
            save_folder_whole(name, name, output_dir)
        else:
            print(f"Directory not found: {name}")
    save_root_files(output_dir)
