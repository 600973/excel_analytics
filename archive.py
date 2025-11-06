# PROJECT_ROOT: archive.py
import os
import shutil
from datetime import datetime
import re

# Общий список исключаемых директорий
EXCLUDE_DIRS = ('venv', 'rag_env_new', 'rag_env', 'archive', 'models', 'docs', 'data')


def copy_all_files(src_directory, dest_directory, exclude_dirs=EXCLUDE_DIRS):
    """
    Копирует все файлы из src_directory и всех её поддиректорий в dest_directory,
    сохраняя структуру папок, но исключая указанные директории и их поддиректории.
    """
    exclude_dir_paths = [os.path.join(src_directory, dir_name) for dir_name in exclude_dirs]

    for root, dirs, files in os.walk(src_directory, topdown=True):
        if any(root.startswith(exclude_path) for exclude_path in exclude_dir_paths):
            continue

        for file in files:
            src_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, src_directory)
            dest_path = os.path.join(dest_directory, relative_path)
            os.makedirs(dest_path, exist_ok=True)
            dest_file_path = os.path.join(dest_path, file)
            shutil.copy2(src_file_path, dest_file_path)
            print(f"File {src_file_path} successfully copied to {dest_file_path}.")


def main():
    try:
        current_datetime = datetime.now()
        timestamp = current_datetime.strftime("%Y%m%d_%H%M%S")
        # Новый путь к папке бэкапа
        folder_name = os.path.join(r'E:\excel_analytics\archive\backup', timestamp)
        print(f"Starting to copy files into folder: {folder_name}")
        os.makedirs(folder_name, exist_ok=True)

        current_directory = os.path.dirname(os.path.abspath(__file__))

        # Используем общий список исключаемых директорий
        copy_all_files(current_directory, folder_name)

        print(f"All files successfully copied into folder: {folder_name}")
    except Exception as e:
        print(f"An error occurred while copying files: {e}")


if __name__ == "__main__":
    main()
