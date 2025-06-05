import pandas as pd
import gradio as gr
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

# CREDENTIALS_CONFIG = os.environ.get('CREDENTIALS_CONFIG')
# TOKEN_PATH = os.environ.get('TOKEN_PATH', 'token.json')
# CREDENTIALS_PATH = os.environ.get('CREDENTIALS_PATH', 'credentials.json')
# SERVICE_ACCOUNT_PATH = os.environ.get(
#     'SERVICE_ACCOUNT_PATH', 'service_account.json')
#
# # Working directory in Google Drive
# DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID', '')


def upload_csv(file=None):
    if file is None:
        return "No file uploaded or filename provided."
    try:
        df = pd.read_csv(file.name)
        return df
    except Exception as e:
        return f"Error: {e}"


# Create and run the MCP server
if __name__ == "__main__":
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

    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    with gr.Blocks() as demo:
        df = None
        with gr.Row():
            with gr.Column():
                sheet_input = gr.File(
                    label="Upload CSV",
                    file_types=["csv"],
                    visible=True,
                    show_label=True
                )
                sheet_link = gr.Textbox(
                    label="Link",
                    type='text',
                    lines=1,
                    placeholder='Link to sheets'
                )
            with gr.Column():
                gr.DataFrame(value=df, label="DataFrame")

    demo.launch(mcp_server=True)
