import subprocess
from pathlib import Path

from utils import settings


class Piper:
    def __init__(self):
        self.max_chars = 1000

    def run(self, text, filepath, random_voice: bool = False):
        tts_config = settings.config["settings"]["tts"]
        voice = tts_config.get("piper_voice", "en_US-lessac-medium")
        voice_dir = Path(tts_config.get("piper_voice_dir", "voices/piper"))
        model_path = voice_dir / f"{voice}.onnx"
        config_path = voice_dir / f"{voice}.onnx.json"

        if not model_path.exists() or not config_path.exists():
            raise FileNotFoundError(
                f"Missing Piper voice files for {voice}. "
                f"Expected {model_path} and {config_path}."
            )

        output_path = Path(filepath)
        wav_path = output_path.with_suffix(".wav")
        piper_bin = Path("venvDigger/bin/piper")
        if not piper_bin.exists():
            piper_bin = Path("piper")

        piper_cmd = [
            str(piper_bin),
            "--model",
            str(model_path),
            "--config",
            str(config_path),
            "--output-file",
            str(wav_path),
            "--length-scale",
            str(tts_config.get("piper_length_scale", 1.05)),
            "--noise-scale",
            str(tts_config.get("piper_noise_scale", 0.55)),
            "--noise-w-scale",
            str(tts_config.get("piper_noise_w_scale", 0.75)),
            "--sentence-silence",
            str(tts_config.get("piper_sentence_silence", 0.25)),
        ]

        subprocess.run(piper_cmd, input=text, text=True, check=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(wav_path),
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "2",
                str(output_path),
            ],
            check=True,
        )
        wav_path.unlink(missing_ok=True)
