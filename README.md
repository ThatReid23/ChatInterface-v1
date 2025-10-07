# ChatInterface

**ChatInterface** is a modern web-based front-end for the [`llm_manager`](https://github.com/ryyReid/llm_manager) system.
It provides a simple yet powerful interface for interacting with local or remote LLM backends managed through your unified API gateway.

---

## 🚀 Features

* **Chat history system** — automatically saves conversations as JSON in the `chat_history/` folder.
* **User authentication** — lightweight login system for personalized sessions.
* **File uploads** — attach files as context for chat interactions.
* **Model auto-detection** — dynamically lists models discovered by the backend.
* **Simple, clean UI** — responsive interface built with Flask templates and minimal JS.

---

## 🧩 Project Structure

```
ChatInterface/
├── app.py                # Main Flask application
├── templates/
│   ├── index.html        # Main chat interface
│   └── login.html        # User login page
├── static/
│   ├── css/              # Stylesheets
│   └── js/               # Client-side scripts
└── chat_history/
    └── user/             # Stored chat logs (JSON)
```

---

## ⚙️ Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/ryyReid/ChatInterface.git
   cd ChatInterface
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   * Set your backend URL and API key inside `app.py`:

     ```python
     MANAGER_API_URL = "http://localhost:8000"
     MANAGER_API_KEY = "your_api_key_here"
     ```

4. **Run the app**

   ```bash
   python app.py
   ```

   Access the interface at `http://127.0.0.1:5000`.

---

## 🧠 How It Works

`ChatInterface` communicates directly with your `llm_manager` backend, which routes requests to the correct LLM nodes.
This allows multiple models to be accessed through one clean endpoint, while user sessions, chat logs, and file contexts stay locally stored for privacy and speed.

---

## 📦 Requirements

* Python 3.10+
* Flask
* Requests
* (Optional) Access to a running `llm_manager` backend

---

## 🧑‍💻 Author

**Reid**
GitHub: [@ryyReid](https://github.com/ryyReid) • [@ThatReid23](https://github.com/ThatReid23)

---

## 🪐 License

MIT License © 2025 Reid
