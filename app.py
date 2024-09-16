from flask import Flask, render_template, request, jsonify
import requests
import os
import yt_dlp as youtube_dl

# Configure sua chave da API AssemblyAI
ASSEMBLYAI_API_KEY = 'd38391f3f2844f8189e411f8d7333392'

# Configuração do Flask
app = Flask(__name__)

# Função para baixar o áudio do vídeo do YouTube
def download_audio_from_youtube(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'audio.mp3',
        'quiet': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        return 'audio.mp3'

# Função para enviar o áudio para transcrição
def upload_audio(file_path):
    headers = {
        'authorization': ASSEMBLYAI_API_KEY
    }

    with open(file_path, 'rb') as f:
        response = requests.post(
            'https://api.assemblyai.com/v2/upload',
            headers=headers,
            files={'file': f}
        )

    return response.json().get('upload_url')

# Função para solicitar transcrição
def request_transcription(audio_url):
    endpoint = "https://api.assemblyai.com/v2/transcript"
    json_data = {
        "audio_url": audio_url
    }
    headers = {
        "authorization": ASSEMBLYAI_API_KEY,
        "content-type": "application/json"
    }

    response = requests.post(endpoint, json=json_data, headers=headers)
    return response.json().get('id')

# Função para obter transcrição
def get_transcription(transcript_id):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {
        "authorization": ASSEMBLYAI_API_KEY
    }

    response = requests.get(endpoint, headers=headers)
    return response.json()

# Rota da página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar o link do YouTube
@app.route('/transcribe', methods=['POST'])
def transcribe():
    youtube_link = request.form['youtube_link']

    # Baixar o áudio do vídeo do YouTube
    audio_path = download_audio_from_youtube(youtube_link)

    # Enviar o áudio para transcrição
    audio_url = upload_audio(audio_path)

    # Solicitar transcrição
    transcript_id = request_transcription(audio_url)

    # Esperar a transcrição ser finalizada
    transcription_data = get_transcription(transcript_id)

    # Excluir o arquivo de áudio
    os.remove(audio_path)

    return jsonify(transcription_data)

# Inicialização da aplicação Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
