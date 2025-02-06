# Video-to-Subtitle and Audio Translator (subdio)

This project takes a **video file** as input, **extracts and transcribes** the audio, **generates subtitles (SRT)**, and **optionally translates** the transcribed text into a target language and **outputs a TTS audio file**.

## Table of Contents

1. [Introduction](#introduction)  
2. [Key Features](#key-features)  
3. [Technologies Used](#technologies-used)  
4. [Installation](#installation)  
5. [Usage](#usage)  
6. [Project Structure](#project-structure)  
7. [How It Works (Process Flow)](#how-it-works-process-flow)  

---

## Introduction

This repository provides a Streamlit-based application that simplifies the process of generating subtitles from a video. It utilizes [OpenAI Whisper](https://github.com/openai/whisper) to handle transcription and [Googletrans 4.0.0-rc1](https://pypi.org/project/googletrans/) to translate the text to a desired language. The translated text can then be converted into an audio file using **TTS** (e.g., `gTTS`).

---

## Key Features

- **Video to Subtitles**: Automatically transcribe any supported video format into an SRT file.  
- **Language Detection**: Attempts to detect the spoken language from the transcription.  
- **Translation**: Uses Googletrans (v4.0.0-rc1) to translate the transcribed text into a chosen language.  
- **TTS Audio**: Generates an audio file (.mp3) of the translated text via `gTTS`.  
- **Streamlit UI**: A simple web interface to upload videos, select models, and download output files.

---

## Technologies Used

1. **Python 3**  
2. **[Streamlit](https://streamlit.io/)**: For creating the interactive web app.  
3. **[MoviePy](https://github.com/Zulko/moviepy)**: To extract audio from video.  
4. **[OpenAI Whisper](https://github.com/openai/whisper)**: For speech recognition and transcription.  
5. **[Googletrans (4.0.0-rc1)](https://pypi.org/project/googletrans/4.0.0-rc1/)**: For translating text.  
6. **[gTTS](https://pypi.org/project/gTTS/)**: For converting translated text to speech.  
7. **[langdetect](https://pypi.org/project/langdetect/)**: For attempting to detect the transcription language.  

> **Note**: This setup **requires** [FFmpeg](https://ffmpeg.org/) installed on your system.

---

## Installation

1. **Clone or download** this repository.
2. Navigate into the project folder:
   ```bash
   cd subdio
   ```
3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate         # Linux/Mac
   # or: venv\Scripts\activate.bat  # Windows
   ```
4. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   Make sure you have [FFmpeg](https://ffmpeg.org/) installed.  
   You can verify by:
   ```bash
   ffmpeg -version
   ```
5. (Optional) If needed, install **PyTorch** for Whisper:
   ```bash
   pip install torch torchvision torchaudio  # For CPU or GPU
   ```
   or a version matching your GPU (if you have CUDA).

---

## Usage

1. **Activate your virtual environment** (if not already):
   ```bash
   source venv/bin/activate
   ```
2. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```
3. Open the displayed **Local URL** in your browser (e.g., http://localhost:8501).  

**In the UI**:
1. **Upload a video** file (e.g., `.mp4`).  
2. Select your **Whisper model** (tiny, small, medium, large, etc.).  
3. **Enter a target language** code for translation (e.g., `en`, `fr`, `es`).  
4. Click **Process**.  
5. After processing, download your **SRT** file and (optionally) the **translated audio MP3**.

---

## Project Structure

Here’s a simplified example:

```
subdio/
│
├── app.py                  # Main Streamlit app
├── requirements.txt        # Dependencies
├── README.md               # This README
└── src/
    └── video_to_subtitle.py  # Main logic class: extraction, transcription, translation
```

---

## How It Works (Process Flow)

1. **Upload Video**  
   - User uploads a video via Streamlit’s uploader.

2. **Extract Audio**  
   - [MoviePy](https://github.com/Zulko/moviepy) extracts the audio track from the video at 16kHz.

3. **Transcription (Whisper)**  
   - OpenAI Whisper transcribes audio into text with timestamps.

4. **Language Detection**  
   - Uses [langdetect](https://pypi.org/project/langdetect/) on a sample of the transcribed text to guess the language code (e.g., `en`, `fr`, `hi`).

5. **Subtitle Generation**  
   - Creates `.srt` file using timestamped segments (`start_time`, `end_time`, `text`).

6. **(Optional) Translation**  
   - [Googletrans](https://pypi.org/project/googletrans/) translates the aggregated text into the user-chosen language.

7. **(Optional) TTS**  
   - [gTTS](https://pypi.org/project/gTTS/) converts the translated text into an audio file (`.mp3`).

8. **Download Outputs**  
   - User can download the `.srt` (subtitles) and `.mp3` (translated speech).

