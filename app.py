from flask import Flask, request, render_template
import yt_dlp as youtube_dl
import openai
import os

# Inicializa o Flask
app = Flask(__name__)

# Defina sua chave da API da OpenAI aqui
openai.api_key = "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"


# Função para baixar o áudio de um vídeo do YouTube usando yt-dlp (sem ffmpeg)
def baixar_audio_youtube(url, output_path="audio.webm"):
    ydl_opts = {
        'format': 'bestaudio[ext=webm]/bestaudio',
        'outtmpl': output_path,  # Define o caminho de saída
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

# Função para transcrever áudio usando a API da OpenAI
def transcrever_audio_com_segmentos(audio_file):
    with open(audio_file, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)

    # Processar a transcrição para incluir os timestamps e formatar o texto
    transcricao_formatada = ""
    for segment in transcript['segments']:
        start_time = segment['start']  # Tempo de início do segmento (em segundos)
        end_time = segment['end']      # Tempo de término do segmento (em segundos)
        text = segment['text']         # Texto transcrito

        # Converter os segundos para formato de minutos e segundos
        start_minutos = int(start_time // 60)
        start_segundos = int(start_time % 60)

        # Adicionar a transcrição formatada com timestamps
        transcricao_formatada += f"[{start_minutos:02d}:{start_segundos:02d}] {text}\n"
    
    return transcricao_formatada

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
        # Baixa o áudio
        audio_file = baixar_audio_youtube(youtube_url)

        # Transcreve o áudio com segmentos e timestamps
        transcricao = transcrever_audio_com_segmentos(audio_file)

        # Remove o arquivo de áudio após a transcrição
        os.remove(audio_file)

        # Retorna a transcrição na página
        return render_template('index.html', transcricao=transcricao)

    except Exception as e:
        return render_template('index.html', transcricao=f"Erro: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)