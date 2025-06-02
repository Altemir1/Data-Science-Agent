import gradio as gr
import pandas as pd
from io import StringIO
import os

# Shared state for the uploaded DataFrame
state = {"df": None}

def upload_csv(file=None, filename=None):
    if file is None and (filename is None or filename.strip() == ""):
        return "No file uploaded or filename provided."
    try:
        if file is not None:
            df = pd.read_csv(file.name)
        else:
            if not os.path.isfile(filename):
                return f"File '{filename}' not found in local directory."
            df = pd.read_csv(filename)
        state["df"] = df
        return f"CSV loaded with shape {df.shape}"
    except Exception as e:
        return f"Error: {e}"

def describe():
    """Returns a description of the dataset"""
    df = state["df"]
    if df is None:
        return "No dataset uploaded."
    return df.describe().to_dict()

def missing():
    """Returns missing value counts"""
    df = state["df"]
    if df is None:
        return "No dataset uploaded."
    return df.isnull().sum().to_dict()

def info():
    """Returns info about the dataset"""
    df = state["df"]
    if df is None:
        return "No dataset uploaded."
    buf = StringIO()
    df.info(buf=buf)
    return buf.getvalue()

# Create and run the MCP server
if __name__ == "__main__":
    with gr.Blocks() as demo:
        file_input = gr.File(label="Upload CSV", visible=True)
        filename_input = gr.Textbox(label="Or enter local filename", visible=True)
        upload_output = gr.Textbox(label="Upload Status")
        upload_btn = gr.Button("Load CSV")
        upload_btn.click(upload_csv, inputs=[file_input, filename_input], outputs=upload_output)

        describe_btn = gr.Button("Describe")
        describe_output = gr.JSON(label="Describe Output")
        describe_btn.click(describe, outputs=describe_output)

        missing_btn = gr.Button("Missing Values")
        missing_output = gr.JSON(label="Missing Output")
        missing_btn.click(missing, outputs=missing_output)

        info_btn = gr.Button("Info")
        info_output = gr.Textbox(label="Info Output")
        info_btn.click(info, outputs=info_output)

    demo.launch(mcp_server=True)
