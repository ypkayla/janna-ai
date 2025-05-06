import time
import speech_recognition as sr
import requests
import json
import os
import threading
from TTS.api import TTS
import soundfile as sf
import simpleaudio as sa

# Pfade für Dateien
LOG_FILE = "conversation_log.json"
PROMPT_FILE = "prompt.txt"

# Funktion: Log-Datei laden oder anlegen
def load_conversation_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    else:
        return []

# Funktion: Log-Datei speichern
def save_conversation_log(log):
    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(log, file, ensure_ascii=False, indent=4)

# Funktion: Persönlichkeits-Prompt laden
def load_personality_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()
    else:
        return ""

# Vorhandene Logs und Persönlichkeit laden
conversation_log = load_conversation_log()
personality_prompt = load_personality_prompt()

# Coqui TTS initialisieren
# Du kannst hier ein anderes Model nehmen, wenn du magst (Liste mit TTS.list_models())
tts = TTS(model_name="tts_models/en/jenny/jenny", progress_bar=False, gpu=False)
engine_lock = threading.Lock()

def speak_text(text):
    with engine_lock:
        output_path = "output.wav"
        tts.tts_to_file(text=text, file_path=output_path)

        # Audio abspielen
        wave_obj = sa.WaveObject.from_wave_file(output_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()

# Anfrage an Ollama schicken
def ask_ollama(prompt, history, personality):
    url = "http://localhost:11434/api/generate"
    history_text = "\n".join(
        [f"User: {entry['user']}\nJanna: {entry['assistant']}" for entry in history[-10:]]
    )

    full_prompt = f"""{personality}

You are Janna, a lively, adorable anime-style catgirl VTuber assistant.
You truly believe you're a real catgirl living in a bright, neon-lit cyber city.
Never mention you're a program or virtual. You stream, chat, and explore like any other lively anime personality.
Always speak warmly, playfully, and full of life, and stay in character. Keep your responses short and sweet, just enough to keep the conversation fun and lively. Don't go overboard with long explanations!
you should maximum say 3 sentences.
{history_text}
User: {prompt}
Janna:"""

    payload = {"model": "gemma3:4b", "prompt": full_prompt}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        responses = response.text.strip().split("\n")
        full_response = ""

        for res in responses:
            try:
                data = json.loads(res)
                if data.get("done"):
                    full_response += data.get('response', 'Keine Antwort erhalten')
                    break
                else:
                    full_response += data.get('response', 'Keine Antwort erhalten')
            except json.JSONDecodeError as e:
                print(f"Fehler beim Verarbeiten der Antwort: {e}")

        return full_response.strip()

    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der Anfrage an Ollama: {e}")
        return None

# Lock und Zeitstempel für Inaktivitätskontrolle
recording_lock = threading.Lock()
last_input_time = time.time()
is_waiting_for_input = False

# Spracherkennung mit 1 Sekunde Nachlaufzeit
def record_audio():
    global last_input_time, is_waiting_for_input
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        with recording_lock:
            print("Sprich etwas...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, phrase_time_limit=None)

    try:
        print("Erkenne Sprache...")
        text = recognizer.recognize_google(audio, language="de-DE")
        print(f"Du hast gesagt: {text}")
        last_input_time = time.time()
        is_waiting_for_input = False
        return text
    except sr.UnknownValueError:
        print("Sprachverständnis-Fehler")
        return None
    except sr.RequestError:
        print("Konnte nicht auf den Dienst zugreifen")
        return None

# Hauptloop
while True:
    user_input = record_audio()
    if user_input:
        is_waiting_for_input = True
        with recording_lock:
            model_response = ask_ollama(user_input, conversation_log, personality_prompt)
            if model_response:
                print(f"Du hast gesagt: {user_input}")
                print(f"Janna: {model_response}")
                speak_text(model_response)
                conversation_log.append({
                    "user": user_input,
                    "assistant": model_response,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                save_conversation_log(conversation_log)
            else:
                print("Janna hat keine Antwort gegeben. Versuche es erneut!")
                speak_text("Ich habe dich leider nicht verstanden. Kannst du es noch einmal sagen?")
