#!/usr/bin/env python3
# PROJECT_ROOT: project_header.py
# -*- coding: utf-8 -*-
"""
Скрипт для добавления/обновления заголовков в Python файлах
Добавляет комментарий с путем к корню проекта в первую строку файлов
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict
import argparse
import time
from tqdm import tqdm

# ===============================================
# НАСТРОЙКИ
# ===============================================

# Паттерны для определения корня проекта
PROJECT_ROOT_INDICATORS = [
    'setup.py', 'pyproject.toml', 'requirements.txt',
    '.git', '.gitignore', 'README.md', 'main.py',
    'manage.py', 'app.py', 'config.py'
]

# Форматы комментариев для поиска существующих заголовков
HEADER_PATTERNS = [
    r'# PROJECT_ROOT:\s*(.+)',
    r'# ROOT:\s*(.+)',
    r'# PATH:\s*(.+)',
]

# Файлы для исключения из обработки
EXCLUDE_FILES = {
    '__init__.py',
    'setup.py',
    'conftest.py',
}

# Папки для исключения из обработки
EXCLUDE_DIRECTORIES = {
    '.git', '.svn', 'node_modules', 'venv', '.venv',
    '__pycache__', 'build', 'dist', '.tox',
    'rag_env_new', 'archive', 'to do', 'models',
}


# ===============================================
# ОСНОВНОЙ КЛАСС
# ===============================================

class ProjectHeaderManager:
    """Менеджер заголовков файлов проекта"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.project_root = self._find_project_root()

        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _find_project_root(self) -> Path:
        """Находит корень проекта по индикаторам"""
        current = self.project_path

        while current != current.parent:
            # Проверяем наличие индикаторов корня
            for indicator in PROJECT_ROOT_INDICATORS:
                if (current / indicator).exists():
                    return current
            current = current.parent

        # Если не найден, используем переданный путь
        return self.project_path

    def find_python_files(self) -> List[Path]:
        """Находит все Python и текстовые файлы для обработки"""
        target_files = []

        for ext in ['*.py', '*.txt']:
            for file_path in self.project_path.rglob(ext):
                # Пропускаем исключенные директории
                if any(excluded in file_path.parts for excluded in EXCLUDE_DIRECTORIES):
                    continue

                # Пропускаем исключенные файлы
                if file_path.name in EXCLUDE_FILES:
                    continue

                target_files.append(file_path)

        return target_files

    def get_path_to_root(self, file_path: Path, absolute: bool = False) -> str:
        """Вычисляет путь от корня к файлу"""
        if absolute:
            return str(self.project_root)
        else:
            # Путь ОТ КОРНЯ к файлу
            relative = os.path.relpath(file_path, self.project_root)
            return relative.replace('\\', '/')

    def analyze_file_header(self, file_path: Path) -> Dict:
        """Анализирует заголовок файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    lines = f.readlines()
            except:
                return {'error': 'Не удалось прочитать файл'}

        # Ищем существующий заголовок в первых 5 строках
        for i, line in enumerate(lines[:5]):
            for pattern in HEADER_PATTERNS:
                match = re.match(pattern, line.strip())
                if match:
                    return {
                        'has_header': True,
                        'line_number': i,
                        'old_path': match.group(1).strip(),
                        'all_lines': lines
                    }

        # Проверяем shebang
        has_shebang = lines and lines[0].startswith('#!')

        return {
            'has_header': False,
            'has_shebang': has_shebang,
            'all_lines': lines
        }

    def create_header_line(self, file_path: Path, absolute: bool = False) -> str:
        """Создает строку заголовка"""
        path_to_root = self.get_path_to_root(file_path, absolute)
        return f"# PROJECT_ROOT: {path_to_root}\n"

    def update_file_header(self, file_path: Path, dry_run: bool = False,
                           absolute_paths: bool = False) -> Dict:
        """Обновляет заголовок файла"""
        analysis = self.analyze_file_header(file_path)

        if 'error' in analysis:
            return {'status': 'error', 'message': analysis['error']}

        new_header = self.create_header_line(file_path, absolute_paths)
        current_path = self.get_path_to_root(file_path, absolute_paths)

        if analysis['has_header']:
            old_path = analysis['old_path']

            # Проверяем, нужно ли обновление
            if old_path == current_path:
                return {'status': 'unchanged', 'message': 'Заголовок актуален'}

            # Обновляем существующий заголовок
            lines = analysis['all_lines']
            lines[analysis['line_number']] = new_header

            action = 'updated'
            message = f"Обновлен путь: {old_path} → {current_path}"

        else:
            # Добавляем новый заголовок
            lines = analysis['all_lines']
            insert_position = 1 if analysis.get('has_shebang') else 0
            lines.insert(insert_position, new_header)

            action = 'added'
            message = f"Добавлен заголовок: {current_path}"

        if not dry_run:
            # Сохраняем файл
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            except Exception as e:
                return {'status': 'error', 'message': f'Ошибка записи: {e}'}

        return {'status': action, 'message': message}

    def process_all_files(self, dry_run: bool = False, absolute_paths: bool = False) -> Dict:
        """Обрабатывает все Python файлы с прогресс-баром"""
        files = self.find_python_files()
        results = {
            'total': len(files),
            'updated': 0,
            'added': 0,
            'unchanged': 0,
            'errors': 0,
            'details': [],
            'start_time': time.time()
        }

        # Создаем прогресс-бар
        with tqdm(
                total=len(files),
                desc="Обработка файлов",
                unit="файл",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        ) as pbar:

            for file_path in files:
                try:
                    result = self.update_file_header(file_path, dry_run, absolute_paths)

                    relative_path = file_path.relative_to(self.project_path)
                    results['details'].append({
                        'file': str(relative_path),
                        'status': result['status'],
                        'message': result['message']
                    })

                    if result['status'] in results:
                        results[result['status']] += 1

                    # Обновляем прогресс-бар
                    status_counts = f"✓{results['added'] + results['updated']} ={results['unchanged']} ✗{results['errors']}"
                    pbar.set_postfix_str(f"{status_counts} | {relative_path.name}")
                    pbar.update(1)

                except Exception as e:
                    results['errors'] += 1
                    results['details'].append({
                        'file': str(file_path.relative_to(self.project_path)),
                        'status': 'error',
                        'message': str(e)
                    })
                    pbar.update(1)

        results['processing_time'] = time.time() - results['start_time']
        return results


# ===============================================
# CLI ИНТЕРФЕЙС
# ===============================================

def main():
    parser = argparse.ArgumentParser(
        description='Добавление/обновление заголовков в Python файлах',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
 python tools\headers\header_manager.py .                    # Относительные пути
 python tools\headers\header_manager.py . --absolute-paths   # Абсолютные пути  
 python tools\headers\header_manager.py . --dry-run          # Предварительный просмотр
 python tools\headers\project_header.py . > tools\headers\header_results.txt

       """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Путь к проекту (по умолчанию: текущая папка)'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Предварительный просмотр без изменений'
    )

    parser.add_argument(
        '--absolute-paths', '-a',
        action='store_true',
        help='Использовать абсолютные пути вместо относительных'
    )

    args = parser.parse_args()

    # Проверяем путь
    project_path = Path(args.path).resolve()
    if not project_path.exists():
        print(f"Путь не существует: {project_path}")
        return 1

    # Создаем менеджер
    manager = ProjectHeaderManager(str(project_path))

    # Выводим информацию
    mode_text = "[DRY RUN] " if args.dry_run else ""
    path_type = "абсолютные" if args.absolute_paths else "относительные"

    print(f"{mode_text}Обработка проекта: {project_path}")
    print(f"Корень проекта: {manager.project_root}")
    print(f"Тип путей: {path_type}")
    print("-" * 60)

    # Обрабатываем файлы
    results = manager.process_all_files(args.dry_run, args.absolute_paths)

    # Выводим результаты
    print("Результаты обработки:")
    print(f"   Всего файлов: {results['total']}")
    print(f"   Обновлено: {results['updated']}")
    print(f"   Добавлено: {results['added']}")
    print(f"   Без изменений: {results['unchanged']}")
    print(f"   Ошибок: {results['errors']}")

    # Показываем детали если есть изменения
    if results['updated'] > 0 or results['added'] > 0 or results['errors'] > 0:
        print(f"\nДетали изменений:")
        for detail in results['details']:
            if detail['status'] != 'unchanged':
                status_icon = {
                    'updated': '[UPD]',
                    'added': '[ADD]',
                    'error': '[ERR]'
                }.get(detail['status'], '❓')

                print(f"   {status_icon} {detail['file']}: {detail['message']}")

    print("\nОбработка завершена!")
    processing_time = results.get('processing_time', 0)
    print(f"\nВремя выполнения: {processing_time:.2f} секунд")
    if processing_time > 0:
        print(f"Скорость: {results['total'] / processing_time:.1f} файлов/сек")
    return 0


if __name__ == "__main__":
    exit(main())