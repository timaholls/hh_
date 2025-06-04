#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный модуль программы для анализа резюме и выбора лучшего кандидата.
Запускает процесс генерации тестовых данных и анализа резюме.
"""

import os
import sys
import logging
import datetime
import json
from pathlib import Path
from data_generator import DataGenerator
from analyzer import ResumeAnalyzer
from llm_interface import LLMInterface

# Создаем директорию для логов, если она не существует
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Формируем имя файла лога с текущей датой и временем
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(logs_dir, f"resume_analyzer_{current_time}.log")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ResumeAnalyzerApp:
    """
    Основной класс приложения для анализа резюме и выбора лучшего кандидата.
    
    Attributes:
        data_dir (str): Путь к директории с данными.
        vacancy_dir (str): Путь к директории с описанием вакансии.
        resumes_dir (str): Путь к директории с резюме кандидатов.
        vacancy_file (str): Имя файла с описанием вакансии.
        num_resumes (int): Количество резюме для генерации.
        top_n (int): Количество лучших кандидатов для отображения.
    """
    
    def __init__(self, data_dir="data", vacancy_file="vacancy.txt", 
                 num_resumes=100, top_n=5):
        """
        Инициализирует приложение для анализа резюме.
        
        Args:
            data_dir (str): Путь к директории с данными.
            vacancy_file (str): Имя файла с описанием вакансии.
            num_resumes (int): Количество резюме для генерации.
            top_n (int): Количество лучших кандидатов для отображения.
        """
        self.data_dir = data_dir
        self.vacancy_dir = os.path.join(data_dir, "vacancy")
        self.resumes_dir = os.path.join(data_dir, "resumes")
        self.vacancy_file = os.path.join(self.vacancy_dir, vacancy_file)
        self.num_resumes = num_resumes  # Всегда 100 резюме
        self.top_n = top_n
        
        # Убедимся, что директории существуют
        os.makedirs(self.vacancy_dir, exist_ok=True)
        os.makedirs(self.resumes_dir, exist_ok=True)
        
        # Логируем путь к файлу журнала
        logger.info(f"Логи записываются в файл: {os.path.abspath(log_file)}")
        
        # Инициализация компонентов
        self.llm_interface = LLMInterface(model="gpt-4.1-nano")
        self.data_generator = DataGenerator(self.llm_interface)
        self.analyzer = ResumeAnalyzer(self.llm_interface)
        
    def generate_data(self):
        """
        Генерирует тестовые данные: описание вакансии и резюме кандидатов.
        """
        logger.info("Генерация тестовых данных...")
        
        # Генерируем описание вакансии, если файл не существует
        if not os.path.exists(self.vacancy_file):
            self.data_generator.generate_vacancy(self.vacancy_file)
            logger.info(f"Описание вакансии сгенерировано: {self.vacancy_file}")
        else:
            logger.info(f"Используется существующее описание вакансии: {self.vacancy_file}")
        
        # Генерируем резюме
        existing_resumes = len([f for f in os.listdir(self.resumes_dir) 
                               if f.startswith("resume_") and f.endswith(".txt")])
        
        if existing_resumes < self.num_resumes:
            to_generate = self.num_resumes - existing_resumes
            logger.info(f"Генерация {to_generate} резюме...")
            
            with open(self.vacancy_file, 'r', encoding='utf-8') as f:
                vacancy_text = f.read()
                
            self.data_generator.generate_resumes(
                self.resumes_dir, 
                vacancy_text, 
                count=to_generate, 
                start_index=existing_resumes + 1
            )
            logger.info(f"Сгенерировано {to_generate} резюме")
        else:
            logger.info(f"Используются существующие резюме: {existing_resumes} шт.")
    
    def analyze_resumes(self):
        """
        Анализирует резюме и определяет лучших кандидатов.
        
        Returns:
            list: Список кандидатов с их оценками и обоснованиями, отсортированный по убыванию оценки.
        """
        logger.info("Начало анализа резюме...")
        
        # Чтение вакансии
        with open(self.vacancy_file, 'r', encoding='utf-8') as f:
            vacancy_text = f.read()
        
        # Получение списка файлов резюме
        resume_files = [f for f in os.listdir(self.resumes_dir) 
                        if f.startswith("resume_") and f.endswith(".txt")]
        
        if not resume_files:
            logger.error("Резюме не найдены. Убедитесь, что они были сгенерированы.")
            return []
        
        # Анализ каждого резюме
        results = []
        for i, resume_file in enumerate(resume_files, 1):
            resume_path = os.path.join(self.resumes_dir, resume_file)
            
            with open(resume_path, 'r', encoding='utf-8') as f:
                resume_text = f.read()
            
            logger.info(f"Анализ резюме {i}/{len(resume_files)}: {resume_file}")
            result = self.analyzer.analyze_resume(resume_text, vacancy_text)
            result['file_name'] = resume_file
            results.append(result)
        
        # Сортировка результатов по оценке (по убыванию)
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        return sorted_results
    
    def display_results(self, results):
        """
        Выводит результаты анализа: лучшего кандидата и топ-N кандидатов.
        
        Args:
            results (list): Отсортированный список результатов анализа.
        """
        if not results:
            logger.warning("Нет результатов для отображения.")
            return
        
        # Вывод информации о лучшем кандидате
        best_candidate = results[0]
        logger.info(f"ЛУЧШИЙ КАНДИДАТ: {best_candidate['file_name']} с оценкой {best_candidate['score']:.2f}/10")
        
        result_summary = "\n" + "="*80 + "\n"
        result_summary += f"ЛУЧШИЙ КАНДИДАТ: {best_candidate['file_name']}\n"
        result_summary += f"Оценка: {best_candidate['score']:.2f}/10\n"
        result_summary += f"Обоснование: {best_candidate['justification']}\n"
        result_summary += "="*80 + "\n\n"
        
        # Вывод топ-N кандидатов
        result_summary += f"ТОП-{min(self.top_n, len(results))} КАНДИДАТОВ:\n"
        result_summary += "-"*80 + "\n"
        
        for i, candidate in enumerate(results[:self.top_n], 1):
            result_summary += f"{i}. {candidate['file_name']}\n"
            result_summary += f"   Оценка: {candidate['score']:.2f}/10\n"
            result_summary += f"   Обоснование: {candidate['justification']}\n"
            result_summary += "-"*80 + "\n"
        
        print(result_summary)
        
        # Также записываем результаты в лог
        logger.info("Подробные результаты анализа:\n" + result_summary)
    
    def save_results_to_json(self, results):
        """
        Сохраняет результаты анализа в JSON-файл.
        
        Args:
            results (list): Отсортированный список результатов анализа.
            
        Returns:
            str: Путь к созданному JSON-файлу.
        """
        if not results:
            logger.warning("Нет результатов для сохранения в JSON.")
            return None
        
        # Создаем объект для сохранения в JSON
        json_data = {
            "best_candidate": {
                "file_name": results[0]["file_name"],
                "score": results[0]["score"],
                "justification": results[0]["justification"]
            },
            "top_candidates": [
                {
                    "file_name": candidate["file_name"],
                    "score": candidate["score"],
                    "justification": candidate["justification"]
                } for candidate in results[:self.top_n]
            ],
            "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Сохраняем в JSON-файл
        output_file = "results.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Результаты сохранены в JSON-файл: {os.path.abspath(output_file)}")
            return output_file
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов в JSON: {e}")
            return None
    
    def save_results_to_markdown(self, results):
        """
        Сохраняет результаты анализа в Markdown-файл.
        
        Args:
            results (list): Отсортированный список результатов анализа.
            
        Returns:
            str: Путь к созданному Markdown-файлу.
        """
        if not results:
            logger.warning("Нет результатов для сохранения в Markdown.")
            return None
        
        # Создаем содержимое Markdown-файла
        markdown_content = "# Результаты анализа резюме\n\n"
        
        # Добавляем информацию о лучшем кандидате
        best_candidate = results[0]
        markdown_content += "## Лучший кандидат:\n"
        markdown_content += f"**Файл**: {best_candidate['file_name']}  \n"
        markdown_content += f"**Оценка**: {best_candidate['score']:.2f}/10  \n"
        markdown_content += f"**Обоснование**: {best_candidate['justification']}\n\n"
        
        # Добавляем информацию о топ-N кандидатах
        markdown_content += f"## ТОП-{min(self.top_n, len(results))} кандидатов:\n\n"
        
        for i, candidate in enumerate(results[:self.top_n], 1):
            markdown_content += f"### {i}. {candidate['file_name']}\n"
            markdown_content += f"**Оценка**: {candidate['score']:.2f}/10  \n"
            markdown_content += f"**Обоснование**: {candidate['justification']}\n\n"
        
        # Добавляем дату анализа
        markdown_content += f"---\n*Анализ завершен: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}* \n"
        
        # Сохраняем в Markdown-файл
        output_file = "results.md"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Результаты сохранены в Markdown-файл: {os.path.abspath(output_file)}")
            return output_file
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов в Markdown: {e}")
            return None
    
    def run(self):
        """
        Запускает полный процесс: генерацию данных, анализ резюме и вывод результатов.
        """
        try:
            logger.info("Запуск приложения для анализа резюме...")
            
            # Генерация данных
            self.generate_data()
            
            # Анализ резюме
            results = self.analyze_resumes()
            
            # Вывод результатов
            self.display_results(results)
            
            # Сохранение результатов в файлы
            self.save_results_to_markdown(results)
            self.save_results_to_json(results)
            
            logger.info("Анализ резюме завершен успешно.")
            
        except Exception as e:
            logger.error(f"Произошла ошибка при выполнении программы: {e}")
            raise


if __name__ == "__main__":
    # Создаем и запускаем приложение с фиксированными параметрами
    app = ResumeAnalyzerApp(
        data_dir="data",
        vacancy_file="vacancy.txt",
        num_resumes=100,  # Всегда генерируем 100 резюме
        top_n=5
    )
    
    app.run() 