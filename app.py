import pandas as pd
import gradio as gr
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']


def upload_csv(file=None):
    if file is None:
        return "No file uploaded or filename provided."
    try:
        df = pd.read_csv(file.name)
        return df
    except Exception as e:
        return f"Error: {e}"


def auth(token):
    creds = None
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        # Store the token in browser state
        creds = flow.run_local_server(port=0)
        return creds.to_json(), "Successfully authenticated with Google!"
    except Exception as e:
        return None, f"Authentication failed: {str(e)}"


def refresh(token):
    creds = None
    if token:
        try:
            # Load credentials from the browser state
            creds = Credentials.from_authorized_user_info(
                json.loads(token), SCOPES)
        except Exception:
            return None, "Invalid credentials stored. Please authenticate again."

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return creds.to_json(), "Credentials refreshed successfully!"
            except Exception:
                return None, "Failed to refresh credentials. Please authenticate again."
        return None, "Please authenticate with Google."
    return creds.to_json(), "Valid credentials found."


if __name__ == "__main__":
    with gr.Blocks() as demo:
        # Initialize browser state for storing token
        token = gr.BrowserState(None, storage_key="token")

        df = gr.State(None)

        with gr.Column():
            with gr.Row():
                with gr.Column():
                    with gr.Group():
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
                    with gr.Group():
                        auth_status = gr.Textbox(
                            label="Authentication Status",
                            interactive=False
                        )
                        auth_button = gr.Button("Authenticate with Google")

            output_df = gr.DataFrame(label="DataFrame")

        # Handle initial credential refresh on app load
        demo.load(
            refresh,
            inputs=[token],
            outputs=[token, auth_status]
        )

        auth_button.click(
            auth,
            inputs=[token],
            outputs=[token, auth_status]
        )

        sheet_input.change(
            upload_csv,
            inputs=[sheet_input],
            outputs=[output_df]
        )

    demo.launch(mcp_server=True)
