from flask import Flask, request, render_template
import yt_dlp as youtube_dl
import requests
import os

# Inicializa o Flask
app = Flask(__name__)

# Defina sua chave da API da AssemblyAI aqui
ASSEMBLYAI_API_KEY = 'd38391f3f2844f8189e411f8d7333392'

# Função para baixar o áudio de um vídeo do YouTube e convertê-lo em MP3 usando yt-dlp
def baixar_audio_youtube(url, output_path="audio.mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,  # Define o caminho de saída
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

# Função para fazer upload do áudio para a AssemblyAI
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
def solicitar_transcricao(audio_url):
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

# Função para obter o resultado da transcrição
def obter_transcricao(transcript_id):
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {
        "authorization": ASSEMBLYAI_API_KEY
    }

    while True:
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        if data['status'] == 'completed':
            return data['text']
        elif data['status'] == 'failed':
            return "Erro: Falha na transcrição."
        else:
            continue  # Aguarda até que a transcrição esteja pronta

# Rota para exibir a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar o download e transcrição
@app.route('/transcrever', methods=['POST'])
def transcrever_video():
    youtube_url = request.form['youtube_url']

    if not youtube_url:
        return render_template('index.html', transcricao="Erro: URL não fornecida.")

    try:
        # Baixar o áudio
        audio_file = baixar_audio_youtube(youtube_url)

        # Fazer upload do áudio para a AssemblyAI
        audio_url = upload_audio(audio_file)

        # Solicitar transcrição
        transcript_id = solicitar_transcricao(audio_url)

        # Obter a transcrição completa
        transcricao = obter_transcricao(transcript_id)

        # Remover o arquivo de áudio após a transcrição
        os.remove(audio_file)

        # Retorna a transcrição na página
        return render_template('index.html', transcricao=transcricao)

    except Exception as e:
        return render_template('index.html', transcricao=f"Erro: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
