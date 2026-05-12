import random

from elevenlabs import VoiceSettings, save
from elevenlabs.client import ElevenLabs

from utils import settings


class elevenlabs:
    def __init__(self):
        self.max_chars = 2500
        self.client: ElevenLabs = None

    def run(self, text, filepath, random_voice: bool = False):
        if self.client is None:
            self.initialize()
        if random_voice:
            voice = self.randomvoice()
        else:
            voice = str(settings.config["settings"]["tts"]["elevenlabs_voice_name"]).capitalize()

        tts_config = settings.config["settings"]["tts"]
        voice_settings = VoiceSettings(
            stability=float(tts_config.get("elevenlabs_stability", 0.45)),
            similarity_boost=float(tts_config.get("elevenlabs_similarity_boost", 0.8)),
            style=float(tts_config.get("elevenlabs_style", 0.25)),
            use_speaker_boost=bool(tts_config.get("elevenlabs_speaker_boost", True)),
        )
        audio = self.client.generate(
            text=text,
            voice=voice,
            voice_settings=voice_settings,
            model=tts_config.get("elevenlabs_model", "eleven_multilingual_v2"),
            output_format="mp3_44100_128",
        )
        save(audio=audio, filename=filepath)

    def initialize(self):
        if settings.config["settings"]["tts"]["elevenlabs_api_key"]:
            api_key = settings.config["settings"]["tts"]["elevenlabs_api_key"]
        else:
            raise ValueError(
                "You didn't set an Elevenlabs API key! Please set the config variable ELEVENLABS_API_KEY to a valid API key."
            )

        self.client = ElevenLabs(api_key=api_key)

    def randomvoice(self):
        if self.client is None:
            self.initialize()
        return random.choice(self.client.voices.get_all().voices).voice_name
