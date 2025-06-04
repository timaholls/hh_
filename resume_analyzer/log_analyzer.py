#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для анализа и управления лог-файлами процесса подбора резюме.
Позволяет получить статистику, метрики и информацию о работе программы.
"""

import os
import re
import sys
import glob
import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

# Регулярные выражения для извлечения информации из логов
TIME_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.*)')
RESUME_ANALYSIS_TIME_PATTERN = re.compile(r'Анализ резюме выполнен за (\d+\.\d+) секунд\. Оценка: (\d+\.\d+)/10')
RESUME_NAME_PATTERN = re.compile(r'Анализ резюме \d+/\d+: (resume_\d+\.txt)')
BEST_CANDIDATE_PATTERN = re.compile(r'ЛУЧШИЙ КАНДИДАТ: (resume_\d+\.txt) с оценкой (\d+\.\d+)/10')


def get_log_dir():
    """
    Получает путь к директории с логами.
    
    Returns:
        str: Абсолютный путь к директории с логами.
    """
    # Получаем путь к текущей директории скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "logs")


def parse_log_file(log_file):
    """
    Парсит файл логов и извлекает полезную информацию.
    
    Args:
        log_file (str): Путь к файлу логов.
        
    Returns:
        dict: Словарь с извлеченной информацией из логов.
    """
    if not os.path.exists(log_file):
        print(f"Файл логов не найден: {log_file}")
        return None
    
    print(f"Анализ лог-файла: {log_file}")
    
    # Структура для хранения результатов анализа
    log_data = {
        'start_time': None,
        'end_time': None,
        'info_count': 0,
        'warning_count': 0,
        'error_count': 0,
        'debug_count': 0,
        'resume_analyses': [],
        'best_candidate': None,
        'best_score': 0,
        'errors': [],
        'warnings': []
    }
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            if lines:
                # Определяем начальное время из первой строки
                first_line_match = TIME_PATTERN.match(lines[0])
                if first_line_match:
                    log_data['start_time'] = first_line_match.group(1)
                
                # Определяем конечное время из последней строки
                last_line_match = TIME_PATTERN.match(lines[-1])
                if last_line_match:
                    log_data['end_time'] = last_line_match.group(1)
            
            current_resume = None
            
            for line in lines:
                # Извлекаем время, модуль, уровень и сообщение
                match = TIME_PATTERN.match(line)
                if match:
                    timestamp, module, level, message = match.groups()
                    
                    # Подсчитываем количество сообщений по уровням
                    if level == 'INFO':
                        log_data['info_count'] += 1
                    elif level == 'WARNING':
                        log_data['warning_count'] += 1
                        log_data['warnings'].append((timestamp, module, message))
                    elif level == 'ERROR':
                        log_data['error_count'] += 1
                        log_data['errors'].append((timestamp, module, message))
                    elif level == 'DEBUG':
                        log_data['debug_count'] += 1
                    
                    # Находим информацию о текущем анализируемом резюме
                    resume_name_match = RESUME_NAME_PATTERN.search(message)
                    if resume_name_match:
                        current_resume = resume_name_match.group(1)
                    
                    # Извлекаем время анализа и оценку резюме
                    analysis_time_match = RESUME_ANALYSIS_TIME_PATTERN.search(message)
                    if analysis_time_match and current_resume:
                        time_taken = float(analysis_time_match.group(1))
                        score = float(analysis_time_match.group(2))
                        log_data['resume_analyses'].append({
                            'resume': current_resume,
                            'time': time_taken,
                            'score': score
                        })
                    
                    # Определение лучшего кандидата
                    best_candidate_match = BEST_CANDIDATE_PATTERN.search(message)
                    if best_candidate_match:
                        log_data['best_candidate'] = best_candidate_match.group(1)
                        log_data['best_score'] = float(best_candidate_match.group(2))
        
        return log_data
    except Exception as e:
        print(f"Ошибка при парсинге файла логов {log_file}: {e}")
        return None


def generate_report(log_data, output_dir=None):
    """
    Генерирует отчет на основе данных из лог-файла.
    
    Args:
        log_data (dict): Словарь с данными из лог-файла.
        output_dir (str): Директория для сохранения отчета и графиков.
        
    Returns:
        str: Путь к сгенерированному отчету.
    """
    if not log_data:
        print("Нет данных для генерации отчета")
        return None
    
    # Создаем директорию для отчета, если она не существует
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        os.makedirs(output_dir, exist_ok=True)
    
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = os.path.join(output_dir, f"log_report_{current_time}.txt")
    
    # Подготовка данных для графиков
    if log_data['resume_analyses']:
        analyses_df = pd.DataFrame(log_data['resume_analyses'])
        
        # График времени анализа каждого резюме
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(analyses_df)), analyses_df['time'])
        plt.title('Время анализа резюме')
        plt.xlabel('Индекс резюме')
        plt.ylabel('Время (сек)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"analysis_time_{current_time}.png"))
        
        # График оценок резюме
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(analyses_df)), analyses_df['score'])
        plt.title('Оценки резюме')
        plt.xlabel('Индекс резюме')
        plt.ylabel('Оценка (0-10)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"scores_{current_time}.png"))
        
        # Гистограмма распределения оценок
        plt.figure(figsize=(10, 6))
        plt.hist(analyses_df['score'], bins=10)
        plt.title('Распределение оценок')
        plt.xlabel('Оценка')
        plt.ylabel('Количество резюме')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"score_distribution_{current_time}.png"))
    
    # Генерация текстового отчета
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ОТЧЕТ ПО АНАЛИЗУ РЕЗЮМЕ\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("ОБЩАЯ ИНФОРМАЦИЯ:\n")
        f.write(f"Время начала: {log_data.get('start_time', 'Не определено')}\n")
        f.write(f"Время окончания: {log_data.get('end_time', 'Не определено')}\n")
        f.write(f"Количество записей INFO: {log_data['info_count']}\n")
        f.write(f"Количество записей WARNING: {log_data['warning_count']}\n")
        f.write(f"Количество записей ERROR: {log_data['error_count']}\n")
        f.write(f"Количество записей DEBUG: {log_data['debug_count']}\n\n")
        
        f.write("РЕЗУЛЬТАТЫ АНАЛИЗА:\n")
        f.write(f"Проанализировано резюме: {len(log_data['resume_analyses'])}\n")
        
        if log_data['resume_analyses']:
            times = [a['time'] for a in log_data['resume_analyses']]
            scores = [a['score'] for a in log_data['resume_analyses']]
            
            f.write(f"Среднее время анализа: {sum(times)/len(times):.2f} сек\n")
            f.write(f"Максимальное время анализа: {max(times):.2f} сек\n")
            f.write(f"Минимальное время анализа: {min(times):.2f} сек\n")
            f.write(f"Средняя оценка: {sum(scores)/len(scores):.2f}/10\n")
            f.write(f"Максимальная оценка: {max(scores):.2f}/10\n")
            f.write(f"Минимальная оценка: {min(scores):.2f}/10\n\n")
        
        f.write("ЛУЧШИЙ КАНДИДАТ:\n")
        if log_data['best_candidate']:
            f.write(f"Файл: {log_data['best_candidate']}\n")
            f.write(f"Оценка: {log_data['best_score']:.2f}/10\n\n")
        else:
            f.write("Информация о лучшем кандидате не найдена\n\n")
        
        if log_data['errors']:
            f.write("ОШИБКИ:\n")
            for timestamp, module, message in log_data['errors']:
                f.write(f"[{timestamp}] {module}: {message}\n")
            f.write("\n")
        
        if log_data['warnings']:
            f.write("ПРЕДУПРЕЖДЕНИЯ:\n")
            for timestamp, module, message in log_data['warnings']:
                f.write(f"[{timestamp}] {module}: {message}\n")
            f.write("\n")
        
        if log_data['resume_analyses']:
            f.write("ТОПОВЫЕ РЕЗЮМЕ ПО ОЦЕНКЕ:\n")
            top_analyses = sorted(log_data['resume_analyses'], key=lambda x: x['score'], reverse=True)[:5]
            for i, analysis in enumerate(top_analyses, 1):
                f.write(f"{i}. {analysis['resume']} - Оценка: {analysis['score']:.2f}/10\n")
            f.write("\n")
    
    print(f"Отчет сохранен в файл: {report_file}")
    
    # Если есть matplotlib, сообщаем о сохраненных графиках
    if log_data['resume_analyses']:
        print(f"Графики сохранены в директорию: {output_dir}")
    
    return report_file


def list_log_files():
    """
    Находит все файлы логов в директории logs.
    
    Returns:
        list: Список путей к файлам логов.
    """
    logs_dir = get_log_dir()
    if not os.path.exists(logs_dir):
        print(f"Директория с логами не найдена: {logs_dir}")
        return []
    
    log_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.endswith('.log')]
    return sorted(log_files, key=os.path.getmtime, reverse=True)


def print_logs_info():
    """Выводит информацию о файлах логов."""
    logs_dir = get_log_dir()
    
    print("\n" + "="*50)
    print("ИНФОРМАЦИЯ О ЛОГИРОВАНИИ")
    print("="*50)
    
    print(f"\nДиректория с логами: {logs_dir}")
    
    if not os.path.exists(logs_dir):
        print("Директория с логами не существует. Будет создана при первом запуске программы.")
        return
    
    # Получаем список лог-файлов
    log_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.endswith('.log')]
    log_files.sort(key=os.path.getmtime, reverse=True)
    
    if not log_files:
        print("Лог-файлы не найдены.")
        return
    
    # Вычисляем статистику
    total_size = 0
    log_files_info = []
    
    for log_file in log_files:
        try:
            file_size = os.path.getsize(log_file)
            mod_time = os.path.getmtime(log_file)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            
            log_files_info.append({
                "path": log_file,
                "name": os.path.basename(log_file),
                "size_bytes": file_size,
                "size_kb": file_size / 1024,
                "mod_time": mod_time,
                "mod_time_str": mod_time_str,
            })
            
            total_size += file_size
            
        except Exception as e:
            print(f"Ошибка при чтении информации о файле {log_file}: {e}", file=sys.stderr)
    
    print(f"Всего лог-файлов: {len(log_files_info)}")
    print(f"Общий размер логов: {total_size / 1024:.2f} КБ ({total_size / (1024 * 1024):.2f} МБ)")
    
    if log_files_info:
        latest = log_files_info[0]
        print(f"\nПоследний лог-файл: {latest['name']}")
        print(f"  Время создания: {latest['mod_time_str']}")
        print(f"  Размер: {latest['size_kb']:.2f} КБ")
    
    if len(log_files_info) > 0:
        print("\nДоступные лог-файлы (от новых к старым):")
        for i, log_file in enumerate(log_files_info[:5], 1):
            print(f"{i}. {log_file['name']} ({log_file['mod_time_str']}, {log_file['size_kb']:.2f} КБ)")
        
        if len(log_files_info) > 5:
            print(f"... и еще {len(log_files_info) - 5} файлов")
    
    print("\nДля анализа логов запустите: python log_analyzer.py --latest")
    print("="*50)


def clean_old_logs():
    """
    Очищает старые лог-файлы, оставляя только 5 последних.
    """
    logs_dir = get_log_dir()
    
    if not os.path.exists(logs_dir):
        print("Директория с логами не существует.")
        return
    
    log_files = list_log_files()
    
    if len(log_files) <= 5:
        print("Нет старых лог-файлов для удаления")
        return
    
    files_to_delete = log_files[5:]
    
    print(f"Удаление {len(files_to_delete)} старых лог-файлов...")
    
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Удален файл: {os.path.basename(file_path)}")
            deleted_count += 1
        except Exception as e:
            print(f"Ошибка при удалении файла {file_path}: {e}", file=sys.stderr)
    
    print(f"Удалено {deleted_count} из {len(files_to_delete)} старых лог-файлов")


def main():
    """Основная функция для запуска анализа логов."""
    parser = argparse.ArgumentParser(description='Анализ и управление лог-файлами процесса подбора резюме')
    
    parser.add_argument('--log-file', type=str, help='Путь к файлу логов для анализа')
    parser.add_argument('--output-dir', type=str, help='Директория для сохранения отчета')
    parser.add_argument('--list-logs', action='store_true', help='Показать список доступных лог-файлов')
    parser.add_argument('--latest', action='store_true', help='Анализировать последний файл логов')
    parser.add_argument('--info', action='store_true', help='Показать общую информацию о логах')
    parser.add_argument('--clean', action='store_true', help='Очистить старые лог-файлы (оставить 5 последних)')
    
    args = parser.parse_args()
    
    # Вывод информации о логах
    if args.info:
        print_logs_info()
        return
    
    # Очистка старых логов
    if args.clean:
        clean_old_logs()
        return
    
    # Просто вывод списка лог-файлов
    if args.list_logs:
        logs = list_log_files()
        if logs:
            print("Доступные лог-файлы:")
            for i, log_file in enumerate(logs, 1):
                print(f"{i}. {os.path.basename(log_file)}")
        else:
            print("Лог-файлы не найдены")
        return
    
    log_file = None
    
    if args.log_file:
        log_file = args.log_file
    elif args.latest:
        logs = list_log_files()
        if logs:
            log_file = logs[0]
            print(f"Выбран последний лог-файл: {os.path.basename(log_file)}")
        else:
            print("Лог-файлы не найдены")
            return
    else:
        logs = list_log_files()
        if not logs:
            print("Лог-файлы не найдены")
            return
        
        print("Доступные лог-файлы:")
        for i, log_path in enumerate(logs, 1):
            print(f"{i}. {os.path.basename(log_path)}")
        
        try:
            selection = int(input("\nВыберите номер лог-файла для анализа: "))
            if 1 <= selection <= len(logs):
                log_file = logs[selection - 1]
            else:
                print("Некорректный выбор")
                return
        except ValueError:
            print("Некорректный ввод")
            return
    
    # Анализ выбранного лог-файла
    log_data = parse_log_file(log_file)
    
    if log_data:
        # Генерация отчета
        generate_report(log_data, args.output_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Произошла ошибка при выполнении анализа логов: {e}")
        import traceback
        traceback.print_exc() 