import os
import tempfile
import streamlit as st

from src.video_to_subtitle import VideoToSubtitle


def main():
    st.title("Video to Subtitles: Original + Translated")

    # File upload for video
    uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

    # Whisper model selection
    model_name = st.selectbox(
        "Select Whisper model",
        ["tiny", "small", "medium", "large", "large-v2"],
        index=1
    )

    # Target language for translation
    target_language = st.text_input(
        "Enter target language code (e.g. 'en' for English, 'fr' for French)",
        value="en"
    )

    # NEW: Option to generate TTS audio or not
    generate_tts = st.checkbox("Generate TTS Audio?", value=False)

    if st.button("Process"):
        if uploaded_video is not None:
            # Save the uploaded video to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
                temp_video.write(uploaded_video.read())
                temp_video_path = temp_video.name

            temp_audio_path = os.path.join(tempfile.gettempdir(), "temp_extracted_audio.wav")
            original_srt_path = os.path.join(tempfile.gettempdir(), "original_subtitles.srt")
            translated_srt_path = os.path.join(tempfile.gettempdir(), "translated_subtitles.srt")
            translated_audio_path = os.path.join(tempfile.gettempdir(), "translated_audio.mp3")

            v2s = VideoToSubtitle(model_name=model_name)

            try:
                # 1) Extract audio
                v2s.extract_audio(temp_video_path, temp_audio_path)

                # 2) Transcribe to get original-language segments
                v2s.transcribe(temp_audio_path)

                # 3) Generate SRT in original language
                v2s.generate_srt(
                    segments=v2s.transcription_segments,
                    output_srt_path=original_srt_path
                )

                # 4) Translate segments to target language
                translated_segments = v2s.translate_segments(
                    segments=v2s.transcription_segments,
                    target_language=target_language
                )

                # 5) Generate SRT in target language
                v2s.generate_srt(
                    segments=translated_segments,
                    output_srt_path=translated_srt_path
                )

                # 6) Optionally generate TTS audio from the translated text
                if generate_tts:
                    full_translated_text = "\n".join(seg["text"] for seg in translated_segments)
                    v2s.generate_translated_audio(
                        text=full_translated_text,
                        target_language=target_language,
                        output_audio_path=translated_audio_path
                    )

                st.success("Processing complete!")

                # --- DOWNLOAD BUTTONS ---

                # Original Subtitles
                with open(original_srt_path, "rb") as f:
                    st.download_button(
                        label="Download Original Subtitles (SRT)",
                        data=f,
                        file_name="original_subtitles.srt",
                        mime="text/plain"
                    )

                # Translated Subtitles
                with open(translated_srt_path, "rb") as f:
                    st.download_button(
                        label="Download Translated Subtitles (SRT)",
                        data=f,
                        file_name="translated_subtitles.srt",
                        mime="text/plain"
                    )

                # TTS Audio (only if generated)
                if generate_tts and os.path.exists(translated_audio_path):
                    with open(translated_audio_path, "rb") as audio_file:
                        st.audio(audio_file, format="audio/mp3")
                        st.download_button(
                            label="Download Translated Audio (MP3)",
                            data=audio_file,
                            file_name="translated_audio.mp3",
                            mime="audio/mpeg"
                        )

            except Exception as e:
                st.error(f"An error occurred: {e}")

            finally:
                # Clean up temporary files
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
        else:
            st.warning("Please upload a valid video file first.")


if __name__ == "__main__":
    main()
