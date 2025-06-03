import gradio as gr
import pandas as pd


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
    with gr.Blocks() as data_science_agent:
        df = None
        with gr.Row():
            with gr.Column():
                file_input = gr.File(
                    label="Upload CSV",
                    file_types=["csv"],
                    visible=True,
                    show_label=True
                )
            with gr.Column():
                gr.DataFrame(value=df, label="DataFrame")
                gr.Chatbot(type="messages", label="Chat")

    data_science_agent.launch(mcp_server=True)
