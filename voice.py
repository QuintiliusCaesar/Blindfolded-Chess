import whisper
import sounddevice as sd
import wavio
import tempfile

import speech_recognition as sr

model = whisper.load_model("base")  # fast but accurate

def listen_and_print():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        print("🎙 Listening...")
        audio = r.listen(source)
    try:
        text = r.recognize_whisper(audio)
        print(f"🎯 Recognized: {text}")
    except sr.UnknownValueError:
        print("❓ Could not understand audio")
    except sr.RequestError as e:
        print(f"❗ Could not request results; {e}")

def listen_for_move(duration=4, samplerate=44100):
    print("🎙 Listening for your move...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        wavio.write(f.name, recording, samplerate, sampwidth=2)
        result = model.transcribe(f.name)

    move_text = result["text"].strip()
    print(f"🎯 Recognized: {move_text}")
    return move_text

def parse_move(text, board):
    text = text.lower().replace("to", "").replace(" ", "")
    try:
        move = board.parse_san(text)
    except:
        try:
            move = board.parse_uci(text)
        except:
            return None
    return move

listen_and_print()