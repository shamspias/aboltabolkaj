import os
import streamlit as st
from src.video_to_subtitle import VideoToSubtitle
import tempfile


def main():
    st.title("Video to Subtitle + Translation App")
    st.write("""
    **Upload a video**, automatically get **subtitles (SRT)**, and optionally
    get **translated TTS audio** in your chosen language.
    """)

    # File uploader for video
    uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi", "mkv"])

    # Whisper model selection
    model_name = st.selectbox(
        "Select Whisper model",
        ["tiny", "small", "medium", "large", "large-v2"],
        index=1  # default "small"
    )

    # Target language for TTS
    target_language = st.text_input(
        "Enter target language code for translation (e.g. 'en', 'fr', 'es', 'hi')",
        value="en"
    )

    if st.button("Process"):
        if uploaded_video is not None:
            # Save uploaded video to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video_file:
                temp_video_file.write(uploaded_video.read())
                temp_video_path = temp_video_file.name

            # Prepare paths for intermediate and output files
            temp_audio_path = os.path.join(tempfile.gettempdir(), "temp_extracted_audio.wav")
            output_srt_path = os.path.join(tempfile.gettempdir(), "transcribed_subtitles.srt")
            translated_audio_path = os.path.join(tempfile.gettempdir(), "translated_audio.mp3")

            # Create our VideoToSubtitle object
            v2s = VideoToSubtitle(model_name=model_name)

            try:
                # Extract audio
                v2s.extract_audio(temp_video_path, temp_audio_path)

                # Transcribe
                v2s.transcribe(temp_audio_path)

                # Generate SRT
                v2s.generate_srt(output_srt_path)

                # Combine the entire transcription text for translation + TTS
                # (Optional: You can also chunk it by segment if needed)
                full_transcript = "\n".join(
                    seg["text"].strip() for seg in v2s.transcription_segments
                )

                translated_text = v2s.translate_text(full_transcript, target_language)

                # Generate TTS audio of the translated text
                v2s.generate_translated_audio(translated_text, target_language, translated_audio_path)

                # Show success message
                st.success("Processing completed.")

                # Provide download buttons for SRT and translated audio
                with open(output_srt_path, "rb") as srt_file:
                    st.download_button(
                        label="Download Subtitles (SRT)",
                        data=srt_file,
                        file_name="generated_subtitles.srt",
                        mime="text/plain"
                    )

                with open(translated_audio_path, "rb") as audio_file:
                    st.audio(audio_file, format="audio/mp3")
                    st.download_button(
                        label="Download Translated Audio (MP3)",
                        data=audio_file,
                        file_name="translated_audio.mp3",
                        mime="audio/mpeg"
                    )
            except Exception as e:
                st.error(f"Error during processing: {e}")
            finally:
                # Cleanup temp files
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                # We'll leave the output files so they can be downloaded by the user
        else:
            st.warning("Please upload a valid video file first.")


if __name__ == "__main__":
    main()
