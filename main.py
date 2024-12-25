from yt_dlp import YoutubeDL
import speech_recognition as sr
from pydub import AudioSegment
import os
from googletrans import Translator
import time

class OptimizedYouTubeTranslator:
    def __init__(self, chunk_size_seconds=30):
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.chunk_size = chunk_size_seconds * 1000  # Convert to milliseconds
        
    def download_audio(self, url, output_path="audio"):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_path}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"{output_path}/{info['id']}.wav"

    def process_chunk(self, chunk, chunk_index):
        chunk_path = f"audio/temp_chunk_{chunk_index}.wav"
        chunk.export(chunk_path, format="wav")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with sr.AudioFile(chunk_path) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio, language='hi-IN')
                    translation = self.translator.translate(text, src='hi', dest='en')
                    os.remove(chunk_path)
                    return translation.text
            except sr.RequestError:
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                return ""
            except Exception as e:
                print(f"Error processing chunk {chunk_index}: {str(e)}")
                return ""
        
        return ""

    def process_video(self, url):
        try:
            wav_path = self.download_audio(url)
            audio = AudioSegment.from_wav(wav_path)
            
            # Process in 30-second chunks
            translations = []
            for i in range(0, len(audio), self.chunk_size):
                chunk = audio[i:i + self.chunk_size]
                translation = self.process_chunk(chunk, i//self.chunk_size)
                if translation:
                    translations.append(translation)
                print(f"Processed chunk {i//self.chunk_size + 1}")
            
            os.remove(wav_path)
            return " ".join(translations)
            
        except Exception as e:
            return f"Processing error: {e}"

# Usage
translator = OptimizedYouTubeTranslator(chunk_size_seconds=30)
url = "https://www.youtube.com/watch?v=pa-j5tx1tMw&t=604s"
english_translation = translator.process_video(url)
print(english_translation)
