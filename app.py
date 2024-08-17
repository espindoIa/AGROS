import os
import logging
from flask import Flask, request, jsonify
from openai import OpenAI, AssistantEventHandler
from openai.types.beta.threads import TextDelta
from typing_extensions import override
import re
import asyncio
from functools import lru_cache

app = Flask(__name__)

# Load API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Thread ID store
thread_id_store = {}

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Thread managementdefget_or_create_thread_id(user_id):
    if user_id notin thread_id_store:
        thread_id_store[user_id] = client.create_thread()  # Placeholder for thread creationreturn thread_id_store[user_id]

# Event handler class with async processingclassMyEventHandler(AssistantEventHandler):
    def__init__(self):
        super().__init__()
        self.message_content = ""    @overrideasyncdefon_text_delta(self, delta: TextDelta, snapshot):
        self.message_content += delta.value

    @overrideasyncdefon_message_done(self, message) -> None:
        self.message_content = self.format_message(self.message_content)

    defformat_message(self, message_content: str) -> str:
        message_content = re.sub(r'\[\d+\]', '', message_content)
        message_content = re.sub(r'【\d+:\d+†source】', '', message_content)
        message_content = re.sub(r'(\n)([^\n]+)(\n===+)', r'\1<h2>\2</h2>\1', message_content)
        return message_content

@app.route('/chat', methods=['POST'])asyncdefchat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    
    thread_id = get_or_create_thread_id(user_id)
    event_handler = MyEventHandler()
    
    try:
        response = await client.stream_message(thread_id=thread_id, message=message, event_handler=event_handler)
        return jsonify({"response": event_handler.message_content})
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        return jsonify({"error": "An error occurred processing your request"}), 500@lru_cache(maxsize=128)defcached_response(user_id):
    return thread_id_store.get(user_id, None)

@app.route('/')defindex():
    return"Welcome to the Conversational AI Application!"@app.after_requestdefapply_security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"return response

if __name__ == "__main__":
    # Render typically uses the PORT environment variable
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
