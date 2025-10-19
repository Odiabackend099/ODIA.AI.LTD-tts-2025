# ODIADEV-TTS Backend

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python -m app.main
   ```

## Running with Docker

1. Build the image:
   ```bash
   docker build -t odia-tts-backend .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 odia-tts-backend
   ```