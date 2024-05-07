#!/usr/bin/env python3
import os
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import base64
import re
import requests
from pypdf import PdfReader, PdfWriter
import io
import subprocess
from dotenv import load_dotenv
import argparse

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
    printer_name = os.getenv("CUPS_PRINTER_NAME", 'QL1110')

    command = f'lp -h {print_server_ip} -d {printer_name} {filename}'
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Check if there were any errors
    if process.returncode != 0:
        print(stdout.decode())
        print("Error:")
        print(stderr.decode())
        exit(1)

def get_download_link(messages, service):
    # Iterate through each email and find the internetmarke download link
    for message in messages[0:100]:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        for header in msg['payload']['headers']:
            if header['name'] == 'From':
                sender = header['value']
                if sender == 'service-shop@deutschepost.de':
                    message = msg['payload']['parts'][0]['parts'][1]['body']['data']
                    message_text = base64.urlsafe_b64decode(message).decode('utf-8')
                    # this will return the first message only! TODO: check all messages
                    return message_text
    return ''

def get_pdf_stream(message_text):
    """
    Extract the download link from the email message and download the PDF file.
    Retruns a BytesIO stream of the PDF file and a filename as a tuple.
    """
    url_pattern = r'href="(https://internetmarke\.deutschepost\.de/PcfExtensionWeb/document\?keyphase=[^"]+)"'
    download_link = re.findall(url_pattern, message_text)[0]

    # download the PDF file
    response = requests.get(download_link)
    if response.status_code != 200:
        print(f"Failed to download file from URL: {download_link}")
        exit(1)

    # Extract the filename from the URL
    filename = download_link.split('/')[-1]

    pdf_stream = io.BytesIO(response.content)
    return (pdf_stream, filename)

def main(args):
    # Load environment variables from the .env file
    load_dotenv()

    # Check if token.json file is present
    if not os.path.isfile('token.json'):
        # Set up OAuth credentials
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        redirect_uri = os.getenv("GOOGLE_CLOUD_REDIRECT_URI", 'http://127.0.0.1:8080')

        flow.redirect_uri = redirect_uri
        auth_uri = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        print(auth_uri[0])
        code = input('Enter the authorization code: ')
        flow.fetch_token(code=code)
        credentials = flow.credentials
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

    message_text = get_download_link(messages, service)
    if message_text == '':
        print('no messages found!')
        exit(0)

    pdf_stream, filename = get_pdf_stream(message_text)
    pdf_reader = PdfReader(pdf_stream)
    pdf_writer = PdfWriter()

    # Read the content of each page
    page = pdf_reader.pages[0]
    page_content = page.extract_text().split('\n')

    # Extract the tracking code and recipient name
    trackingcode = page_content[0].replace(' ', '')
    buewa = page_content[2].replace(' ', '')
    if buewa.upper() == 'BÜWA':
        reciepent = page_content[5].replace(' ', '_')
    else:
        # regular letter stamp
        reciepent = page_content[4].replace(' ', '_')

    # Resize the PDF if the resize flag is set
    if args.resize:
        page.mediabox.top = page.mediabox.top - 50
        page.mediabox.bottom = page.mediabox.bottom + 10
        pdf_writer.add_page(page)
        filename = f'Briefmarke_{reciepent}_{trackingcode}_resized.pdf'
        with open(filename, 'wb') as file:
            pdf_writer.write(file)
    else:
        filename = f'Briefmarke_{reciepent}_{trackingcode}.pdf'
        with open(filename, 'wb') as file:
            file.write(pdf_stream.getvalue())

    print(f"File '{filename}' downloaded successfully.")

    ask_for_print(filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Warenpost Label Downloader')
    parser.add_argument('-r', '--resize', action='store_true', help='Resize the PDF label to save paper')
    args = parser.parse_args()

    main(args)
