from flask import Flask, request, render_template
import requests
import time
import yt_dlp as youtube_dl
import os

API_KEY_ASSEMBLYAI = "d38391f3f2844f8189e411f8d7333392"  # Substitua pela sua chave da API AssemblyAI

# Inicializa o Flask
app = Flask(__name__)

# Função para baixar o áudio de um vídeo do YouTube usando yt-dlp
def baixar_audio_youtube(url, output_path="audio.mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

# Função para enviar o áudio para AssemblyAI e transcrever
def transcrever_audio_assemblyai(audio_file):
    headers = {'authorization': API_KEY_ASSEMBLYAI}

    # Enviar o arquivo de áudio para AssemblyAI
    upload_url = "https://api.assemblyai.com/v2/upload"
    with open(audio_file, 'rb') as f:
        upload_response = requests.post(upload_url, headers=headers, files={'file': f})
    audio_url = upload_response.json()['upload_url']

    # Iniciar a transcrição
    transcript_url = "https://api.assemblyai.com/v2/transcript"
    transcript_request = {
        'audio_url': audio_url,
        'iab_categories': True
    }
    transcript_response = requests.post(transcript_url, json=transcript_request, headers=headers)
    transcript_id = transcript_response.json()['id']

    # Aguardar a transcrição ser processada
    status = 'processing'
    while status != 'completed':
        transcript_status_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        status_response = requests.get(transcript_status_url, headers=headers)
        status = status_response.json()['status']
        if status == 'failed':
            return "Erro na transcrição."
        time.sleep(5)

    # Obter a transcrição completa com segmentos
    return status_response.json()

# Rota principal para exibir a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar a URL do vídeo do YouTube e transcrever o áudio
@app.route('/transcrever', methods=['POST'])
def transcrever_video():
    youtube_url = request.form['youtube_url']

    if not youtube_url:
        return render_template('index.html', transcricao="Erro: URL não fornecida.")

    try:
        # Baixar o áudio do vídeo do YouTube
        audio_file = baixar_audio_youtube(youtube_url)

        # Enviar o áudio para AssemblyAI e obter a transcrição
        transcricao_json = transcrever_audio_assemblyai(audio_file)

        # Formatar a transcrição com timestamps
        transcricao_formatada = ""
        for segment in transcricao_json['utterances']:
            start_time = segment['start'] / 1000  # Converter milissegundos para segundos
            end_time = segment['end'] / 1000
            text = segment['text']

            start_minutos = int(start_time // 60)
            start_segundos = int(start_time % 60)

            transcricao_formatada += f"[{start_minutos:02d}:{start_segundos:02d}] {text}\n"

        # Remover o arquivo de áudio
        os.remove(audio_file)

        # Exibir a transcrição na página
        return render_template('index.html', transcricao=transcricao_formatada)

    except Exception as e:
        return render_template('index.html', transcricao=f"Erro: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
