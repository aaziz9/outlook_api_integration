import os

import requests
import uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Replace with your own secret key for session management
app.add_middleware(SessionMiddleware, secret_key="YOUR_SECRET_KEY")

# Configuration data
config_data = {
    'MICROSOFT_CLIENT_ID': os.environ.get("MICROSOFT_CLIENT_ID"),
    'MICROSOFT_CLIENT_SECRET': os.environ.get("MICROSOFT_CLIENT_SECRET"),
    'MICROSOFT_TENANT_ID': os.environ.get("MICROSOFT_TENANT_ID")
}

config = Config(environ=config_data)

# Initialize OAuth
oauth = OAuth(config)

oauth.register(
    name='microsoft',
    client_id=config('MICROSOFT_CLIENT_ID'),
    client_secret=config('MICROSOFT_CLIENT_SECRET'),
    server_metadata_url=f'https://login.microsoftonline.com/{config("MICROSOFT_TENANT_ID")}/v2.0/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'User.Read Mail.Read',
    }
)

@app.get("/")
async def homepage():
    return HTMLResponse('<a href="/login">Login with Microsoft</a>')

@app.get("/login")
async def login(request: Request):
    redirect_uri = "http://localhost:8080/auth"
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.microsoft.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f"OAuth Error: {error.error}", status_code=400)
    request.session['token'] = token
    print(f">>>>>>>>>>>>>> Token Object: {token}")
    return RedirectResponse(url='/emails')

@app.get("/emails")
async def emails(request: Request):
    token = request.session.get('token')
    if not token:
        return RedirectResponse(url='/')
    access_token = token['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    graph_endpoint = 'https://graph.microsoft.com/v1.0/me/messages'
    response = requests.get(graph_endpoint, headers=headers)
    if response.status_code != 200:
        return HTMLResponse(f"Error fetching emails: {response.text}", status_code=response.status_code)
    emails = response.json()
    return emails


if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
