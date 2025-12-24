import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import base64
from email import message_from_bytes

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def search_messages(service, query):
    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=5
    ).execute()

    return results.get("messages", [])

def get_message(service, msg_id):
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="raw"
    ).execute()
    return msg

def parse_email(raw_msg):
    raw_data = base64.urlsafe_b64decode(raw_msg["raw"])
    email_msg = message_from_bytes(raw_data)
    return email_msg

import re # move to the top

def extract_code(email_msg):
    body = email_msg.get_payload(decode=True).decode(errors="ignore")
    match = re.search(r"\b(\d{6})\b", body)
    return match.group(1) if match else None


# stealing old code

import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    
    if message.content.startswith('$code'):
        service = get_service()
        messages = search_messages(service, "from:noreply@github.com subject:\"[Github] Please verify your device\"")
        if not messages:
            print("No messages found.")
            exit()
        msg = get_message(service, messages[0]['id'])
        email_msg = parse_email(msg)
        code = extract_code(email_msg)
        await message.channel.send(f'github code: {code}')

from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv('TOKEN')


client.run(BOT_TOKEN)