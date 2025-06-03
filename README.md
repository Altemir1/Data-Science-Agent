---
title: Data Science Agent
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: 5.0.1
app_file: app.py
pinned: false
license: apache-2.0
short_description: Agent implements basic functions of Data Scientist
---

# Data Science Agent

A Gradio-based web application for data analysis with MCP (Machine Control Protocol) support. This tool provides an interactive interface for analyzing CSV datasets with various statistical tools.

## Features

- Upload CSV files through web interface or local path
- Statistical description of datasets
- Missing value analysis
- Detailed dataset information
- MCP server support for programmatic control

## Project Structure

```
.
├── src/
│   ├── tools/
│   │   └── data_tools.py    # Data analysis tools
│   ├── app/
│   │   └── gradio_app.py    # Gradio web interface
│   └── main.py              # Application entry point
├── requirements.txt
└── README.md
```

## Setup

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv env
   source env/bin/activate  # On Linux/Mac
   # or
   .\env\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/main.py
   ```

The application will be available at http://localhost:7860 by default.

## Usage

1. Upload a CSV file using the file upload button or provide a local file path
2. Use the various analysis tools:
   - "Describe Data" for statistical summary
   - "Missing Values" to check for null values
   - "Dataset Info" for detailed DataFrame information

## MCP Support

The application runs with MCP server enabled, allowing for programmatic control and integration with other tools.

TODO:
[ ] brainstorm
[ ] test functions
[ ] more dataframe functions

rakhat:
[ ] gradio components
[ ] chatbot 

altem:
[ ] connecting gradio client to mcp
[ ] project structure
