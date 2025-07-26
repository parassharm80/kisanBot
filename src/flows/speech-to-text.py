import pyaudio
import wave
from google.cloud import speech
from google.cloud.speech import RecognitionConfig, RecognitionAudio


def list_microphones():
    p = pyaudio.PyAudio()
    print("Available Microphones:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"[{i}] {info['name']}")
    p.terminate()

def record_audio(device_index: int, seconds=5, filename="output.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK)

    print(f"Recording from device {device_index}...")
    frames = [stream.read(CHUNK) for _ in range(0, int(RATE / CHUNK * seconds))]
    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return filename


def speech_to_text(file_path: str):
    client = speech.SpeechClient()

    with open(file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="hi-IN",                     # Hindi (India)
        model="command_and_search"                 # Use command_and_search model
    )

    return client.recognize(config=config, audio=audio)
def print_response(response: speech.RecognizeResponse):
    for result in response.results:
        best = result.alternatives[0]
        print("-" * 80)
        print(f"Transcript: {best.transcript}")
        print(f"Confidence: {best.confidence:.0%}")

if __name__ == "__main__":
    list_microphones()
    choice = int(input("Enter the device index to use for recording: "))
    audio_file = record_audio(choice)
    response = speech_to_text(audio_file)
    print_response(response)