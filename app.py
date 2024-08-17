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

# Load the OpenAI API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
ifnot api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables")
client = OpenAI(api_key=api_key)

# Rest of your existing code...# Armazenar o ID da thread para reutilização
thread_id_store = {}

classMyEventHandler(AssistantEventHandler):
    def__init__(self):
        super().__init__()
        self.message_content = ""    @overridedefon_text_delta(self, delta: TextDelta, snapshot):
        self.message_content += delta.value

    @overridedefon_message_done(self, message) -> None:
        self.message_content = self.format_message(self.message_content)

    defformat_message(self, message_content: str) -> str:
        message_content = re.sub(r'\[\d+\]', '', message_content)
        message_content = re.sub(r'【\d+:\d+†source】', '', message_content)
        message_content = re.sub(r'(\n)([^\n]+)(\n===+)', r'\1<h2>\2</h2>\1', message_content)
        message_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', message_content)
        message_content = re.sub(r'__(.*?)__', r'<u>\1</u>', message_content)
        message_content = message_content.replace('\n', '<br>')
        return message_content

    defget_message(self):
        return self.message_content

defget_or_create_thread(assistant_id):
    if assistant_id notin thread_id_store:
        thread = client.beta.threads.create()
        thread_id_store[assistant_id] = thread.idreturn thread_id_store[assistant_id]

defcreate_message_and_get_response(user_message, assistant_id, retries=3, delay=5):
    thread_id = get_or_create_thread(assistant_id)
    
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    attempt = 1 while attempt <= retries:
        try:
            event_handler = MyEventHandler()
            with client.beta.threads.runs.stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
                event_handler=event_handler,
            ) as stream:
                stream.until_done()
            return event_handler.get_message()

        except Exception as e:
            print(f"Attempt {attempt} failed with error: {e}")
            attempt += 1
            time.sleep(delay)
    raise RuntimeError("Failed to get response after 3 attempts")

@app.route('/')defindex():
    return send_from_directory('', 'index.html')

@app.route('/chat')defchat():
    assistant = request.args.get('assistant')
    if assistant == 'vida':
        return send_from_directory('', 'chat_vida.html')
    elif assistant == 'invest':
        return send_from_directory('', 'chat_invest.html')
    else:
        return redirect(url_for('index'))

@app.route('/send_message', methods=['POST'])defsend_message():
    data = request.json
    assistant_id = data['assistant_id']
    user_message = data['message']
    response = create_message_and_get_response(user_message, assistant_id)
    return jsonify({'response': response})

defopen_browser():
    webbrowser.open_new(f'http://0.0.0.0:{os.environ.get("PORT", 5000)}/')

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

