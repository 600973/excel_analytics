#!/usr/bin/env python3
# PROJECT_ROOT: tree_generator.py
# -*- coding: utf-8 -*-
"""
Генератор структуры проекта
Создает текстовое представление структуры директорий с различными форматами вывода
"""

import os
import json
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Set, Dict, Optional, Union
import argparse

# ===============================================
# НАСТРОЙКИ (легко изменяемые)
# ===============================================

# Файлы и папки для исключения (паттерны)
DEFAULT_IGNORE_PATTERNS = {
    # Системные папки
    '.git', '.svn', '.hg',
    '__pycache__', '.pytest_cache', '.coverage',
    'node_modules', '.npm', 'bower_components',
    'rag_env_new', 'archive', 'docs', 'documentation',
    'to do', 'tests',

    # Виртуальные окружения
    'venv', '.venv', 'env', '.env',
    'virtualenv', '.virtualenv',

    # IDE папки
    '.idea', '.vscode', '.eclipse',
    '.sublime-project', '.sublime-workspace',

    # Временные и сборочные папки
    'build', 'dist', 'target', 'out',
    'tmp', 'temp', 'logs', 'log',
    '*.egg-info', '.tox',

    # Файлы
    '*.pyc', '*.pyo', '*.pyd',
    '*.log', '*.tmp', '*.cache',
    '.DS_Store', 'Thumbs.db',
    '*.swp', '*.swo', '*~',
}

# Форматы вывода
OUTPUT_FORMATS = ['tree', 'list', 'json', 'markdown']


# ===============================================
# ОСНОВНЫЕ КЛАССЫ
# ===============================================

class ProjectStructureGenerator:
    """Генератор структуры проекта"""

    def __init__(self, root_path: str, ignore_patterns: Optional[Set[str]] = None):
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS
        self.stats = {
            'total_dirs': 0,
            'total_files': 0,
            'total_size': 0,
            'file_types': {}
        }

    def should_ignore(self, path: Path) -> bool:
        """Проверяет, нужно ли игнорировать путь"""
        # Проверяем относительный путь от корня
        try:
            relative_path = path.relative_to(self.root_path)
        except ValueError:
            return True

        # Проверяем каждую часть пути
        for part in relative_path.parts:
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(part, pattern):
                    return True

        # Проверяем полный относительный путь
        relative_str = str(relative_path)
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(relative_str, pattern):
                return True

        return False

    def collect_structure(self) -> Dict:
        """Собирает структуру проекта"""
        structure = {
            'name': self.root_path.name,
            'path': str(self.root_path),
            'type': 'directory',
            'children': [],
            'size': 0
        }

        self._collect_recursive(self.root_path, structure)

        return structure

    def _collect_recursive(self, current_path: Path, node: Dict):
        """Рекурсивно собирает структуру"""
        if not current_path.is_dir():
            return

        try:
            items = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return

        for item in items:
            if self.should_ignore(item):
                continue

            if item.is_dir():
                self.stats['total_dirs'] += 1
                child_node = {
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory',
                    'children': [],
                    'size': 0
                }
                self._collect_recursive(item, child_node)
                node['children'].append(child_node)

            elif item.is_file():
                self.stats['total_files'] += 1
                try:
                    file_size = item.stat().st_size
                    self.stats['total_size'] += file_size

                    # Статистика по типам файлов
                    ext = item.suffix.lower()
                    self.stats['file_types'][ext] = self.stats['file_types'].get(ext, 0) + 1

                    child_node = {
                        'name': item.name,
                        'path': str(item),
                        'type': 'file',
                        'size': file_size,
                        'extension': ext
                    }
                    node['children'].append(child_node)

                except (OSError, PermissionError):
                    continue

    def generate_tree_format(self, structure: Dict, include_sizes: bool = False) -> str:
        """Генерирует ASCII дерево"""
        lines = []
        lines.append(f"📁 {structure['name']}/")

        def _generate_tree_recursive(node: Dict, prefix: str = "", is_last: bool = True):
            children = node.get('children', [])

            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)

                # Символы для дерева
                if is_last_child:
                    current_prefix = "└── "
                    next_prefix = prefix + "    "
                else:
                    current_prefix = "├── "
                    next_prefix = prefix + "│   "

                # Иконка для типа
                if child['type'] == 'directory':
                    icon = "📁"
                    name_suffix = "/"
                else:
                    icon = self._get_file_icon(child.get('extension', ''))
                    name_suffix = ""

                # Размер файла
                size_info = ""
                if include_sizes and child['type'] == 'file':
                    size_info = f" ({self._format_size(child.get('size', 0))})"

                line = f"{prefix}{current_prefix}{icon} {child['name']}{name_suffix}{size_info}"
                lines.append(line)

                # Рекурсивно для папок
                if child['type'] == 'directory':
                    _generate_tree_recursive(child, next_prefix, is_last_child)

        _generate_tree_recursive(structure)
        return '\n'.join(lines)

    def generate_list_format(self, structure: Dict, include_sizes: bool = False) -> str:
        """Генерирует простой список файлов"""
        lines = []

        def _generate_list_recursive(node: Dict, current_path: str = ""):
            for child in node.get('children', []):
                if child['type'] == 'directory':
                    dir_path = f"{current_path}/{child['name']}" if current_path else child['name']
                    lines.append(f"{dir_path}/")
                    _generate_list_recursive(child, dir_path)
                else:
                    file_path = f"{current_path}/{child['name']}" if current_path else child['name']
                    if include_sizes:
                        size_info = f" ({self._format_size(child.get('size', 0))})"
                        lines.append(f"{file_path}{size_info}")
                    else:
                        lines.append(file_path)

        _generate_list_recursive(structure)
        return '\n'.join(lines)

    def generate_json_format(self, structure: Dict) -> str:
        """Генерирует JSON представление"""
        return json.dumps(structure, indent=2, ensure_ascii=False)

    def generate_markdown_format(self, structure: Dict, include_sizes: bool = False) -> str:
        """Генерирует Markdown документ"""
        lines = []
        lines.append(f"# Структура проекта: {structure['name']}")
        lines.append("")
        lines.append(f"**Сгенерировано:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Статистика
        lines.append("## 📊 Статистика")
        lines.append(f"- **Папок:** {self.stats['total_dirs']}")
        lines.append(f"- **Файлов:** {self.stats['total_files']}")
        lines.append(f"- **Общий размер:** {self._format_size(self.stats['total_size'])}")
        lines.append("")

        # Типы файлов
        if self.stats['file_types']:
            lines.append("### Типы файлов")
            sorted_types = sorted(self.stats['file_types'].items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types[:10]:  # Топ 10
                ext_name = ext if ext else "без расширения"
                lines.append(f"- **{ext_name}:** {count} файлов")
            lines.append("")

        # Структура дерева
        lines.append("## 🌳 Структура")
        lines.append("```")
        lines.append(self.generate_tree_format(structure, include_sizes))
        lines.append("```")

        return '\n'.join(lines)

    def _get_file_icon(self, extension: str) -> str:
        """Возвращает иконку для типа файла"""
        icon_map = {
            '.py': '🐍',
            '.js': '📜',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.xml': '📋',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.md': '📝',
            '.txt': '📄',
            '.pdf': '📕',
            '.doc': '📘',
            '.docx': '📘',
            '.xls': '📊',
            '.xlsx': '📊',
            '.png': '🖼️',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.gif': '🖼️',
            '.svg': '🖼️',
            '.zip': '🗜️',
            '.tar': '🗜️',
            '.gz': '🗜️',
            '.sql': '🗄️',
            '.db': '🗄️',
            '.log': '📋',
        }
        return icon_map.get(extension, '📄')

    def _format_size(self, size_bytes: int) -> str:
        """Форматирует размер файла"""
        if size_bytes == 0:
            return "0 B"

        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"


# ===============================================
# ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ
# ===============================================

class GitAwareGenerator(ProjectStructureGenerator):
    """Генератор с учетом Git репозитория"""

    def __init__(self, root_path: str, ignore_patterns: Optional[Set[str]] = None, only_tracked: bool = False):
        super().__init__(root_path, ignore_patterns)
        self.only_tracked = only_tracked
        self.tracked_files = self._get_tracked_files() if only_tracked else None

    def _get_tracked_files(self) -> Set[str]:
        """Получает список отслеживаемых Git файлов"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'ls-files'],
                cwd=self.root_path,
                capture_output=True,
                text=True,
                check=True
            )
            tracked = set()
            for line in result.stdout.strip().split('\n'):
                if line:
                    tracked.add(str(self.root_path / line))
            return tracked
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def should_ignore(self, path: Path) -> bool:
        """Расширенная проверка с учетом Git"""
        # Базовая проверка
        if super().should_ignore(path):
            return True

        # Проверка Git отслеживания
        if self.only_tracked and self.tracked_files is not None:
            if path.is_file() and str(path) not in self.tracked_files:
                return True

        return False


# ===============================================
# ГЛАВНАЯ ФУНКЦИЯ И CLI
# ===============================================

def main():
    """Главная функция с CLI интерфейсом"""
    parser = argparse.ArgumentParser(
        description='Генератор структуры проекта',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
 python tree_generator.py .                          # Генерация дерева для текущей папки
 python tree_generator.py /path/to/project --format=json   # JSON формат
 python tree_generator.py . --output=structure.txt   # Сохранение в файл
 python tree_generator.py . --git-only               # Только отслеживаемые Git файлы
 python tree_generator.py . --ignore="*.log,temp"    # Дополнительные исключения
 python tools\tree_genegator\tree_generator.py . --output=tools\tree_genegator\structure.txt # Генерация дерева из корневой папки
       """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Путь к проекту для анализа (по умолчанию: текущая папка)'
    )

    parser.add_argument(
        '--format', '-f',
        choices=OUTPUT_FORMATS,
        default='tree',
        help='Формат вывода (по умолчанию: tree)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Файл для сохранения результата (по умолчанию: вывод в консоль)'
    )

    parser.add_argument(
        '--sizes', '-s',
        action='store_true',
        help='Включить размеры файлов в вывод'
    )

    parser.add_argument(
        '--git-only', '-g',
        action='store_true',
        help='Показывать только файлы, отслеживаемые Git'
    )

    parser.add_argument(
        '--ignore', '-i',
        help='Дополнительные паттерны для исключения (через запятую)'
    )

    parser.add_argument(
        '--no-default-ignores',
        action='store_true',
        help='Не использовать стандартные исключения'
    )

    args = parser.parse_args()

    # Подготавливаем паттерны исключений
    ignore_patterns = set()
    if not args.no_default_ignores:
        ignore_patterns.update(DEFAULT_IGNORE_PATTERNS)

    if args.ignore:
        custom_patterns = [p.strip() for p in args.ignore.split(',')]
        ignore_patterns.update(custom_patterns)

    # Проверяем путь
    project_path = Path(args.path or "..").resolve()
    if not project_path.exists():
        print(f"❌ Путь не существует: {project_path}")
        return 1

    if not project_path.is_dir():
        print(f"❌ Путь не является папкой: {project_path}")
        return 1

    # Создаем генератор
    if args.git_only:
        generator = GitAwareGenerator(str(project_path), ignore_patterns, only_tracked=True)
    else:
        generator = ProjectStructureGenerator(str(project_path), ignore_patterns)

    print(f"🔍 Анализ проекта: {project_path}")
    print(f"📊 Формат: {args.format}")
    if args.git_only:
        print("📝 Режим: только Git отслеживаемые файлы")
    print("-" * 50)

    # Собираем структуру
    structure = generator.collect_structure()

    # Генерируем вывод
    if args.format == 'tree':
        output = generator.generate_tree_format(structure, args.sizes)
    elif args.format == 'list':
        output = generator.generate_list_format(structure, args.sizes)
    elif args.format == 'json':
        output = generator.generate_json_format(structure)
    elif args.format == 'markdown':
        output = generator.generate_markdown_format(structure, args.sizes)

    # Добавляем заголовок для консольного вывода
    if not args.output and args.format != 'json':
        header = f"\n📁 Структура проекта: {project_path.name}\n"
        header += f"📊 Папок: {generator.stats['total_dirs']}, "
        header += f"Файлов: {generator.stats['total_files']}, "
        header += f"Размер: {generator._format_size(generator.stats['total_size'])}\n"
        header += "=" * 60 + "\n"
        output = header + output

    # Сохраняем или выводим
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ Структура сохранена в: {output_path}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    exit(main())