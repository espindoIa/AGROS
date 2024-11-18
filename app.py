import os
import logging
from flask import Flask, request, jsonify
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads import TextDelta
from typing_extensions import override
import re
import asyncio
from functools import lru_cache

# Inicialização do aplicativo Flask
app = Flask(__name__)

# Carrega a chave da API do ambiente
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Armazenamento de IDs de thread
thread_id_store = {}

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Gerenciamento de threads
def get_or_create_thread_id(user_id):
    if user_id not in thread_id_store:
        thread_id_store[user_id] = client.create_thread()  # Placeholder para criação de thread
    return thread_id_store[user_id]

# Classe manipuladora de eventos com processamento assíncrono
class MyEventHandler(AssistantEventHandler):
    def __init__(self):
        super().__init__()
        self.message_content = ""
    
    @override
    async def on_text_delta(self, delta: TextDelta, snapshot):
        self.message_content += delta.value
    
    @override
    async def on_message_done(self, message) -> None:
        self.message_content = self.format_message(self.message_content)
    
    def format_message(self, message_content: str) -> str:
        message_content = re.sub(r'\[\d+\]', '', message_content)
        message_content = re.sub(r'【\d+:\d+†source】', '', message_content)
        message_content = re.sub(r'(\n)([^\n]+)(\n===+)', r'\1<h2>\2</h2>\1', message_content)
        return message_content

# Rota para o chat
@app.route('/chat', methods=['POST'])
async def chat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    
    thread_id = get_or_create_thread_id(user_id)
    event_handler = MyEventHandler()
    
    try:
        response = await client.stream_message(
            thread_id=thread_id,
            message=message,
            event_handler=event_handler
        )
        return jsonify({"response": event_handler.message_content})
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return jsonify({"error": "An error occurred processing your request"}), 500

# Cache para respostas
@lru_cache(maxsize=128)
def cached_response(user_id):
    return thread_id_store.get(user_id, None)

# Rota principal
@app.route('/')
def index():
    return "Welcome to the Conversational AI Application!"

# Middleware para headers de segurança
@app.after_request
def apply_security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# Execução principal do aplicativo
if __name__ == "__main__":
    # Render tipicamente usa a variável de ambiente PORT
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
