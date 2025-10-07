# ChatInterface/app.py (Fixed & Usable Version)

import os
import json
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests

# --- Configuration ---
MANAGER_API_URL = "http://192.168.1.129:8000"
MANAGER_API_KEY = "89009"
CHAT_HISTORY_DIR = "chat_history"

app = Flask(__name__)
app.secret_key = '0000'

# Ensure chat history directory exists
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# --- Helper Functions ---
def get_online_models():
    try:
        headers = {"Authorization": f"Bearer {MANAGER_API_KEY}"}
        response = requests.get(f"{MANAGER_API_URL}/v1/models", headers=headers, timeout=5)
        response.raise_for_status()
        return [m['id'] for m in response.json().get('data', [])]
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not fetch models: {e}")
        flash(f"Could not connect to the LLM Manager: {e}", "error")
        return []

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def get_user_dir(username=None):
    username = username or session.get('username')
    path = os.path.join(CHAT_HISTORY_DIR, username)
    os.makedirs(path, exist_ok=True)
    return path

def get_chat_files(username=None):
    user_dir = get_user_dir(username)
    files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(user_dir, x)), reverse=True)
    return files

def load_chat(chat_id):
    filepath = os.path.join(get_user_dir(), f"{chat_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If JSON is corrupt, return empty chat
            return {"id": chat_id, "title": "Corrupt Chat", "model": None, "messages": []}
    return None

def save_chat(chat_id, messages, title=None, model=None):
    filepath = os.path.join(get_user_dir(), f"{chat_id}.json")
    existing = load_chat(chat_id)
    if not title:
        title = existing.get('title') if existing else next((m['content'][:50] for m in messages if m['role']=='user'), "New Chat")
    if not model:
        model = existing.get('model') if existing else session.get('selected_model')
    data = {"id": chat_id, "title": title, "model": model, "messages": messages}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    return data

def get_chat_title(chat_id):
    chat = load_chat(chat_id)
    return chat.get('title', 'Chat') if chat else 'Chat'

# --- Routes ---
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        if username:
            session['username'] = username
            session['selected_model'] = None
            get_user_dir(username)
            return redirect(url_for('home'))
        return render_template('login.html', error="Username cannot be empty.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    files = get_chat_files()
    if files:
        return redirect(url_for('view_chat', chat_id=files[0].replace('.json','')))
    return redirect(url_for('new_chat'))

@app.route('/new')
@login_required
def new_chat():
    chat_id = str(uuid.uuid4())
    save_chat(chat_id, [], title="New Chat")
    return redirect(url_for('view_chat', chat_id=chat_id))

@app.route('/chat/<chat_id>', methods=['GET','POST'])
@login_required
def view_chat(chat_id):
    chat = load_chat(chat_id)
    if chat is None:
        return redirect(url_for('new_chat'))

    online_models = get_online_models()
    selected_model = session.get('selected_model')
    if not selected_model or selected_model not in online_models:
        selected_model = online_models[0] if online_models else None
        session['selected_model'] = selected_model

    if request.method == 'POST':
        if not selected_model:
            flash("No models online.", "error")
            return redirect(url_for('view_chat', chat_id=chat_id))

        prompt = request.form.get('prompt','').strip()
        uploaded_file = request.files.get('context_file')
        if uploaded_file and uploaded_file.filename:
            try:
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                prompt = f"--- FILE {uploaded_file.filename} ---\n{content}\n--- END ---\n{prompt}"
            except Exception as e:
                flash(f"File read error: {e}", "error")

        if prompt:
            chat['messages'].append({"role":"user","content":prompt})
            try:
                resp = requests.post(
                    f"{MANAGER_API_URL}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {MANAGER_API_KEY}", "Content-Type":"application/json"},
                    json={"model": selected_model, "messages": chat['messages']},
                    timeout=60
                )
                resp.raise_for_status()
                llm_msg = resp.json()['choices'][0]['message']['content']
                chat['messages'].append({"role":"assistant","content":llm_msg})
            except Exception as e:
                err = f"LLM Manager error: {e}"
                chat['messages'].append({"role":"assistant","content":err})
                flash(err, "error")
            save_chat(chat_id, chat['messages'], model=selected_model)
        return redirect(url_for('view_chat', chat_id=chat_id))

    files = get_chat_files()
    chat_titles = {f.replace('.json',''): get_chat_title(f.replace('.json','')) for f in files}
    return render_template('index.html', chats=chat_titles, current_chat=chat, available_models=online_models, selected_model=selected_model)

@app.route('/select_model', methods=['POST'])
@login_required
def select_model():
    model = request.form.get('model')
    chat_id = request.form.get('chat_id')
    online_models = get_online_models()
    if model in online_models:
        session['selected_model'] = model
        flash(f"Model switched to {model}", "success")
    else:
        flash("Invalid or offline model.", "error")
    return redirect(url_for('view_chat', chat_id=chat_id or ''))

@app.route('/rename/<chat_id>', methods=['POST'])
@login_required
def rename_chat(chat_id):
    chat = load_chat(chat_id)
    new_title = request.form.get('new_title','').strip()
    save_chat(chat_id, chat['messages'], title=new_title)
    return redirect(url_for('view_chat', chat_id=chat_id))

@app.route('/duplicate/<chat_id>', methods=['POST'])
@login_required
def duplicate_chat(chat_id):
    chat = load_chat(chat_id)
    new_id = str(uuid.uuid4())
    save_chat(new_id, chat['messages'], title=f"{chat.get('title','Chat')} (copy)", model=chat.get('model'))
    return redirect(url_for('view_chat', chat_id=new_id))

@app.route('/delete/<chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    path = os.path.join(get_user_dir(), f"{chat_id}.json")
    if os.path.exists(path):
        os.remove(path)
        flash("Chat deleted.", "success")
    else:
        flash("Chat not found.", "error")
    return redirect(url_for('home'))

# --- Run App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
