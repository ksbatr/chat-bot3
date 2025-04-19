import re
import random
import datetime
import urllib.parse
import http.client
import json
import spacy
from textblob import TextBlob
from translate import Translator
from typing import Optional, Tuple

API_KEY = "API_KEY" 

class ToneAnalyzer:
    def __init__(self):
        """Инициализация переводчика для анализа тональности и загрузка модели spaCy"""
        self.translator = Translator(to_lang="en", from_lang="ru")
        self.nlp = spacy.load("ru_core_news_sm")

    def translate_text(self, text: str) -> str:
        """Переводит текст с русского на английский"""
        try:
            return self.translator.translate(text).lower()
        except Exception as e:
            print(f"Ошибка перевода: {e}")
            return text

    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Анализирует тональность текста и возвращает оценку + эмоцию
        
        Args:
            text: Текст для анализа
            
        Returns:
            Кортеж (оценка тональности, эмоциональная реакция)
        """
        english_text = self.translate_text(text)
        blob = TextBlob(english_text)
        score = blob.sentiment.polarity * 100  
        
      
        if score > 30:
            emotion = random.choice(["Рад это слышать! 😊", "Это прекрасно! 🌟", "Замечательно! 👍"])
        elif score < -30:
            emotion = random.choice(["Мне жаль это слышать 😔", "Надеюсь, всё наладится 🤗", "Понимаю ваши чувства 🫂"])
        else:
            emotion = random.choice(["Интересно 🤔", "Понятно 😐", "Я вас слушаю 👂"])
        
        return score, emotion

    def analyze_text(self, text: str) -> str:
        """Анализирует текст с использованием spaCy и возвращает результаты"""
        doc = self.nlp(text)

       
        nouns = [token.text for token in doc if token.pos_ == "NOUN"]
        verbs = [token.text for token in doc if token.pos_ == "VERB"]
        adjectives = [token.text for token in doc if token.pos_ == "ADJ"]
        
        
        subjects = [token.text for token in doc if "subj" in token.dep_]
        predicates = [token.text for token in doc if "VERB" in token.dep_ or "ROOT" in token.dep_]

        response = (
            f"**Анализ текста:**\n"
            f"Существительные: {', '.join(set(nouns)) or 'Нет'}\n"
            f"Глаголы: {', '.join(set(verbs)) or 'Нет'}\n"
            f"Прилагательные: {', '.join(set(adjectives)) or 'Нет'}\n"
            f"Подлежащее: {', '.join(set(subjects)) or 'Нет'}\n"
            f"Сказуемое: {', '.join(set(predicates)) or 'Нет'}\n"
        )
        
        return response


responses = {
    r"привет": ["Добрый день!", "Привет!", "Здравствуйте!"],
    r"как дела\??": ["Отлично!", "Хорошо", "Всё в порядке", "Неплохо, а у вас?"],
    r"как тебя зовут\??|кто ты такой\??": ["Меня зовут Бот!", "Я просто чат-бот."],
    r"сколько сейчас времени": lambda: datetime.datetime.now().strftime("%H:%M:%S"),
    r"какое сегодня число": lambda: datetime.datetime.now().strftime("%d.%m.%Y"),
    r"какая сейчас погода в городе\s+(.+)\??": "get_weather",
    r"(\d+)\s*([+\-\/*])\s*(\d+)": "calculate",
    r"выход": "exit",
    r"что ты умеешь\??|какие у тебя функции\??|что ты можешь\??": [
        "Я могу отвечать на приветствия, сообщать текущее время и дату.",
        "Я могу говорить о погоде, выполнять поиск в интернете, вычислять простые арифметические выражения и прощаться.",
        "Мои возможности пока ограничены, но я постоянно развиваюсь!"
    ],
    r"спасибо": ["Пожалуйста!", "Всегда рад помочь!", "Не за что."],
    r"хорошо|нормально": ["Отлично!"],
    r"разбери текст (.+)": "analyze_text"
}

def calculate(match):
    try:
        num1 = int(match.group(1))
        operator = match.group(2)
        num2 = int(match.group(3))

        if operator == '+':
            result = num1 + num2
        elif operator == '-':
            result = num1 - num2
        elif operator == '*':
            result = num1 * num2
        elif operator == '/':
            if num2 == 0:
                return "На ноль делить нельзя :(", None
            result = num1 / num2
        else:
            return "Неизвестная операция.", None

        return str(result), None
    except ValueError:
        return "Некорректный ввод чисел.", None

def get_weather(city):
    try:
        conn = http.client.HTTPSConnection("api.openweathermap.org")
        encoded_city = urllib.parse.quote(city)
        url = f"/data/2.5/weather?q={encoded_city}&appid={API_KEY}&units=metric&lang=ru"
        conn.request("GET", url)
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()

        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        return f"В городе {city} сейчас {weather_desc}, температура {temp}°C.", None
    except Exception as e:
        return f"Не удалось получить погоду: {str(e)}", None

# Основная функция обработки сообщений
def process_message(message: str, analyzer: ToneAnalyzer) -> Tuple[str, Optional[float]]:
    message = message.lower().strip()
    
    # Проверка стандартных команд
    for pattern, response in responses.items():
        match = re.search(pattern, message)
        if match:
            if callable(response):
                return response(), None
            elif response == "get_weather":
                return get_weather(match.group(1))
            elif response == "calculate":
                return calculate(match)
            elif response == "exit":
                return "До свидания! Было приятно пообщаться. 👋", None
            elif response == "analyze_text":
                return analyzer.analyze_text(match.group(1)), None
            else:
                return random.choice(response), None
            
    # Анализ тональности для произвольного текста
    score, emotion = analyzer.analyze_sentiment(message)
    
    # Подбираем ответ в зависимости от тональности
    if score > 30:
        response_options = [
            f"{emotion} Ваше сообщение звучит очень позитивно!",
            f"Ваш настрой заразителен! {emotion}",
            f"{emotion} Продолжайте в том же духе!"
        ]
    elif score < -30:
        response_options = [
            f"{emotion} Если вам нужна помощь, я здесь.",
            f"Я чувствую ваше расстройство. {emotion}",
            f"{emotion} Хотите поговорить об этом?"
        ]
    else:
        response_options = [
            f"{emotion} Спасибо за сообщение.",
            f"{emotion} Продолжайте, я вас слушаю.",
            f"Интересно. {emotion}"
        ]
    
    return random.choice(response_options), score

if __name__ == "__main__":
    analyzer = ToneAnalyzer()
    print("Бот: Привет! Я бот с эмоциональным интеллектом. Напишите что-нибудь :)")
    
    while True:
        try:
            user_input = input("Вы: ")
            if user_input.lower() == 'выход':
                print("Бот: До новых встреч! 👋")
                break
                
            response, score = process_message(user_input, analyzer)
            
            if score is not None:
                print(f"Бот: {response} (Тональность: {score:.1f}%)")
            else:
                print(f"Бот: {response}")
                
        except KeyboardInterrupt:
            print("\nБот: Завершаю работу...")
            break
        except Exception as e:
            print(f"Бот: Произошла ошибка: {str(e)}")
