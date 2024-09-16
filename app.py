import requests
import time
import yt_dlp as youtube_dl
import os
from flask import Flask, request, render_template

API_KEY_ASSEMBLYAI = "d38391f3f2844f8189e411f8d7333392"

# Inicializa o Flask
app = Flask(__name__)

def baixar_audio_youtube(url, output_path="audio.mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'cookiefile': './cookies.txt',  # Forneça o caminho para o arquivo de cookies
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
    
    if upload_response.status_code != 200:
        return None, f"Erro no upload do áudio: {upload_response.text}"
    
    audio_url = upload_response.json().get('upload_url')
    if not audio_url:
        return None, "Erro: URL de upload não foi gerada corretamente."
    
    # Iniciar a transcrição
    transcript_url = "https://api.assemblyai.com/v2/transcript"
    transcript_request = {
        'audio_url': audio_url,
        'iab_categories': True
    }
    transcript_response = requests.post(transcript_url, json=transcript_request, headers=headers)

    if transcript_response.status_code != 200:
        return None, f"Erro ao iniciar a transcrição: {transcript_response.text}"
    
    transcript_id = transcript_response.json()['id']

    # Aguardar a transcrição ser processada
    status = 'processing'
    while status != 'completed':
        transcript_status_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        status_response = requests.get(transcript_status_url, headers=headers)
        status = status_response.json().get('status')

        if status == 'failed':
            return None, "Erro no processamento da transcrição."

        if status == 'completed':
            break
        
        time.sleep(5)

    # Retornar a resposta da transcrição
    return status_response.json(), None

# Função para processar e formatar a transcrição com timestamps
def formatar_transcricao(transcricao_json):
    if not transcricao_json or 'utterances' not in transcricao_json:
        return "Erro: Não foi possível obter os segmentos da transcrição."

    transcricao_formatada = ""
    for segment in transcricao_json['utterances']:
        start_time = segment['start'] / 1000  # Converter milissegundos para segundos
        end_time = segment['end'] / 1000
        text = segment['text']

        start_minutos = int(start_time // 60)
        start_segundos = int(start_time % 60)

        transcricao_formatada += f"[{start_minutos:02d}:{start_segundos:02d}] {text}\n"

    return transcricao_formatada

# Rota principal para exibir o formulário de entrada de URL
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar a URL do vídeo e transcrever o áudio
@app.route('/transcrever', methods=['POST'])
def transcrever_video():
    youtube_url = request.form['youtube_url']

    if not youtube_url:
        return render_template('index.html', transcricao="Erro: URL não fornecida.")

    try:
        # Baixar o áudio do vídeo do YouTube
        audio_file = baixar_audio_youtube(youtube_url)

        # Enviar o áudio para AssemblyAI e obter a transcrição
        transcricao_json, erro = transcrever_audio_assemblyai(audio_file)

        if erro:
            return render_template('index.html', transcricao=erro)

        # Formatar a transcrição com timestamps
        transcricao_formatada = formatar_transcricao(transcricao_json)

        # Exibir a transcrição na página
        return render_template('index.html', transcricao=transcricao_formatada)

    except Exception as e:
        return render_template('index.html', transcricao=f"Erro: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
