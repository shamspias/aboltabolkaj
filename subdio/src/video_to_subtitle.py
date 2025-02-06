import os
from moviepy import VideoFileClip
import whisper
from langdetect import detect
from googletrans import Translator
from gtts import gTTS


class VideoToSubtitle:
    """
    A class to handle:
    1. Extracting audio from a video file.
    2. Transcribing the audio with timestamps.
    3. Generating an SRT subtitle file.
    4. (Optional) Translating the text and generating a TTS audio file.
    """

    def __init__(self, model_name="small"):
        """
        Initialize the VideoToSubtitle object.

        :param model_name: Whisper model size/name, e.g. "tiny", "small", "medium", "large".
        """
        self.model_name = model_name
        self.model = None
        self.transcription_segments = []
        self.detected_language = None

    def load_model(self):
        """
        Loads the Whisper model.
        """
        if not self.model:
            print(f"[INFO] Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
        else:
            print("[INFO] Whisper model already loaded.")

    def extract_audio(self, input_video_path, output_audio_path):
        """
        Extract audio from the input video and save as output_audio_path.

        :param input_video_path: Path to the input video file.
        :param output_audio_path: Path to the output audio file.
        """
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input video not found: {input_video_path}")

        print(f"[INFO] Extracting audio from {input_video_path}...")
        video_clip = VideoFileClip(input_video_path)
        video_clip.audio.write_audiofile(output_audio_path, fps=16000)  # 16kHz is a typical speech-model sample rate
        video_clip.close()
        print(f"[INFO] Audio extracted to {output_audio_path}")

    def detect_language(self, sample_text):
        """
        Detect the language from a sample text using langdetect.

        :param sample_text: Text used for language detection.
        :return: Detected language code (e.g., 'en', 'fr', etc.)
        """
        try:
            language_code = detect(sample_text)
            print(f"[INFO] Detected language: {language_code}")
            return language_code
        except Exception:
            print("[WARNING] Could not detect language from sample text.")
            return "unknown"

    def transcribe(self, audio_path):
        """
        Transcribe the audio using the loaded Whisper model.

        :param audio_path: Path to the audio file for transcription.
        """
        if not self.model:
            self.load_model()

        print(f"[INFO] Transcribing audio from {audio_path}...")
        result = self.model.transcribe(audio_path)

        self.transcription_segments = result["segments"]

        # Attempt to detect language from the first segment
        if self.transcription_segments:
            first_text = self.transcription_segments[0].get("text", "")
            self.detected_language = self.detect_language(first_text)

    def generate_srt(self, output_srt_path):
        """
        Generate an SRT file from the transcription segments.

        :param output_srt_path: Path to save the SRT file.
        """
        if not self.transcription_segments:
            print("[WARNING] No transcription segments found. Make sure you transcribe first.")
            return

        print(f"[INFO] Generating SRT file at {output_srt_path}...")
        with open(output_srt_path, "w", encoding="utf-8") as srt_file:
            for index, segment in enumerate(self.transcription_segments, start=1):
                start_time = self._format_timecode(segment["start"])
                end_time = self._format_timecode(segment["end"])
                text = segment["text"].strip()

                srt_file.write(f"{index}\n")
                srt_file.write(f"{start_time} --> {end_time}\n")
                srt_file.write(f"{text}\n\n")

        print("[INFO] SRT file generated successfully.")

    def translate_text(self, text, target_language="en"):
        """
        Translate text to a target language using googletrans.

        :param text: The source text to translate.
        :param target_language: The language code to translate the text into (e.g. 'en', 'fr').
        :return: Translated text.
        """
        translator = Translator()
        try:
            print(f"[INFO] Translating text to '{target_language}'...")
            result = translator.translate(text, dest=target_language)
            return result.text
        except Exception as e:
            print(f"[ERROR] Translation failed: {e}")
            return text  # fallback to original if translation fails

    def generate_translated_audio(self, text, target_language="en", output_audio_path="translated_audio.mp3"):
        """
        Generate an audio file (TTS) from the given text, in the specified language.

        :param text: The text to convert into speech.
        :param target_language: Language code (e.g. 'en', 'fr', 'hi').
        :param output_audio_path: Path for the output audio file.
        """
        print(f"[INFO] Generating TTS audio in '{target_language}'...")
        tts = gTTS(text=text, lang=target_language)
        tts.save(output_audio_path)
        print(f"[INFO] Translated audio saved to {output_audio_path}")

    @staticmethod
    def _format_timecode(seconds):
        """
        Convert float seconds to SRT timecode format: HH:MM:SS,mmm
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds - int(seconds)) * 1000)

        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"
