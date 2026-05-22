# Neyo Talk

Neyo Talk is a ChatGPT-style AI + SI branded assistant built with Flask.

## Features

- ChatGPT-style web UI
- Voice input through browser speech recognition
- Voice output through browser text-to-speech
- Deep Think mode
- Image prompt creation mode
- Website creation mode
- Memory storage with SQLite
- Saved facts
- Conversation history
- OpenAI API optional integration
- Render-ready deployment

## Environment Variables

OPENAI_API_KEY = optional OpenAI API key  
OPENAI_MODEL = gpt-4o-mini  
SECRET_KEY = Flask secret  
DATABASE_URL = optional external database  

## Render Deployment

Build command:
pip install -r requirements.txt

Start command:
gunicorn app:app

## Note

Neyo Talk does not have real consciousness. SI is used as a product/brand concept for synthetic-intelligence-style workflows.
