import speech_recognition as sr
import pyttsx3
from datetime import datetime
import importlib.util


engine = None
_has_sphinx = importlib.util.find_spec("pocketsphinx") is not None
_printed_sphinx_hint = False
try:
    engine = pyttsx3.init()
    if engine:
        engine.setProperty("rate", 175)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)
        engine.say("Text to speech initialized")
        engine.runAndWait()
        print("Text-to-speech engine initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize text-to-speech engine: {e}")
    engine = None


def set_voice_properties(rate: int, volume_percent: int):
    if engine is None:
        return
    engine.setProperty("rate", int(rate))
    engine.setProperty("volume", max(0, min(100, int(volume_percent))) / 100)


def speak(audio):
    try:
        if engine is not None:
            text = str(audio).strip()
            if text:
                engine.say(text)
                engine.runAndWait()
                print(f"Assistant: {text}")
        else:
            print(f"Assistant (TTS Disabled): {audio}")
    except Exception as e:
        print(f"Error in speak function: {e}")
        print(f"Assistant (Error): {audio}")


def take_command(offline_only=False):
    global _printed_sphinx_hint
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.dynamic_energy_threshold = True
        r.energy_threshold = 300
        r.dynamic_energy_adjustment_ratio = 1.5
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognizing...")
            query = ""
            recognition_errors = []
            if not offline_only:
                try:
                    query = r.recognize_google(audio, language="en-in")
                except Exception as e:
                    recognition_errors.append(f"google:{e}")
                    query = ""
            if not query and _has_sphinx:
                try:
                    query = r.recognize_sphinx(audio)
                except Exception as e:
                    recognition_errors.append(f"sphinx:{e}")
                    query = ""
            elif not query and offline_only and not _has_sphinx:
                if not _printed_sphinx_hint:
                    print("Offline mode needs PocketSphinx. Install with: pip install pocketsphinx")
                    _printed_sphinx_hint = True
            if not query:
                if recognition_errors:
                    print(f"Recognition fallback failed: {' | '.join(recognition_errors)}")
                return ""
            print(f"User: {query}")
            return query.lower()
        except sr.UnknownValueError:
            speak("I didn't catch that. Can you say it again?")
            return ""
        except sr.RequestError:
            print("Speech recognition request failed.")
            return ""
        except Exception as e:
            print(f"Error: {e}")
            speak("An error occurred while recognizing speech.")
            return ""


def wish():
    hour = int(datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am your Assip. How can I help you today?")
