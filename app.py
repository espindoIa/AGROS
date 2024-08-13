
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads import TextDelta
from typing_extensions import override
import re
import webbrowser
import threading
import time
import os

app = Flask(__name__)

# Configurar a chave da API do OpenAI de forma segura
api_key = "sk-proj-UNjkmlvR3uT77qRYWDUlT3BlbkFJCGYlU4n5K6NoQU26FhS2"
client = OpenAI(api_key=api_key)

# Definindo a classe EventHandler para processar eventos do streaming
class MyEventHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()
        self.message_content = ""

    @override
    def on_text_delta(self, delta: TextDelta, snapshot):
        self.message_content += delta.value

    @override
    def on_message_done(self, message) -> None:
        # Finaliza a mensagem quando o processamento estiver completo
        self.message_content = self.format_message(self.message_content)

    def format_message(self, message_content: str) -> str:
        # Limpa anotações e referências
        message_content = re.sub(r'\[\d+\]', '', message_content)
        message_content = re.sub(r'【\d+:\d+†source】', '', message_content)
        
        # Formatação de subtítulos, negrito, sublinhado e listas
        message_content = re.sub(r'(
)([^
]+)(
===+)', r'<h2></h2>', message_content)
        message_content = re.sub(r'\*\*(.*?)\*\*', r'<strong></strong>', message_content)
        message_content = re.sub(r'__(.*?)__', r'<u></u>', message_content)
        message_content = message_content.replace('
', '<br>')
        return message_content

    def get_message(self):
        return self.message_content

def create_thread_and_get_response(user_message, assistant_id, retries=3, delay=5):
    thread = {
        "messages": [{"role": "user", "content": user_message}]
    }

    attempt = 1
    while attempt <= retries:
        try:
            event_handler = MyEventHandler()
            with client.beta.threads.create_and_run_stream(
                assistant_id=assistant_id,
                thread=thread,
                event_handler=event_handler,
            ) as stream:
                stream.until_done()

            return event_handler.get_message()

        except Exception as e:
            print(f"Attempt {attempt} failed with error: {e}")
            attempt += 1
            time.sleep(delay)
    raise RuntimeError("Failed to get response after 3 attempts")

@app.route('/')
def index():
    return send_from_directory('', 'index.html')

@app.route('/chat')
def chat():
    assistant = request.args.get('assistant')
    if assistant == 'vida':
        return send_from_directory('', 'chat_vida.html')
    elif assistant == 'invest':
        return send_from_directory('', 'chat_invest.html')
    else:
        return redirect(url_for('index'))

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    assistant_id = data['assistant_id']
    user_message = data['message']
    response = create_thread_and_get_response(user_message, assistant_id)
    return jsonify({'response': response})

def open_browser():
    webbrowser.open_new(f'http://0.0.0.0:{os.environ.get("PORT", 5000)}/')

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
