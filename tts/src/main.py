import subprocess
import wave

from piper import PiperVoice, SynthesisConfig

voice = PiperVoice.load("en_US-lessac-medium.onnx")
syn_config = SynthesisConfig(
    length_scale=1.3,
)
device_index = 1
tts_file = "text.wav"
SAMPLE_RATE = voice.config.sample_rate


def play_text(device: int, text: str, ok_google: bool = True):
    with wave.open(tts_file, "wb") as file:
        voice.synthesize_wav(text, file, syn_config=syn_config)
    if ok_google:
        subprocess.run(
            ["aplay", "-D", f"plughw:{device},0", "ok-google.wav"], check=True
        )
    subprocess.run(["aplay", "-D", f"plughw:{device},0", tts_file], check=True)


with wave.open("ok-google.wav", "wb") as file:
    voice.synthesize_wav("Ok Google", file, syn_config=syn_config)

play_text(1, "Ok Google")
play_text(1, "Go to TV home screen")
