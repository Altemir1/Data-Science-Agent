import pandas as pd
import gradio as gr
import json
from typing import Optional, Dict, Any, List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import mcp_tools as mcp

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

# Define available commands and their descriptions
COMMANDS = {
    'describe': 'Get statistical description of the data',
    'missing': 'Show missing values in the data',
    'info': 'Get detailed information about the data',
    'create_sheet': 'Create a new Google Spreadsheet',
    'upload': 'Upload current data to Google Drive',
    'write': 'Write data to a Google Spreadsheet',
    'read': 'Read data from a Google Spreadsheet',
    'list': 'List files in Google Drive',
    'help': 'Show available commands'
}

def get_help_message() -> str:
    """Generate help message with available commands"""
    message = "Available commands:\n\n"
    for cmd, desc in COMMANDS.items():
        message += f"/{cmd} - {desc}\n"
    return message


def process_command(command: str, 
                   args: List[str], 
                   df: Optional[pd.DataFrame],
                   sheets_service: Optional[Any],
                   drive_service: Optional[Any]) -> Tuple[str, Optional[pd.DataFrame]]:
    """
    Process chat commands and return appropriate response
    """
    if command == 'help':
        return get_help_message(), df

    if command in ['describe', 'missing', 'info'] and df is None:
        return "No data loaded. Please upload a CSV file first.", None

    if command in ['create_sheet', 'upload', 'write', 'read', 'list'] and \
       (sheets_service is None or drive_service is None):
        return "Not authenticated with Google. Please authenticate first.", df

    try:
        if command == 'describe':
            result = mcp.describe(df)
            return f"Statistical Description:\n{json.dumps(result, indent=2)}", df

        elif command == 'missing':
            result = mcp.missing_values(df)
            return f"Missing Values:\n{json.dumps(result, indent=2)}", df

        elif command == 'info':
            result = mcp.get_info(df)
            return f"Dataset Info:\n{result}", df

        elif command == 'create_sheet':
            if len(args) < 1:
                return "Please provide a name for the spreadsheet: /create_sheet <name>", df
            sheet_id = mcp.create_spreadsheet(sheets_service, args[0])
            if sheet_id:
                return f"Created new spreadsheet with ID: {sheet_id}", df
            return "Failed to create spreadsheet", df

        elif command == 'upload':
            if df is None:
                return "No data to upload. Please load a CSV file first.", None
            if len(args) < 1:
                return "Please provide a filename: /upload <filename>", df
            
            # Save DataFrame to temporary CSV
            temp_path = f"temp_{args[0]}.csv"
            df.to_csv(temp_path, index=False)
            
            file_id = mcp.upload_to_drive(drive_service, temp_path, 'text/csv')
            if file_id:
                return f"File uploaded successfully with ID: {file_id}", df
            return "Failed to upload file", df

        elif command == 'write':
            if df is None:
                return "No data to write. Please load a CSV file first.", None
            if len(args) < 1:
                return "Please provide spreadsheet ID: /write <spreadsheet_id>", df
            
            # Convert DataFrame to list of lists
            data = [df.columns.tolist()] + df.values.tolist()
            success = mcp.write_to_sheet(sheets_service, args[0], data)
            if success:
                return "Data written to sheet successfully", df
            return "Failed to write data to sheet", df

        elif command == 'read':
            if len(args) < 1:
                return "Please provide spreadsheet ID: /read <spreadsheet_id>", df
            new_df = mcp.read_sheet(sheets_service, args[0])
            if new_df is not None:
                return "Data loaded from sheet successfully", new_df
            return "Failed to read data from sheet", df

        elif command == 'list':
            files = mcp.list_files(drive_service, 
                                 file_type='application/vnd.google-apps.spreadsheet')
            if files:
                file_list = "\n".join([f"- {f['name']} (ID: {f['id']})" for f in files])
                return f"Available Spreadsheets:\n{file_list}", df
            return "No spreadsheets found or error occurred", df

        else:
            return f"Unknown command. Type /help to see available commands.", df

    except Exception as e:
        return f"Error processing command: {str(e)}", df


def process_chat(message: str, 
                history: List[Tuple[str, str]], 
                df: Optional[pd.DataFrame],
                sheets_service: Optional[Any],
                drive_service: Optional[Any]) -> Tuple[str, List[Tuple[str, str]], Optional[pd.DataFrame]]:
    """
    Process chat messages and commands
    """
    if message.startswith('/'):
        # Split command and arguments
        parts = message[1:].split()
        command = parts[0].lower()
        args = parts[1:]
        
        response, new_df = process_command(command, args, df, sheets_service, drive_service)
        history.append((message, response))
        return response, history, new_df
    
    # Handle non-command messages
    response = "Type /help to see available commands"
    history.append((message, response))
    return response, history, df


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
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        # Store the token in browser state
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
        # Initialize states
        token = gr.BrowserState(None, storage_key="token")
        sheets_service = gr.State(None)
        drive_service = gr.State(None)
        df = gr.State(None)
        
        with gr.Row():
            with gr.Column(scale=2):
                # File upload and data display section
                with gr.Group():
                    file_upload = gr.File(
                        label="Upload CSV",
                        file_types=["csv"],
                        visible=True
                    )
                    data_status = gr.Textbox(
                        label="Data Status",
                        interactive=False
                    )
                    df_display = gr.DataFrame(label="Current Data")
                
                # Help section
                with gr.Group():
                    gr.Markdown("### Quick Help")
                    gr.Markdown("""
                    1. Upload a CSV file
                    2. Authenticate with Google
                    3. Use commands in chat:
                       - /help - Show all commands
                       - /describe - Get data stats
                       - /create_sheet - Create new sheet
                       - /upload - Save to Drive
                    """)
                
            with gr.Column(scale=1):
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
                # Authentication section
                with gr.Group():
                    auth_status = gr.Textbox(
                        label="Authentication Status",
                        interactive=False
                    )
                    auth_button = gr.Button("Authenticate with Google")

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

        msg.submit(
            process_chat,
            inputs=[msg, chatbot, df, sheets_service, drive_service],
            outputs=[msg, chatbot, df]
        )

    demo.launch(mcp_server=True)
