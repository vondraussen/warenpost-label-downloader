# Warenpost Label Downloader

## Overview
This Python script reads emails from a Gmail account and looks for emails from 'service-shop@deutschepost.de'. If it finds such an email, it will search for a download link of the shipping label (PDF) and download it. Then, it will prompt the user if they want to print it via a CUPS network printer.

## Requirements
- Python 3.x
- Dependencies listed in `requirements.txt`

## Setup
1. Clone or download this repository.
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the following environment variables:
   - `CUPS_SERVER_IP`: The IP address of your CUPS server.
   - `CUPS_PRINTER_NAME`: The name of your CUPS printer.
   - `GOOGLE_CLOUD_REDIRECT_URI`: The Oauth2 redirect uri set in google api console
4. Enable the Gmail API for your Google account:
   - Go to the [Google API Console](https://console.developers.google.com/).
   - Create a new project and enable the Gmail API.
   - Create OAuth 2.0 credentials.
   - Download the credentials file (usually `client_secret.json`).
5. Place the downloaded `client_secret.json` file in the same directory as the script.

## Usage
1. Run the script:
   ```bash
   python warenpost_label_downloader.py
   ```
2. Follow the instructions in the terminal.
3. If the script finds an email from 'service-shop@deutschepost.de' with a shipping label attachment, it will download the label.
4. After downloading, the script will prompt you if you want to print the label via your configured CUPS network printer.

## Notes
- Make sure to keep your `client_secret.json` and `token.json` files secure and not expose it publicly.
- Customize the script as needed to fit your specific requirements.
