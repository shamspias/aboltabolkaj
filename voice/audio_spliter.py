from pydub import AudioSegment
import os
import math


def split_mp3(file_path, chunk_length_sec=250):
    # Load audio file
    audio = AudioSegment.from_mp3(file_path)

    # Get filename and directory
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.dirname(file_path)

    # Calculate total number of chunks
    total_length_sec = len(audio) / 1000  # convert ms to seconds
    num_chunks = math.ceil(total_length_sec / chunk_length_sec)

    print(f"Splitting '{file_name}.mp3' into {num_chunks} chunks of {chunk_length_sec} seconds each...")

    for i in range(num_chunks):
        start_time = i * chunk_length_sec * 1000  # in ms
        end_time = min((i + 1) * chunk_length_sec * 1000, len(audio))
        chunk = audio[start_time:end_time]

        chunk_name = f"{file_name}_part{i + 1}.wav"
        chunk_path = os.path.join(output_dir, chunk_name)
        chunk.export(chunk_path, format="wav")
        print(f"Saved: {chunk_path}")

    print("Splitting complete.")


# Example usage
# Replace this with the path to your MP3 file
split_mp3("story_voice_1.wav")
