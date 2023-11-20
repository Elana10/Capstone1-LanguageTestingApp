from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
from openai import OpenAI

client = OpenAI(
    api_key = ("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")
)


def generate_and_play_audio(user_input):
    audio_folder = Path(__file__).parent /"audio"
    speech_file_path = audio_folder / "speech.mp3"

    response = client.audio.speech.create(
        model = "tts-1-hd",
        voice="nova",
        input=user_input,
        speed=1
    )

    response.stream_to_file(speech_file_path)
    audio = AudioSegment.from_mp3(speech_file_path)
    play(audio)