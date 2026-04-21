import json
import os
import re
import time
import webbrowser

import groq
import requests
import wikipedia
from dotenv import load_dotenv

from core_voice import speak

load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


def _load_settings_json():
    global WEATHER_API_KEY, NEWS_API_KEY
    try:
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        if not os.path.exists(settings_path):
            return
        with open(settings_path, "r") as f:
            settings = json.load(f)
        w_key = settings.get("weather_api_key")
        n_key = settings.get("news_api_key")
        if isinstance(w_key, str) and w_key.strip() and not w_key.strip().startswith("#"):
            WEATHER_API_KEY = w_key.strip()
        if isinstance(n_key, str) and n_key.strip() and not n_key.strip().startswith("#"):
            NEWS_API_KEY = n_key.strip()
    except Exception as e:
        print(f"Warning: Could not load settings.json: {e}")


_load_settings_json()


if GROQ_API_KEY:
    try:
        client = groq.Client(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Groq client: {e}")
        client = None
else:
    print("Warning: GROQ_API_KEY not found in environment variables")
    client = None


def set_api_keys(weather_api: str, news_api: str):
    global WEATHER_API_KEY, NEWS_API_KEY
    WEATHER_API_KEY = weather_api
    NEWS_API_KEY = news_api


def get_api_keys():
    return WEATHER_API_KEY, NEWS_API_KEY


def get_chat_response(user_input):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are ASSIP, a virtual assistant with a human-like personality. Keep responses brief and conversational - 1-2 sentences max. Never say 'as an AI' or similar phrases. Use casual language like a helpful friend would. Be direct and to the point.",
                },
                {"role": "user", "content": user_input},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=100,
            top_p=1,
            stream=False,
        )
        response = chat_completion.choices[0].message.content
        print(f"AI: {response}")
        speak(response)
        return response
    except Exception as e:
        error_message = f"I having trouble to connecting my AI services. {str(e)}"
        print(f"Error: {e}")
        speak(error_message)
        return error_message


def search_wikipedia(query):
    try:
        speak("Searching Wikipedia...")
        query = query.replace("wikipedia", "").strip()
        results = wikipedia.summary(query, sentences=2)
        speak("According to Wikipedia")
        print(results)
        speak(results)
    except wikipedia.exceptions.DisambiguationError:
        speak("Your query is too broad. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak("I couldn't find anything on Wikipedia for that.")


def open_website(query):
    domain_pattern = r"\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})\b"
    match = re.search(domain_pattern, query)
    if match:
        domain = match.group(0)
        if not domain.startswith("http"):
            domain = "https://" + domain
        webbrowser.open(domain)
        speak(f"Opening website {domain.split('//')[-1]}")
    else:
        search_url = f"https://www.google.com/search?q={query}"
        webbrowser.open(search_url)
        speak(f"Searching Google for {query}")


def web_search(query):
    search_url = f"https://www.google.com/search?q={query}"
    webbrowser.open(search_url)
    speak(f"Searching the web for {query}")


def extract_category(user_input):
    categories = {
        "sports": ["sports", "cricket", "football", "tennis"],
        "business": ["finance", "stocks", "economy", "business"],
        "technology": ["tech", "gadgets", "AI", "software"],
        "health": ["health", "medicine", "COVID", "fitness"],
        "entertainment": ["movies", "music", "entertainment", "Hollywood"],
    }
    for category, keywords in categories.items():
        if any(word in user_input for word in keywords):
            return category
    return "general"


api_cache = {}


def cache_api_response(func):
    def wrapper(*args, **kwargs):
        cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
        current_time = time.time()
        if cache_key in api_cache and current_time - api_cache[cache_key]["time"] < 600:
            print(f"Using cached result for {func.__name__}")
            return api_cache[cache_key]["result"]
        result = func(*args, **kwargs)
        api_cache[cache_key] = {"result": result, "time": current_time}
        return result

    return wrapper


@cache_api_response
def get_weather(city):
    if not WEATHER_API_KEY or str(WEATHER_API_KEY).strip().startswith("#"):
        message = "Please add a valid Weather API key in Settings."
        speak(message)
        return message
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    try:
        response = requests.get(url, timeout=10)
    except Exception as e:
        message = f"Unable to reach WeatherAPI: {str(e)}"
        speak(message)
        return message
    if response.status_code == 200:
        weather_data = response.json()
        temp = weather_data["current"]["temp_c"]
        condition = weather_data["current"]["condition"]["text"]
        forecast = f"The weather in {city} is {condition} with a temperature of {temp}°C."
        print(forecast)
        speak(forecast)
        return forecast
    try:
        err = response.json().get("error", {})
        err_msg = err.get("message")
        if err_msg:
            message = f"Weather error: {err_msg}"
        else:
            message = f"Weather request failed with code {response.status_code}."
    except Exception:
        message = f"Weather request failed with code {response.status_code}."
    speak(message)
    return message


@cache_api_response
def get_daily_news(api_key, category="general", country="us", page_size=5):
    url = f"https://newsapi.org/v2/top-headlines?country={country}&category={category}&pageSize={page_size}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get("articles", [])
        if articles:
            speak(f"Here are the top {len(articles)} news headlines in {category}.")
            result = []
            for i, article in enumerate(articles, 1):
                headline = f"{i}. {article['title']}"
                print(headline)
                print(f"   Source: {article['source']['name']}")
                speak(article["title"])
                result.append(headline)
            return result
        message = "No news found for this category."
        speak(message)
        return message
    message = "Error fetching news."
    speak(message)
    return message
