#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для генерации тестовых данных: описания вакансии и резюме кандидатов.
Использует языковую модель (LLM) для создания реалистичных текстов.
"""

import os
import logging
import random
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class DataGenerator:
    """
    Класс для генерации тестовых данных: описания вакансии и резюме кандидатов.
    
    Attributes:
        llm_interface: Интерфейс для взаимодействия с языковой моделью.
    """
    
    def __init__(self, llm_interface):
        """
        Инициализирует генератор данных.
        
        Args:
            llm_interface: Интерфейс для взаимодействия с языковой моделью.
        """
        self.llm_interface = llm_interface
        logger.info("Инициализирован генератор данных")
    
    def generate_vacancy(self, output_path):
        """
        Генерирует описание вакансии и сохраняет его в файл.
        
        Args:
            output_path (str): Путь для сохранения файла с описанием вакансии.
            
        Returns:
            str: Путь к созданному файлу.
        """
        logger.info(f"Генерация описания вакансии в файл: {output_path}")
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        start_time = time.time()
        
        try:
            # Генерируем описание вакансии
            vacancy_text = self.llm_interface.generate_vacancy()
            
            # Записываем время генерации
            elapsed_time = time.time() - start_time
            logger.info(f"Описание вакансии сгенерировано за {elapsed_time:.2f} секунд")
            
            # Логируем первые 100 символов для отладки
            vacancy_preview = vacancy_text[:100].replace('\n', ' ').strip() + '...' if len(vacancy_text) > 100 else vacancy_text
            logger.debug(f"Начало описания вакансии: {vacancy_preview}")
            
            # Сохраняем в файл
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(vacancy_text)
            
            logger.info(f"Описание вакансии сохранено в: {os.path.abspath(output_path)}")
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при генерации описания вакансии: {e}")
            raise
    
    def generate_resumes(self, output_dir, vacancy_text, count=100, start_index=1):
        """
        Генерирует резюме кандидатов на основе описания вакансии и сохраняет их в файлы.
        
        Args:
            output_dir (str): Директория для сохранения файлов с резюме.
            vacancy_text (str): Текст описания вакансии.
            count (int): Количество резюме для генерации.
            start_index (int): Начальный индекс для нумерации файлов.
            
        Returns:
            list: Список путей к созданным файлам.
        """
        logger.info(f"Генерация {count} резюме в директорию: {output_dir}")
        
        # Создаем директорию, если она не существует
        os.makedirs(output_dir, exist_ok=True)
        
        # Логируем абсолютный путь для отладки
        logger.debug(f"Абсолютный путь директории резюме: {os.path.abspath(output_dir)}")
        
        # Распределение качества резюме: 20% высокое, 50% среднее, 30% низкое
        quality_distribution = {
            'high': int(count * 0.2),
            'medium': int(count * 0.5),
            'low': count - int(count * 0.2) - int(count * 0.5)
        }
        
        logger.info(f"Распределение качества резюме: {quality_distribution}")
        
        # Создаем список уровней качества
        quality_levels = []
        for level, amount in quality_distribution.items():
            quality_levels.extend([level] * amount)
        
        # Перемешиваем список
        random.shuffle(quality_levels)
        
        # Генерируем резюме
        resume_files = []
        total_start_time = time.time()
        
        for i in range(count):
            quality_level = quality_levels[i]
            file_name = f"resume_{start_index + i:03d}.txt"
            file_path = os.path.join(output_dir, file_name)
            
            logger.info(f"Генерация резюме {i+1}/{count}: {file_name} (качество: {quality_level})")
            
            start_time = time.time()
            
            try:
                # Генерируем резюме
                resume_text = self.llm_interface.generate_resume(vacancy_text, quality_level)
                
                # Записываем время генерации для мониторинга
                elapsed_time = time.time() - start_time
                logger.info(f"Резюме {file_name} сгенерировано за {elapsed_time:.2f} секунд")
                
                # Логируем первые 100 символов для отладки
                resume_preview = resume_text[:100].replace('\n', ' ').strip() + '...' if len(resume_text) > 100 else resume_text
                logger.debug(f"Начало резюме {file_name}: {resume_preview}")
                
                # Сохраняем в файл
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(resume_text)
                
                resume_files.append(file_path)
                
                # Прогресс выполнения
                if (i+1) % 10 == 0 or i+1 == count:
                    logger.info(f"Прогресс: {i+1}/{count} резюме сгенерировано ({(i+1)/count*100:.1f}%)")
                
                # Задержка между генерациями резюме
                delay = 3
                logger.debug(f"Пауза перед генерацией следующего резюме: {delay} сек")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Ошибка при генерации резюме {file_name}: {e}")
                # Продолжаем с другими резюме
        
        # Общее время выполнения
        total_elapsed_time = time.time() - total_start_time
        average_time_per_resume = total_elapsed_time / max(count, 1)
        
        logger.info(f"Сгенерировано {len(resume_files)} из {count} резюме в директории: {os.path.abspath(output_dir)}")
        logger.info(f"Общее время генерации: {total_elapsed_time:.2f} секунд (в среднем {average_time_per_resume:.2f} секунд на резюме)")
        
        # Сохраним статистику генерации
        self._save_generation_stats(output_dir, {
            'total_resumes': len(resume_files),
            'quality_distribution': quality_distribution,
            'generation_time': total_elapsed_time,
            'average_time_per_resume': average_time_per_resume,
            'timestamp': datetime.now().isoformat()
        })
        
        return resume_files
    
    def _save_generation_stats(self, output_dir, stats):
        """
        Сохраняет статистику генерации резюме в файл.
        
        Args:
            output_dir (str): Директория для сохранения файла статистики.
            stats (dict): Словарь со статистикой генерации.
        """
        try:
            stats_file = os.path.join(output_dir, "generation_stats.txt")
            with open(stats_file, 'w', encoding='utf-8') as f:
                f.write(f"Статистика генерации резюме\n")
                f.write(f"Дата и время: {stats['timestamp']}\n")
                f.write(f"Всего сгенерировано резюме: {stats['total_resumes']}\n")
                f.write(f"Распределение качества:\n")
                for level, amount in stats['quality_distribution'].items():
                    f.write(f"  - {level}: {amount}\n")
                f.write(f"Общее время генерации: {stats['generation_time']:.2f} секунд\n")
                f.write(f"Среднее время на резюме: {stats['average_time_per_resume']:.2f} секунд\n")
            
            logger.info(f"Статистика генерации сохранена в файл: {stats_file}")
        except Exception as e:
            logger.warning(f"Не удалось сохранить статистику генерации: {e}") 