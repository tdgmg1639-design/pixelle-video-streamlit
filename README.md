# Pixelle-Video Streamlit Deploy

Lightweight Streamlit Cloud launcher for Pixelle-Video v0.1.15.

## Streamlit entrypoint

```text
streamlit_app.py
```

## Secrets

Add these in Streamlit Cloud app settings:

```toml
[llm]
api_key = "your-llm-api-key"
base_url = "https://api.openai.com/v1"
model = "gpt-4o"

[comfyui]
runninghub_api_key = "your-runninghub-api-key"
runninghub_concurrent_limit = 1
runninghub_instance_type = ""
```
