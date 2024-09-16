from flask import Flask, request, render_template
import yt_dlp as youtube_dl
import openai
import os

# Inicializa o Flask
app = Flask(__name__)

# Defina sua chave da API da OpenAI aqui
openai.api_key = "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"


def baixar_audio_youtube(url, output_path="audio.webm"):
    ydl_opts = {
        'format': 'bestaudio[ext=webm]/bestaudio',
        'outtmpl': output_path,  # Define o caminho de saída
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        }
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path


# Função para transcrever áudio usando a API da OpenAI
def transcrever_audio_api(audio_file):
    with open(audio_file, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    return transcript['text']

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

        # Transcreve o áudio
        transcricao = transcrever_audio_api(audio_file)

        # Remove o arquivo de áudio após a transcrição
        os.remove(audio_file)

        # Retorna a transcrição na página
        return render_template('index.html', transcricao=transcricao)

    except Exception as e:
        return render_template('index.html', transcricao=f"Erro: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Especificando a porta 8000