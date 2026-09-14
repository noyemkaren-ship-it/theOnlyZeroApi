# ai.py
import json
import random
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from pathlib import Path
import hashlib
import threading
from collections import OrderedDict

class AdvancedConsultant:
    def __init__(self, data_file: str = 'Data.json'):
        self.data_file = data_file
        self.load_data()
        
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), analyzer='char_wb')
        self.conversation_history = []
        self.context = None
        self.context_stack = []
        self.user_preferences = {}
        self.session_id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
        self.confidence_threshold = 0.15
        self.max_context_depth = 3
        
        self.response_cache = OrderedDict()
        self.cache_size = 100
        self.setup_vectorizer()
        
        self.synonyms = self.load_synonyms()
        
        print(f"🚀 ИИ-консультант инициализирован (сессия: {self.session_id})")
        
    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ Данные загружены из {self.data_file}")
            print(f"📚 Версия базы знаний: {self.data.get('version', 'неизвестно')}")
            print(f"🕒 Обновлено: {self.data.get('last_updated', 'неизвестно')}")
        except FileNotFoundError:
            print(f"⚠️ Файл {self.data_file} не найден. Создаю новую базу знаний.")
            self.data = self.create_default_data()
            self.save_data()
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка чтения JSON: {e}")
            self.data = self.create_default_data()
            self.save_data()
    
    def create_default_data(self) -> Dict:
        return {
            "version": "3.0.0",
            "last_updated": datetime.now().isoformat(),
            "metadata": {
                "author": "Advanced AI Consultant",
                "description": "Многофункциональный ИИ-консультант по учебным предметам",
                "capabilities": ["math", "physics", "chemistry", "biology", "language", "history", "geography"]
            },
            "intents": {
                "fallback": {
                    "patterns": ["*"],
                    "responses": [
                        "Извините, я не совсем понял вопрос. Можете переформулировать?",
                        "Могу я уточнить, что именно вас интересует?",
                        "Я специализируюсь на учебных предметах. Спросите о математике, физике, химии или другом предмете."
                    ]
                }
            },
            "small_talk": {
                "greetings": {
                    "patterns": ["привет", "здравствуйте", "добрый день"],
                    "responses": ["Здравствуйте! Чем могу помочь?", "Привет! Задавайте вопрос."]
                },
                "thanks": {
                    "patterns": ["спасибо", "благодарю"],
                    "responses": ["Пожалуйста!", "Рад помочь!"]
                },
                "goodbye": {
                    "patterns": ["пока", "до свидания"],
                    "responses": ["До свидания!", "Всего доброго!"]
                }
            },
            "context_responses": {},
            "learning": {
                "unanswered_questions": [],
                "user_feedback": []
            }
        }
    
    def save_data(self):
        self.data['last_updated'] = datetime.now().isoformat()
        
        backup_file = f"{self.data_file}.backup"
        try:
            if Path(self.data_file).exists():
                import shutil
                shutil.copy2(self.data_file, backup_file)
        except Exception as e:
            print(f"⚠️ Ошибка создания резервной копии: {e}")
        
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"💾 Данные сохранены в {self.data_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    def load_synonyms(self) -> Dict[str, List[str]]:
        """Загрузка словаря синонимов для расширенного поиска"""
        return {
            "математика": ["алгебра", "геометрия", "арифметика", "тригонометрия", "вычисления"],
            "физика": ["механика", "электричество", "термодинамика", "оптика", "ядерная физика"],
            "химия": ["реакция", "вещество", "элемент", "молекула", "атом"],
            "биология": ["клетка", "организм", "днк", "генетика", "эволюция"],
            "русский язык": ["грамматика", "орфография", "пунктуация", "синтаксис"],
            "английский": ["english", "grammar", "vocabulary", "произношение"],
            "история": ["даты", "события", "война", "революция", "правители"],
            "география": ["страны", "континенты", "океаны", "климат", "население"]
        }
    
    def setup_vectorizer(self):
        all_patterns = []
        self.pattern_mapping = {}
        
        # Собираем паттерны с весами
        for intent, intent_data in self.data.get('intents', {}).items():
            if intent != 'fallback' and 'patterns' in intent_data:
                for pattern in intent_data['patterns']:
                    pattern_lower = pattern.lower()
                    all_patterns.append(pattern_lower)
                    self.pattern_mapping[pattern_lower] = {
                        'type': 'intent',
                        'key': intent,
                        'priority': intent_data.get('priority', 1)
                    }
        
        # Паттерны small talk
        for talk_type, talk_data in self.data.get('small_talk', {}).items():
            if 'patterns' in talk_data:
                for pattern in talk_data['patterns']:
                    pattern_lower = pattern.lower()
                    all_patterns.append(pattern_lower)
                    self.pattern_mapping[pattern_lower] = {
                        'type': 'small_talk',
                        'key': talk_type,
                        'priority': talk_data.get('priority', 0.8)
                    }
        
        # Паттерны контекста
        for context_type, context_data in self.data.get('context_responses', {}).items():
            if 'patterns' in context_data:
                for pattern in context_data['patterns']:
                    pattern_lower = pattern.lower()
                    all_patterns.append(pattern_lower)
                    self.pattern_mapping[pattern_lower] = {
                        'type': 'context',
                        'key': context_type,
                        'priority': 1.5
                    }
        
        if all_patterns:
            self.vectorizer.fit(all_patterns)
            self.patterns_matrix = self.vectorizer.transform(all_patterns)
            self.patterns_list = all_patterns
    
    def normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        typos = {
            'превед': 'привет',
            'здарова': 'здравствуй',
            'спс': 'спасибо',
            'плз': 'пожалуйста',
            'ок': 'хорошо'
        }
        for typo, correct in typos.items():
            text = text.replace(typo, correct)
        return text
    
    def expand_with_synonyms(self, text: str) -> str:
        words = text.split()
        expanded = list(words)
        for word in words:
            for key, synonyms in self.synonyms.items():
                if word in synonyms:
                    expanded.append(key)
        return ' '.join(expanded)
    
    def find_best_match(self, user_input: str) -> Tuple[str, str, float]:
        user_input = self.normalize_text(user_input)
        user_input_expanded = self.expand_with_synonyms(user_input)
        
        if self.context and self.context in self.data.get('context_responses', {}):
            context_patterns = self.data['context_responses'][self.context].get('patterns', [])
            if any(pattern.lower() in user_input for pattern in context_patterns):
                return ('context', self.context, 1.0)
        
        best_match = None
        best_score = 0
        
        for intent, intent_data in self.data.get('intents', {}).items():
            if intent != 'fallback' and 'patterns' in intent_data:
                for pattern in intent_data['patterns']:
                    if pattern.lower() in user_input:
                        score = len(pattern) / len(user_input) if len(user_input) > 0 else 1
                        priority = intent_data.get('priority', 1)
                        weighted_score = score * priority
                        if weighted_score > best_score:
                            best_score = weighted_score
                            best_match = ('intent', intent, 1.0)
        
        for talk_type, talk_data in self.data.get('small_talk', {}).items():
            if 'patterns' in talk_data:
                for pattern in talk_data['patterns']:
                    if pattern.lower() in user_input:
                        score = len(pattern) / len(user_input) if len(user_input) > 0 else 1
                        if score > best_score * 0.9:  # Small talk имеет небольшой приоритет
                            best_score = score
                            best_match = ('small_talk', talk_type, 0.9)
        
        try:
            if hasattr(self, 'patterns_matrix'):
                user_vector = self.vectorizer.transform([user_input_expanded])
                similarities = cosine_similarity(user_vector, self.patterns_matrix)[0]
                
                if max(similarities) > self.confidence_threshold:
                    best_match_idx = np.argmax(similarities)
                    similarity_score = similarities[best_match_idx]
                    best_pattern = self.patterns_list[best_match_idx]
                    mapping = self.pattern_mapping.get(best_pattern)
                    if mapping:
                        priority = mapping.get('priority', 1)
                        weighted_similarity = similarity_score * priority
                        if weighted_similarity > best_score:
                            best_match = (mapping['type'], mapping['key'], similarity_score)
        except Exception as e:
            print(f"⚠️ Ошибка в TF-IDF поиске: {e}")
        
        if best_match:
            return best_match
        return ('fallback', 'fallback', 0.0)
    
    def generate_response(self, user_input: str) -> str:
        user_input_original = user_input
        user_input = self.normalize_text(user_input)
        
        cache_key = f"{self.context}:{user_input}"
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]
        
        match_type, match_key, confidence = self.find_best_match(user_input)
        
        response = None
        
        if match_type == 'intent':
            intent_data = self.data['intents'].get(match_key, {})
            responses = intent_data.get('responses', [])
            if responses:
                response = random.choice(responses)
                self.update_context(match_key)
                
                if confidence < 0.5:
                    response += "\n\n(Возможно, я не совсем точно понял вопрос. Уточните, если это не то, что вы искали.)"
        
        elif match_type == 'small_talk':
            talk_data = self.data['small_talk'].get(match_key, {})
            responses = talk_data.get('responses', [])
            if responses:
                response = random.choice(responses)
        
        elif match_type == 'context':
            context_data = self.data['context_responses'].get(match_key, {})
            responses = context_data.get('responses', [])
            if responses:
                response = random.choice(responses)
                self.pop_context()
        
        if response is None:
            response = self.get_fallback_response()
            self.save_unanswered_question(user_input_original)
        
        if len(self.response_cache) >= self.cache_size:
            self.response_cache.popitem(last=False)
        self.response_cache[cache_key] = response
        
        self.conversation_history.append((user_input_original, response))
        
        return response
    
    def update_context(self, intent: str):
        if intent == 'greetings':
            self.push_context('after_greeting')
        elif intent in ['services', 'about_company', 'pricing', 'contact']:
            self.push_context('after_info')
        elif intent in ['math_basics', 'algebra', 'geometry', 'trigonometry']:
            self.push_context('math_context')
        elif intent.startswith('physics_'):
            self.push_context('physics_context')
        elif intent.startswith('chemistry_'):
            self.push_context('chemistry_context')
        elif intent.startswith('biology_'):
            self.push_context('biology_context')
    
    def push_context(self, context: str):
        """Добавление контекста в стек"""
        if len(self.context_stack) < self.max_context_depth:
            self.context_stack.append(self.context)
            self.context = context
    
    def pop_context(self):
        """Возврат к предыдущему контексту"""
        if self.context_stack:
            self.context = self.context_stack.pop()
        else:
            self.context = None
    
    def get_fallback_response(self) -> str:
        fallback_responses = self.data['intents'].get('fallback', {}).get('responses', [
            "Извините, я не совсем понял вопрос.",
            "Могу я уточнить, что вас интересует?",
            "Я специализируюсь на учебных предметах. Спросите о математике, физике, химии и т.д."
        ])
        
        response = random.choice(fallback_responses)
        response += "\n\nЯ могу помочь с:\n• Математикой\n• Физикой\n• Химией\n• Биологией\n• Русским языком\n• Английским языком\n• Историей\n• Географией\n• Информатикой\n• Литературой"
        
        return response
    
    def save_unanswered_question(self, question: str):
        if 'learning' not in self.data:
            self.data['learning'] = {'unanswered_questions': []}
        
        self.data['learning']['unanswered_questions'].append({
            'question': question,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.data['learning']['unanswered_questions']) > 100:
            self.data['learning']['unanswered_questions'] = \
                self.data['learning']['unanswered_questions'][-100:]
    
    def add_intent(self, intent_name: str, patterns: List[str], responses: List[str], priority: float = 1.0):
        if 'intents' not in self.data:
            self.data['intents'] = {}
        
        self.data['intents'][intent_name] = {
            'patterns': patterns,
            'responses': responses,
            'priority': priority
        }
        
        self.save_data()
        self.setup_vectorizer()
        print(f"✅ Интент '{intent_name}' добавлен с приоритетом {priority}")
    
    def add_small_talk(self, talk_type: str, patterns: List[str], responses: List[str]):
        if 'small_talk' not in self.data:
            self.data['small_talk'] = {}
        
        self.data['small_talk'][talk_type] = {
            'patterns': patterns,
            'responses': responses
        }
        
        self.save_data()
        self.setup_vectorizer()
        print(f"✅ Small talk '{talk_type}' добавлен")
    
    def get_statistics(self) -> Dict:
        """Расширенная статистика"""
        total_patterns = sum(
            len(intent_data.get('patterns', [])) 
            for intent_data in self.data.get('intents', {}).values()
        ) + sum(
            len(talk_data.get('patterns', [])) 
            for talk_data in self.data.get('small_talk', {}).values()
        )
        
        total_responses = sum(
            len(intent_data.get('responses', [])) 
            for intent_data in self.data.get('intents', {}).values()
        ) + sum(
            len(talk_data.get('responses', [])) 
            for talk_data in self.data.get('small_talk', {}).values()
        )
        
        stats = {
            'total_intents': len(self.data.get('intents', {})),
            'total_small_talk': len(self.data.get('small_talk', {})),
            'total_patterns': total_patterns,
            'total_responses': total_responses,
            'unanswered_questions': len(self.data.get('learning', {}).get('unanswered_questions', [])),
            'conversation_history': len(self.conversation_history),
            'cache_size': len(self.response_cache),
            'session_id': self.session_id,
            'version': self.data.get('version', 'unknown'),
            'last_updated': self.data.get('last_updated', 'unknown')
        }
        return stats
    
    def get_conversation_history(self) -> List[Tuple[str, str]]:
        return self.conversation_history
    
    def clear_conversation_history(self):
        self.conversation_history = []
        self.context = None
        self.context_stack = []
        self.response_cache.clear()
        print("🔄 История диалога очищена")
    
    def export_conversation(self, filename: str = "conversation_log.txt"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Сессия: {self.session_id}\n")
                f.write(f"Дата: {datetime.now().isoformat()}\n")
                f.write("-" * 50 + "\n\n")
                
                for i, (question, answer) in enumerate(self.conversation_history, 1):
                    f.write(f"Вопрос {i}: {question}\n")
                    f.write(f"Ответ {i}: {answer}\n")
                    f.write("-" * 50 + "\n")
            
            print(f"📝 Диалог экспортирован в {filename}")
        except Exception as e:
            print(f"❌ Ошибка экспорта: {e}")
    
    def analyze_user_input(self, text: str) -> Dict[str, Any]:
        """Анализ ввода пользователя"""
        analysis = {
            'length': len(text),
            'words': len(text.split()),
            'has_question': '?' in text or any(word in text.lower() for word in ['что', 'как', 'почему', 'когда', 'где', 'кто']),
            'sentiment': self.analyze_sentiment(text),
            'language': self.detect_language(text)
        }
        return analysis
    
    def analyze_sentiment(self, text: str) -> str:
        """Простой анализ тональности"""
        positive_words = ['спасибо', 'отлично', 'хорошо', 'супер', 'класс', 'помогло', 'понял']
        negative_words = ['плохо', 'не понял', 'ошибка', 'неправильно', 'ужасно', 'отвратительно']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'
    
    def detect_language(self, text: str) -> str:
        cyrillic_chars = len(re.findall(r'[а-яА-Я]', text))
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if cyrillic_chars > latin_chars:
            return 'russian'
        elif latin_chars > cyrillic_chars:
            return 'english'
        return 'mixed'

consultant = AdvancedConsultant()
