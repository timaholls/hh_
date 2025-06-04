#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для анализа резюме и выбора лучшего кандидата.
Оценивает соответствие резюме требованиям вакансии.
"""

import logging
import time
import os

logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """
    Класс для анализа резюме и выбора лучшего кандидата.
    
    Attributes:
        llm_interface: Интерфейс для взаимодействия с языковой моделью.
    """
    
    def __init__(self, llm_interface):
        """
        Инициализирует анализатор резюме.
        
        Args:
            llm_interface: Интерфейс для взаимодействия с языковой моделью.
        """
        self.llm_interface = llm_interface
        logger.info("Инициализирован анализатор резюме")
    
    def analyze_resume(self, resume_text, vacancy_text):
        """
        Анализирует соответствие резюме вакансии.
        
        Args:
            resume_text (str): Текст резюме.
            vacancy_text (str): Текст вакансии.
            
        Returns:
            dict: Словарь с результатами анализа:
                - score (float): Оценка соответствия от 0 до 10.
                - justification (str): Обоснование оценки.
        """
        logger.info("Анализ соответствия резюме вакансии")
        
        # Логируем первые 100 символов резюме для отладки
        resume_preview = resume_text[:100].replace('\n', ' ').strip() + '...' if len(resume_text) > 100 else resume_text
        logger.debug(f"Анализ резюме начинающегося с: {resume_preview}")
        
        start_time = time.time()
        
        try:
            # Используем LLM для анализа
            result = self.llm_interface.analyze_resume(resume_text, vacancy_text)
            
            # Проверяем наличие необходимых полей в результате и что justification не пустой
            if ('score' not in result or 
                'justification' not in result or 
                not result.get('justification') or 
                result.get('justification') == 'Python'):
                logger.warning("В результате анализа отсутствуют необходимые поля или обоснование некорректно")
                result = self._fallback_analysis(resume_text, vacancy_text)
            
            # Измеряем время анализа для мониторинга производительности
            elapsed_time = time.time() - start_time
            logger.info(f"Анализ резюме выполнен за {elapsed_time:.2f} секунд. Оценка: {result.get('score', 0)}/10")
            
            # Добавляем задержку после каждого анализа
            time.sleep(3)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при анализе резюме: {e}")
            elapsed_time = time.time() - start_time
            logger.info(f"Анализ резюме завершился с ошибкой за {elapsed_time:.2f} секунд")
            
            # В случае ошибки используем запасной метод анализа
            return self._fallback_analysis(resume_text, vacancy_text)
    
    def _fallback_analysis(self, resume_text, vacancy_text):
        """
        Запасной метод анализа резюме, используется при ошибках основного метода.
        
        Args:
            resume_text (str): Текст резюме.
            vacancy_text (str): Текст вакансии.
            
        Returns:
            dict: Словарь с результатами анализа:
                - score (float): Оценка соответствия от 0 до 10.
                - justification (str): Обоснование оценки.
        """
        logger.info("Использование запасного метода анализа резюме")
        
        try:
            # Импортируем функцию для имитации LLM из модуля llm_interface
            from llm_interface import analyze_with_mock_llm
            start_time = time.time()
            result = analyze_with_mock_llm(resume_text, vacancy_text)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Запасной анализ выполнен за {elapsed_time:.2f} секунд. Оценка: {result.get('score', 0)}/10")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при запасном анализе резюме: {e}")
            
            # В случае полного отказа возвращаем нулевую оценку
            return {
                'score': 0.0,
                'justification': f"Не удалось проанализировать резюме: {e}"
            }
    
    def select_best_candidate(self, results):
        """
        Выбирает лучшего кандидата из результатов анализа.
        
        Args:
            results (list): Список словарей с результатами анализа для каждого резюме.
                Каждый словарь должен содержать поля:
                - file_name (str): Имя файла резюме.
                - score (float): Оценка соответствия от 0 до 10.
                - justification (str): Обоснование оценки.
                
        Returns:
            dict: Словарь с информацией о лучшем кандидате или None, если список пуст.
        """
        if not results:
            logger.warning("Нет результатов для выбора лучшего кандидата")
            return None
        
        # Сортируем результаты по оценке (по убыванию)
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Выбираем лучшего кандидата
        best_candidate = sorted_results[0]
        
        logger.info(f"Выбран лучший кандидат: {best_candidate['file_name']} с оценкой {best_candidate['score']}")
        
        return best_candidate
    
    def select_top_candidates(self, results, top_n=5):
        """
        Выбирает топ-N лучших кандидатов из результатов анализа.
        
        Args:
            results (list): Список словарей с результатами анализа для каждого резюме.
            top_n (int): Количество лучших кандидатов для выбора.
                
        Returns:
            list: Список словарей с информацией о лучших кандидатах.
        """
        if not results:
            logger.warning("Нет результатов для выбора лучших кандидатов")
            return []
        
        # Сортируем результаты по оценке (по убыванию)
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Выбираем топ-N кандидатов
        top_candidates = sorted_results[:min(top_n, len(sorted_results))]
        
        logger.info(f"Выбрано {len(top_candidates)} лучших кандидатов")
        logger.debug(f"Топ кандидаты: {', '.join([c['file_name'] for c in top_candidates])}")
        
        return top_candidates 