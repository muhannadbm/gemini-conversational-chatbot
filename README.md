# Gemini Conversational Chatbot

A command-line chatbot that talks to a Gemini model through the Google Gen AI SDK. Each reply stays in memory for the rest of the session, so later turns can refer to earlier ones. The history is discarded when the process exits.

## Prerequisites

- Python 3.10 or newer (`google-genai` and `python-dotenv` both require it)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

## Setup

Create a virtual environment, install the pinned dependencies, and copy the environment template.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**macOS and Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace `your_api_key_here` with your API key. `GEN_AI_MODEL` is set to `gemini-flash-lite-latest`; change it to another Gemini model id your key can access.

## Run

From the project root, with the virtual environment active:

```powershell
python main.py
```

The script prompts on one line. Type a message and press Enter. The reply is printed after a line of hyphens. Type `quit` to leave. Matching ignores case and surrounding spaces, so `Quit` and ` quit ` also exit.

```text
I am your AI Assistant. How can I help you today? (type 'quit' to exit) Explain attention in one sentence.
--------------------------------
Attention lets each token weigh the other tokens in the sequence when building its representation.
I am your AI Assistant. How can I help you today? (type 'quit' to exit) quit
Goodbye!
```

The model text above is an example of the layout. The live reply depends on the model and the prompt.

## How a turn works

1. The script appends your message to an in-memory list of `{role, content}` turns.
2. Earlier turns are sent as chat history. `user` stays `user`; `assistant` is sent as `model`.
3. The latest message is sent with `chat.send_message`.
4. The reply text is stored as an `assistant` turn and printed. An empty model response prints as a blank line.

There is no system prompt, tool use, or persistence between runs.

## Project structure

```text
.
├── .env.example      # Variable names and a sample model id
├── .gitignore        # Ignores .env, virtual environments, and local caches
├── README.md
├── main.py           # Interactive chat loop
└── requirements.txt  # Pinned Python dependencies
```

| File | Role |
| --- | --- |
| `main.py` | Loads configuration, keeps session history, and prints model replies |
| `requirements.txt` | Pins `google-genai==2.31.0` and `python-dotenv==1.2.4` |
| `.env.example` | Template for the local environment file |
| `.gitignore` | Keeps secrets and local environments out of git |

Create `.env` locally from `.env.example`. It is gitignored and should not be committed.

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `GEN_AI_API_KEY` | Yes | API key passed to `genai.Client` |
| `GEN_AI_MODEL` | Yes | Model id passed to `client.chats.create`, for example `gemini-flash-lite-latest` |

`main.py` calls `load_dotenv()` at startup. That loads `.env` from the current working directory, or from a parent directory if the file is not in the current one. Values already set in the process environment are left unchanged.

## Troubleshooting

**`ValueError: GEN_AI_API_KEY is not set in the environment.`**

`.env` is missing, the variable is empty, or the process was started somewhere `load_dotenv()` cannot reach the file. Copy `.env.example` to `.env` in the project root, set the key, and run `python main.py` from that directory.

**`ValueError: GEN_AI_MODEL is not set in the environment.`**

Set `GEN_AI_MODEL` in `.env`. The template uses `gemini-flash-lite-latest`.

**The API rejects the key or the model id**

A non-empty placeholder such as `your_api_key_here` passes the startup check. Authentication and model errors are raised by the Google Gen AI SDK and stop the process; `main.py` does not catch them. Confirm the key, the model id, and that the key is allowed to call that model.

## Security

Store the API key only in `.env`. Commit `.env.example`, which contains a placeholder, and leave `.env` untracked.
