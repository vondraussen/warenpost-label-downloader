#!/usr/bin/env python3
import os
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import base64
import re
import requests
from pypdf import PdfReader
import io
import subprocess
from dotenv import load_dotenv

def ask_for_print(filename):
    question = 'Do you want to print this label?'

    while True:
        response = input(question + " (Y/n): ").strip().lower()
        if response in ['y', '']:
            print_pdf(filename)
            return
        if response == 'n':
            return
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def print_pdf(filename):
    # Access the environment variables
    print_server_ip = os.getenv("CUPS_SERVER_IP", '127.0.0.1')
    print_name = os.getenv("CUPS_PRINTER_NAME", 'QL1110')

    command = f'lp -h {print_server_ip} -d {print_name} {filename}'
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Check if there were any errors
    if process.returncode != 0:
        print(stdout.decode())
        print("Error:")
        print(stderr.decode())
        exit(1)

# Load environment variables from the .env file
load_dotenv()

# Check if token.json file is present
if not os.path.isfile('token.json'):
    # Set up OAuth credentials
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    credentials = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(credentials.to_json())
else:
    # Load existing credentials from token.json
    with open('token.json', 'r') as token:
        data = json.load(token)
        credentials = Credentials('access_token',
                                  refresh_token=data['refresh_token'],
                                  token_uri=data['token_uri'],
                                  client_id=data['client_id'],
                                  client_secret=data['client_secret'])

# Set up the Gmail API client
service = build('gmail', 'v1', credentials=credentials)
# Retrieve all emails from the account
results = service.users().messages().list(userId='me').execute()
messages = results.get('messages', [])

message_text = ''

# Iterate through each email and find the internetmarke download link
for message in messages[0:10]:
    msg = service.users().messages().get(userId='me', id=message['id']).execute()
    for header in msg['payload']['headers']:
        if header['name'] == 'From':
            sender = header['value']
            if sender == 'service-shop@deutschepost.de':
                message = msg['payload']['parts'][0]['parts'][1]['body']['data']
                message_text = base64.urlsafe_b64decode(message).decode('utf-8')

if message_text == '':
    print('no messages found!')
    exit(0)

# Define the URL pattern
url_pattern = r'href="(https://internetmarke\.deutschepost\.de/PcfExtensionWeb/document\?keyphase=[^"]+)"'

# Search for the URL pattern in the decoded data
matches = re.findall(url_pattern, message_text)

# Print the matched URLs
response = requests.get(matches[0])
if response.status_code != 200:
    print(f"Failed to download file from URL: {matches[0]}")
    exit(1)

# Extract the filename from the URL
filename = matches[0].split('/')[-1]

pdf_stream = io.BytesIO(response.content)
pdf_reader = PdfReader(pdf_stream)

# Read the content of each page
page = pdf_reader.pages[0]
page_content = page.extract_text().split('\n')

# Do something with the page content
trackingcode = page_content[0].replace(' ', '')
reciepent = page_content[5].replace(' ', '_')

filename = f'Briefmarke_{reciepent}_{trackingcode}.pdf'
# Check if the file is already downloaded
if os.path.isfile(filename):
    print(f'File {filename} is already downloaded!')
else:
    # Save the file
    with open(filename, 'wb') as file:
        file.write(response.content)
    print(f"File '{filename}' downloaded successfully.")

ask_for_print(filename)
