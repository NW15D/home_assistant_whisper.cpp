# Home Assistant: Whisper API Integration for Speech-to-Text

Integration works for Assist pipelines. 

### Requirements:
- Installed Whisper.cpp server in network

### Server setup (whisper.cpp):
1. Git pull [whisper.cpp](https://github.com/ggerganov/whisper.cpp)
2. Build the server (example for CUDA):
```bash
cmake -B build -DGGML_CUDA=1
cmake --build build --config Release
```

3. Run the server:
```bash
./ai/whisper.cpp/build/bin/whisper-server -m /ai/models/whisper/ggml-large-v3-turbo-q8_0.bin --host 192.168.0.55 --port 5045 -l ru  -sow -sns --vad --vad-model /ai/models/whisper/ggml-silero-v6.2.0.bin --inference-path /v1/audio/transcriptions

```

### Configuration:

Configuration is done in the UI (YAML is no longer supported):

1. Install via HACS (or copy `custom_components/whisper_api_stt` to your config directory) and restart Home Assistant.
2. **Settings → Devices & services → Add integration → Whisper.cpp API**.
3. Fill in the form. Settings can be changed later via the integration's **Configure** button; the entry reloads automatically.

You can add several entries (e.g. different languages or servers).

> Upgrading from the YAML version: remove the `stt: - platform: whisper_api_stt` block from `configuration.yaml`, restart, and add the integration through the UI.

#### Parameters:
- `Server URL`: full URL of your whisper.cpp or OpenAI-compatible endpoint, e.g. `http://192.168.0.55:5045/v1/audio/transcriptions`.
- `API key` (optional): API key if required by your server.
- `Model`: model name. Defaults to `whisper-1` (whisper.cpp server ignores it).
- `Language`: language code (e.g., `en-US`, `ru-RU`).
- `Prompt` (optional): text to guide the model's style.
- `Temperature`: sampling temperature between 0 and 1. Defaults to `0.0`.

The form checks that the server is reachable before saving.

### Notes:
- The integration converts the language code to ISO-639-1 (e.g., `ru-RU` -> `ru`) for API compatibility.
- Ensure your `server_url` includes the full path to the endpoint, e.g., `/v1/audio/transcriptions`.

### Used sources + thanks to:
- sfortis/openai_tts: https://github.com/sfortis/openai_tts
