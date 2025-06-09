import pandas as pd
import gradio as gr
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

# Environment variables
ENV = os.environ.get('ENV', 'dev')  # Default to 'dev' if not set
GOOGLE_API = os.environ.get('GOOGLE_API')  # Will be None if not set


def upload_csv(file=None):
    """Handle CSV file upload"""
    if file is None:
        return "No file uploaded or filename provided.", None
    try:
        df = pd.read_csv(file.name)
        return "File uploaded successfully!", df
    except Exception as e:
        return f"Error: {e}", None


def create_services(creds):
    """Create Google Sheets and Drive services from credentials"""
    try:
        sheets = build('sheets', 'v4', credentials=creds)
        drive = build('drive', 'v3', credentials=creds)
        return sheets, drive
    except Exception as e:
        return None, None


def auth(token):
    creds = None
    try:
        if ENV == 'prod' and GOOGLE_API:
            # In production, use credentials from environment variable
            client_config = json.loads(GOOGLE_API)
            flow = InstalledAppFlow.from_client_config(
                client_config, SCOPES)
        else:
            # In development, use credentials from file
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)

        creds = flow.run_local_server(port=0)
        sheets_service, drive_service = create_services(creds)
        if sheets_service and drive_service:
            return (creds.to_json(), sheets_service, drive_service,
                    "Successfully authenticated with Google!")
        return creds.to_json(), None, None, "Services creation failed after authentication."
    except Exception as e:
        return None, None, None, f"Authentication failed: {str(e)}"


def refresh(token):
    creds = None
    if token:
        try:
            # Load credentials from the browser state
            creds = Credentials.from_authorized_user_info(
                json.loads(token), SCOPES)
        except Exception:
            return None, None, None, "Invalid credentials stored. Please authenticate again."

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                sheets_service, drive_service = create_services(creds)
                if sheets_service and drive_service:
                    return (creds.to_json(), sheets_service, drive_service,
                            "Credentials refreshed successfully!")
                return creds.to_json(), None, None, "Services creation failed after refresh."
            except Exception:
                return None, None, None, "Failed to refresh credentials. Please authenticate again."
        return None, None, None, "Please authenticate with Google."

    sheets_service, drive_service = create_services(creds)
    if sheets_service and drive_service:
        return creds.to_json(), sheets_service, drive_service, "Valid credentials found."
    return creds.to_json(), None, None, "Services creation failed."


if __name__ == "__main__":
    with gr.Blocks() as demo:
        token = gr.State(None)
        sheets_service = gr.State(None)
        drive_service = gr.State(None)
        df = gr.State(None)

        with gr.Row():
            with gr.Column(scale=1):
                # File upload and data display section
                with gr.Group():
                    data_status = gr.Textbox(
                        label="Data Status",
                        interactive=False
                    )
                    file_url = gr.Textbox(
                        label="Google Sheet URL",
                        type="text"
                    )
                    file_upload = gr.File(
                        label="Upload CSV",
                        file_types=["csv"],
                        visible=True
                    )
            with gr.Column(scale=2):
                # Authentication section
                with gr.Group():
                    auth_status = gr.Textbox(
                        label="Authentication Status",
                        interactive=False
                    )
                    auth_button = gr.Button("Authenticate with Google")
                # Chat interface
                with gr.Group():
                    chatbot = gr.Chatbot(
                        label="Data Science Assistant",
                        height=400
                    )
                    msg = gr.Textbox(
                        label="Type a command (e.g., /help)",
                        placeholder="Enter a command..."
                    )
        with gr.Row():
            df_display = gr.DataFrame(label="Current Data")

        # Event handlers
        demo.load(
            refresh,
            inputs=[token],
            outputs=[token, sheets_service, drive_service, auth_status]
        )

        auth_button.click(
            auth,
            inputs=[token],
            outputs=[token, sheets_service, drive_service, auth_status]
        )

        file_upload.upload(
            upload_csv,
            inputs=[file_upload],
            outputs=[data_status, df]
        )

        df.change(
            lambda x: x if x is not None else gr.DataFrame(),
            inputs=[df],
            outputs=[df_display]
        )

    demo.launch(mcp_server=True)
