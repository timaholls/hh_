#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для взаимодействия с языковой моделью (LLM) через OpenAI API.
Обеспечивает интерфейс для отправки запросов к LLM и обработки ответов.
"""

import os
import sys
import logging
import json
import time
import random
import re
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные окружения, в том числе API ключ
load_dotenv()

logger = logging.getLogger(__name__)


class LLMInterface:
    """
    Класс для взаимодействия с языковой моделью (LLM) через OpenAI API.
    Обеспечивает методы для генерации текста и анализа резюме.
    
    Attributes:
        model (str): Название модели для использования.
        api_key (str): API ключ для доступа к OpenAI API.
        client (OpenAI): Клиент для работы с OpenAI API.
    """
    
    def __init__(self, model="gpt-3.5-turbo", timeout=60):
        """
        Инициализирует интерфейс для взаимодействия с OpenAI API.
        
        Args:
            model (str): Название модели для использования.
            timeout (int): Таймаут запроса в секундах.
        """
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.error("API ключ OpenAI не найден. Убедитесь, что переменная среды OPENAI_API_KEY установлена.")
            raise ValueError("API ключ OpenAI не найден")
        
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"Инициализирован LLM интерфейс с OpenAI API, модель: {model}")
    
    def generate_text(self, prompt, max_retries=3, temperature=0.7):
        """
        Отправляет запрос к OpenAI API и получает сгенерированный текст.
        
        Args:
            prompt (str): Промпт для генерации текста.
            max_retries (int): Максимальное количество попыток при ошибке.
            temperature (float): Параметр температуры для генерации (0.0 - 1.0).
            
        Returns:
            str: Сгенерированный текст.
            
        Raises:
            Exception: Если не удалось получить ответ от API.
        """
        messages = [{"role": "user", "content": prompt}]
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Отправка запроса к OpenAI API, попытка {attempt+1}/{max_retries}")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature
                )
                
                # Получаем текст из ответа
                if response and response.choices:
                    text = response.choices[0].message.content
                    if text and text.strip():
                        return text.strip()
                
                logger.warning("Получен пустой ответ от OpenAI API")
                
            except Exception as e:
                logger.warning(f"Ошибка при запросе к OpenAI API: {e}")
                
            # Экспоненциальная задержка перед следующей попыткой
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"Ожидание {wait_time:.2f} секунд перед следующей попыткой")
            time.sleep(wait_time)
        
        # Если все попытки не удались
        logger.error(f"Не удалось получить ответ от OpenAI API после {max_retries} попыток")
        
        # В случае анализа резюме будет использована резервная функция analyze_with_mock_llm
        return ""
    
    def generate_vacancy(self):
        """
        Генерирует описание вакансии с помощью OpenAI API.
        
        Returns:
            str: Сгенерированное описание вакансии.
        """
        prompt = """
        Сгенерируй детальное описание вакансии на должность Python-разработчика.
        
        Описание должно включать:
        1. Название должности
        2. О компании (краткое описание)
        3. Обязанности
        4. Требования (обязательные и желательные навыки)
        5. Условия работы
        
        Сделай описание реалистичным, с конкретными техническими требованиями и навыками.
        """
        
        logger.info("Генерация описания вакансии с помощью OpenAI API...")
        return self.generate_text(prompt, temperature=0.8)
    
    def generate_resume(self, vacancy_text, quality_level=None):
        """
        Генерирует резюме кандидата на основе описания вакансии.
        
        Args:
            vacancy_text (str): Текст описания вакансии.
            quality_level (str, optional): Уровень соответствия резюме вакансии
                ('low', 'medium', 'high' или None для случайного выбора).
                
        Returns:
            str: Сгенерированное резюме.
        """
        quality_instructions = {
            'low': 'Резюме должно соответствовать вакансии на низком уровне, с небольшим количеством совпадений по требуемым навыкам и опыту.',
            'medium': 'Резюме должно соответствовать вакансии на среднем уровне, с частичным совпадением по требуемым навыкам и опыту.',
            'high': 'Резюме должно соответствовать вакансии на высоком уровне, с хорошим совпадением по требуемым навыкам и опыту.'
        }
        
        if quality_level is None:
            quality_level = random.choice(['low', 'medium', 'high'])
        
        quality_instruction = quality_instructions.get(quality_level, quality_instructions['medium'])
        
        prompt = f"""
        Сгенерируй резюме кандидата для следующей вакансии:
        
        {vacancy_text}
        
        {quality_instruction}
        
        Резюме должно включать:
        1. ФИО кандидата
        2. Контактная информация (email, телефон)
        3. Цель (краткое описание желаемой позиции)
        4. Опыт работы (в обратном хронологическом порядке)
        5. Образование
        6. Навыки
        7. Дополнительная информация (языки, сертификаты и т.д.)
        
        Сделай резюме реалистичным, с разным уровнем соответствия требованиям вакансии.
        """
        
        # Для разных уровней качества используем разную температуру
        temperature = {
            'low': 0.9,     # Выше для более творческих результатов (меньше совпадений)
            'medium': 0.7,  # Средняя температура
            'high': 0.5     # Ниже для более предсказуемых результатов (больше совпадений)
        }.get(quality_level, 0.7)
        
        logger.info(f"Генерация резюме с уровнем соответствия: {quality_level}, температура: {temperature}")
        return self.generate_text(prompt, temperature=temperature)
    
    def analyze_resume(self, resume_text, vacancy_text):
        """
        Анализирует соответствие резюме вакансии с помощью OpenAI API.
        
        Args:
            resume_text (str): Текст резюме.
            vacancy_text (str): Текст вакансии.
            
        Returns:
            dict: Словарь с результатами анализа:
                - score (float): Оценка соответствия от 0 до 10.
                - justification (str): Обоснование оценки.
        """
        prompt = f"""
        Проанализируй соответствие резюме кандидата требованиям вакансии.
        
        ВАКАНСИЯ:
        {vacancy_text}
        
        РЕЗЮМЕ:
        {resume_text}
        
        Оцени соответствие резюме вакансии по шкале от 0 до 10, где 0 - полное несоответствие, 10 - идеальное соответствие.
        Приведи краткое обоснование оценки, включая сильные и слабые стороны кандидата относительно требований вакансии.
        
        Выдай результат в формате JSON с полями:
        - score: число от 0 до 10
        - justification: строка с обоснованием
        """
        
        logger.info("Анализ соответствия резюме вакансии с помощью OpenAI API...")
        
        try:
            # Используем низкую температуру для более стабильных и предсказуемых результатов
            response = self.generate_text(prompt, temperature=0.2)
            
            # Попытка распарсить JSON из ответа
            try:
                # Извлечение JSON из ответа (если он находится внутри текста)
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response.strip()
                    
                result = json.loads(json_str)
                
                # Проверяем наличие необходимых полей
                if 'score' not in result or 'justification' not in result:
                    logger.warning("В ответе от API отсутствуют необходимые поля")
                    return analyze_with_mock_llm(resume_text, vacancy_text)
                
                # Преобразуем score в число, если это строка
                if isinstance(result['score'], str):
                    try:
                        result['score'] = float(result['score'])
                    except ValueError:
                        # Если не удалось преобразовать, используем запасной метод
                        logger.warning("Не удалось преобразовать оценку в число")
                        return analyze_with_mock_llm(resume_text, vacancy_text)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON из ответа: {e}")
                return analyze_with_mock_llm(resume_text, vacancy_text)
                
        except Exception as e:
            logger.error(f"Ошибка при анализе резюме через OpenAI API: {e}")
            return analyze_with_mock_llm(resume_text, vacancy_text)


def analyze_with_mock_llm(resume_text, vacancy_text):
    """
    Имитация анализа резюме без использования реальной языковой модели.
    Используется как запасной метод в случае недоступности OpenAI API.
    
    Args:
        resume_text (str): Текст резюме.
        vacancy_text (str): Текст вакансии.
        
    Returns:
        dict: Словарь с результатами анализа:
            - score (float): Оценка соответствия от 0 до 10.
            - justification (str): Обоснование оценки.
    """
    logger.info("Использование имитации LLM для анализа резюме")
    
    # Слова, которые указывают на соответствие требованиям
    resume_lower = resume_text.lower()
    vacancy_lower = vacancy_text.lower()
    
    # Извлечем ключевые слова из вакансии
    key_techs = [
        'python', 'django', 'flask', 'fastapi', 'rest', 'api', 
        'sql', 'postgresql', 'mysql', 'mongodb', 'nosql', 'redis',
        'docker', 'kubernetes', 'git', 'ci/cd', 'linux', 'aws', 'azure',
        'microservices', 'tdd', 'unit tests', 'pytest', 'asyncio'
    ]
    
    # Подсчет ключевых слов
    keyword_matches = 0
    for tech in key_techs:
        if tech in resume_lower:
            keyword_matches += 1
    
    # Оценка опыта работы
    experience = 0
    if 'senior' in resume_lower or '5+ лет' in resume_lower or '5 лет' in resume_lower:
        experience = 3
    elif 'middle' in resume_lower or '3+ лет' in resume_lower or '3 года' in resume_lower:
        experience = 2
    elif 'junior' in resume_lower or '1+ год' in resume_lower or '2 года' in resume_lower:
        experience = 1
    
    # Проверка образования
    education = 0
    if 'магистр' in resume_lower or 'высшее' in resume_lower:
        education = 2
    elif 'бакалавр' in resume_lower or 'колледж' in resume_lower:
        education = 1
    
    # Расчет итоговой оценки
    max_keywords = len(key_techs)
    keyword_score = (keyword_matches / max_keywords) * 6  # до 6 баллов за ключевые навыки
    experience_score = experience  # до 3 баллов за опыт
    education_score = education / 2  # до 1 балла за образование
    
    total_score = keyword_score + experience_score + education_score
    # Ограничим оценку диапазоном от 0 до 10
    total_score = min(max(total_score, 0), 10)
    
    # Формирование обоснования
    justification = f"Кандидат соответствует {keyword_matches} из {max_keywords} ключевых технологий. "
    
    if experience == 3:
        justification += "Имеет значительный опыт работы (уровень Senior). "
    elif experience == 2:
        justification += "Имеет средний опыт работы (уровень Middle). "
    elif experience == 1:
        justification += "Имеет небольшой опыт работы (уровень Junior). "
    else:
        justification += "Опыт работы не указан или минимален. "
    
    if education == 2:
        justification += "Имеет высшее образование или степень магистра. "
    elif education == 1:
        justification += "Имеет степень бакалавра или образование колледжа. "
    else:
        justification += "Информация об образовании отсутствует. "
    
    return {
        'score': round(total_score, 2),
        'justification': justification
    } 