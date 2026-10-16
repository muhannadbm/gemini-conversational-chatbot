# Multi-provider Conversational Chatbot

A command-line chatbot that keeps the conversation in memory and sends it to Google Gemini, OpenAI, or Anthropic Claude. At startup you type the provider. A factory builds the matching adapter, and that adapter translates the shared history into the vendor's current API. History is discarded when the process exits.

## Prerequisites

- Python 3.10 or newer
- An API key for the provider you select:
  - [Google AI Studio](https://aistudio.google.com/apikey) for Gemini
  - [OpenAI](https://platform.openai.com/api-keys) for OpenAI
  - [Anthropic](https://platform.claude.com/settings/keys) for Claude

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

Open `.env` and set a real API key. The provider is not read from the environment. `main.py` asks you to type `google`, `openai`, or `anthropic`. Change `GEN_AI_MODEL` to an id that the provider you choose accepts. The app does not rewrite the model id for you.

## Run

From the project root, with the virtual environment active:

```powershell
python main.py
```

The script first asks you to choose a provider. Type `google`, `openai`, or `anthropic` and press Enter. Matching ignores case and surrounding spaces. An empty line or any other name prints the allowed names and asks again. Type `quit` to leave before the chat starts.

The chat then prompts on one line. Type a message and press Enter. The reply is printed after a line of hyphens. Type `quit` to leave. `Quit` and ` quit ` also exit.

```text
Choose a provider (google, openai, anthropic). Type 'quit' to exit: nope
Unknown provider 'nope'. Expected one of: google, openai, anthropic.
Choose a provider (google, openai, anthropic). Type 'quit' to exit: google
I am your AI Assistant. How can I help you today? (type 'quit' to exit) Explain attention in one sentence.
--------------------------------
Attention lets each token weigh the other tokens in the sequence when building its representation.
I am your AI Assistant. How can I help you today? (type 'quit' to exit) quit
Goodbye!
```

The model text above is an example of the layout. The live reply depends on the provider, the model, and the prompt.

## How a turn works

1. You choose `google`, `openai`, or `anthropic`. `main.py` prints a `ConfigError` when that name is not one of those values, when the model id is missing, or when the matching API key is missing.
2. The script appends your message to an in-memory list of `Message` turns. Roles are `user` and `assistant`.
3. The selected adapter sends that list to the vendor. Gemini receives earlier turns as chat history (`assistant` is sent as `model`) and the latest line as the new message. OpenAI and Anthropic receive the full list on each call.
4. The reply text is stored as an `assistant` turn and printed. An empty model response prints as a blank line. A provider failure is printed as `ProviderError`.

There is no system prompt, tool use, or persistence between runs. The process is the source of truth for history. The OpenAI adapter sets `store=False` so the Responses API does not keep a server-side transcript.

## Design

This project uses more than one design pattern on purpose. Together they show how a chat client stays vendor-neutral and testable as providers are added.

- **Adapter.** Gemini, OpenAI, and Anthropic do not share a method, a role name, or a response shape. Each adapter wraps one SDK behind `ChatProvider.complete`, so the conversation loop can stay the same while those differences stay in `GoogleChatProvider`, `OpenAIChatProvider`, and `AnthropicChatProvider`. Role names, sampling field names, and where the reply text lives are translated inside the adapter.
- **Factory.** The loop still has to receive one concrete adapter. You type the provider at startup, and `ProviderFactory` turns that `Provider` value into the matching class. `main.py` does not import the SDKs or branch on the vendor name. A name outside the enum raises `ConfigError`, and `main.py` prints that message. Registering another provider is a new class plus one `register` call in `chatbot/providers/__init__.py`.
- **Dependency injection.** Each adapter takes its SDK client as an optional constructor argument. Production code builds the real client from the API key. Tests pass a fake, so the suite never calls a live API.

## Project structure

```text
.
├── .env.example                 # Variable names and a sample model id
├── .gitignore                   # Ignores .env, virtual environments, and local caches
├── README.md
├── main.py                      # Loads settings, builds a provider, starts the prompt
├── requirements.txt             # Pinned Python dependencies
├── chatbot/
│   ├── cli.py                   # Interactive prompt loop
│   ├── config.py                # Settings loaded from the environment
│   ├── conversation.py          # In-memory session history
│   ├── errors.py                # ConfigError and ProviderError
│   ├── messages.py              # Provider-neutral turns
│   └── providers/
│       ├── base.py              # ChatProvider and shared sampling helpers
│       ├── factory.py           # ProviderFactory
│       ├── google.py            # Gemini chats
│       ├── openai.py            # OpenAI Responses API
│       └── anthropic.py         # Anthropic Messages API
└── tests/                       # Stdlib unittest suite, no live API calls
```

| File | Role |
| --- | --- |
| `main.py` | Entry point. Loads `.env`, asks the factory for an adapter, and starts the loop |
| `chatbot/cli.py` | Reads lines and prints replies |
| `chatbot/conversation.py` | Owns the session list of turns |
| `chatbot/providers/` | Adapters and the factory that selects one |
| `requirements.txt` | Pins `google-genai==2.31.0`, `openai==3.31.0`, `anthropic==1.15.0`, and `python-dotenv==1.2.4` |
| `.env.example` | Template for the local environment file |
| `.gitignore` | Keeps secrets and local environments out of git |

Create `.env` locally from `.env.example`. It is gitignored and should not be committed.

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `GEN_AI_MODEL` | Yes | Model id for the provider you type at startup |
| `GOOGLE_API_KEY` | For Google | Preferred Gemini key. `GEN_AI_API_KEY` is accepted when this is empty |
| `OPENAI_API_KEY` | For OpenAI | Preferred OpenAI key. `GEN_AI_API_KEY` is accepted when this is empty |
| `ANTHROPIC_API_KEY` | For Anthropic | Preferred Claude key. `GEN_AI_API_KEY` is accepted when this is empty |
| `GEN_AI_API_KEY` | Fallback | Used when the selected provider's own key variable is empty |
| `GEN_AI_TEMPERATURE` | No | Sampling temperature. Omitted from the request when unset |
| `GEN_AI_TOP_P` | No | Nucleus sampling. Omitted from the request when unset |
| `GEN_AI_MAX_TOKENS` | No | Output token cap. Defaults to `4096` |

`main.py` calls `load_dotenv()` at startup. That loads `.env` from the current working directory, or from a parent directory if the file is not in the current one. Values already set in the process environment are left unchanged.

### Sampling

The app exposes one set of knobs. Each adapter maps them onto the field names in that vendor's current API.

| App setting | Google | OpenAI | Anthropic |
| --- | --- | --- | --- |
| `GEN_AI_TEMPERATURE` | `temperature` on `GenerateContentConfig` (0.0–2.0) | `temperature` on `responses.create` (0–2) | `temperature` in the JSON body (0.0–1.0) |
| `GEN_AI_TOP_P` | `top_p` (0.0–1.0) | `top_p` (0–1) | `top_p` in the JSON body (0.0–1.0) |
| `GEN_AI_MAX_TOKENS` | `max_output_tokens` | `max_output_tokens` | `max_tokens` on `messages.create` |

`anthropic` 1.15 no longer has `temperature` or `top_p` on `messages.create`. The adapter sends those two fields with `extra_body`, which the SDK merges into the request JSON. `max_tokens` stays a normal argument.

OpenAI recommends setting `temperature` or `top_p`, and not both. The adapter still forwards both when both are set. `max_output_tokens` on OpenAI counts visible output and reasoning tokens.

A value outside the selected provider's range raises `ConfigError` before any network call. Vendor defaults apply when `GEN_AI_TEMPERATURE` or `GEN_AI_TOP_P` is unset.

Some current models ignore or reject custom sampling:

- Gemini 3.6 Flash and newer, including Gemini 4, ignore `temperature` and `top_p`. A later Gemini release is expected to reject them with HTTP 400.
- Some OpenAI reasoning models reject `temperature` and `top_p` unless reasoning effort is `none`.
- Claude models after Claude Opus 4.6, including Claude 4.7 and later, accept `temperature` only at `1.0` and reject `top_p` below `0.99`.

The adapter still sends a value you set. If the model rejects it, the SDK error is raised as `ProviderError` and `main.py` prints that message.

Sample model ids from the vendor docs, for a key that can call them:

- Google: `gemini-flash-lite-latest`
- OpenAI: `gpt-5.2`
- Anthropic: `claude-opus-5-5`

## Tests

From the project root:

```powershell
python -m unittest discover -s tests -t .
```

The suite checks configuration, the factory, session memory, the prompt loop, sampling kwargs, and response-text extraction. It does not call a live API.

## Troubleshooting

**`Unknown provider ...`**

The startup prompt only accepts `google`, `openai`, or `anthropic`. The message lists those names, and the prompt is shown again. Type `quit` to leave.

**`ConfigError: GEN_AI_MODEL is not set in the environment.`**

Set `GEN_AI_MODEL` in `.env` to a model id the provider you choose can call.

**`ConfigError: GOOGLE_API_KEY is not set in the environment.`**

The same message is printed for `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` when that provider is selected. `main.py` prints the `ConfigError` and exits. Set the provider key, or set `GEN_AI_API_KEY` as the fallback. Copy `.env.example` to `.env` in the project root and run `python main.py` from that directory.

**`ConfigError: GEN_AI_TEMPERATURE must be between ...`**

The number is outside the range for the selected provider. Anthropic's temperature stops at `1.0`. Google and OpenAI allow up to `2.0`. `GEN_AI_TOP_P` is `0.0` to `1.0` for all three. `GEN_AI_MAX_TOKENS` must be an integer of at least `1`.

**The API rejects the key, the model id, or the sampling values**

A non-empty placeholder such as `your_api_key_here` passes the startup check. Authentication, model, and sampling errors are raised by the SDK, wrapped as `ProviderError`, and printed by `main.py`. Confirm the key, the model id, and that the model accepts the temperature and top-p you set.

## Security

Store API keys only in `.env`. Commit `.env.example`, which contains placeholders, and leave `.env` untracked.
