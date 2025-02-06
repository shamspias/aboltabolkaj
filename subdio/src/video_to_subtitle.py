import os
from moviepy import VideoFileClip
import whisper
from langdetect import detect
from googletrans import Translator  # or your translation library
from gtts import gTTS


class VideoToSubtitle:
    """
    A class to handle:
    1. Extracting audio from a video file.
    2. Transcribing the audio with timestamps (Whisper).
    3. Generating two SRT files:
       - Original language subtitle
       - Translated language subtitle
    4. Generating a TTS audio file from the translated text (optional).
    """

    def __init__(self, model_name="small"):
        """
        :param model_name: Whisper model size/name (e.g., "tiny", "small", "medium", "large").
        """
        self.model_name = model_name
        self.model = None
        self.transcription_segments = []
        self.detected_language = None

    def load_model(self):
        """
        Loads the Whisper model for transcription.
        """
        if not self.model:
            print(f"[INFO] Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
        else:
            print("[INFO] Whisper model already loaded.")

    def extract_audio(self, input_video_path, output_audio_path):
        """
        Extracts audio from the input video using MoviePy.
        """
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input video not found: {input_video_path}")

        print(f"[INFO] Extracting audio from {input_video_path}...")
        video_clip = VideoFileClip(input_video_path)
        video_clip.audio.write_audiofile(output_audio_path, fps=16000)
        video_clip.close()
        print(f"[INFO] Audio extracted to {output_audio_path}")

    def detect_language(self, sample_text):
        """
        Detects the language from a sample of the transcription (langdetect).
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
        Transcribes the audio using Whisper.
        """
        if not self.model:
            self.load_model()

        print(f"[INFO] Transcribing audio from {audio_path}...")
        result = self.model.transcribe(audio_path)
        self.transcription_segments = result["segments"]  # list of dicts: {id, start, end, text, ...}

        # Attempt language detection from the first non-empty segment
        if self.transcription_segments:
            first_text = self.transcription_segments[0].get("text", "")
            self.detected_language = self.detect_language(first_text)
        else:
            self.detected_language = "unknown"

    def generate_srt(self, segments, output_srt_path):
        """
        Generate an SRT file from a given list of segments.

        :param segments: A list of dicts with 'start', 'end', 'text'.
        :param output_srt_path: Path to save the SRT file.
        """
        if not segments:
            print("[WARNING] No segments provided. Skipping SRT generation.")
            return

        print(f"[INFO] Generating SRT file at {output_srt_path}...")
        with open(output_srt_path, "w", encoding="utf-8") as srt_file:
            for index, segment in enumerate(segments, start=1):
                start_time = self._format_timecode(segment["start"])
                end_time = self._format_timecode(segment["end"])
                text = segment["text"].strip()

                srt_file.write(f"{index}\n")
                srt_file.write(f"{start_time} --> {end_time}\n")
                srt_file.write(f"{text}\n\n")

        print(f"[INFO] SRT file generated: {output_srt_path}")

    def translate_segments(self, segments, target_language="en"):
        """
        Translate each segment's text into the target language.

        :param segments: Original segments (list of dicts).
        :param target_language: Language code (e.g. 'en', 'fr', 'es').
        :return: A new list of segments, same timestamps but translated text.
        """
        translator = Translator()
        translated_segments = []

        print(f"[INFO] Translating segments to '{target_language}'...")
        for seg in segments:
            original_text = seg["text"].strip()
            if not original_text:
                translated_text = ""
            else:
                try:
                    result = translator.translate(original_text, dest=target_language)
                    translated_text = result.text
                except Exception as e:
                    print(f"[WARNING] Translation error for segment: {original_text}\n{e}")
                    translated_text = original_text  # fallback to original text

            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": translated_text
            })

        return translated_segments

    def generate_translated_audio(self, text, target_language="en", output_audio_path="translated_audio.mp3"):
        """
        Convert text into speech (TTS) in the target language using gTTS.
        """
        if not text.strip():
            print("[INFO] No text provided; skipping TTS generation.")
            return

        print(f"[INFO] Generating TTS audio in '{target_language}'...")
        try:
            tts = gTTS(text=text, lang=target_language)
            tts.save(output_audio_path)
            print(f"[INFO] Translated audio saved to {output_audio_path}")
        except Exception as e:
            print(f"[ERROR] TTS generation failed: {e}")

    @staticmethod
    def _format_timecode(seconds):
        """
        Convert float seconds to SRT timecode: HH:MM:SS,mmm
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds - int(seconds)) * 1000)

        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"
