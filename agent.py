import os
from smolagents import InferenceClientModel, ToolCallingAgent, MCPClient

SYSTEM_PROMPT = """You are an expert in spreadsheets. You have access to tools for manipulating, analyzing, cleaning, and formatting spreadsheet data.
Use these tools whenever possible to answer user questions about Excel/CSV/Google Sheets-like documents.
Be concise, precise, and rely on structured tool use whenever needed."""

# Globally define agent
agent = None


def run_agent(prompt: str):
    """Run the agent with the provided prompt. Goes into Gradio main function"""
    full_prompt = f"{SYSTEM_PROMPT}\nTask: {prompt}"
    return agent.run(full_prompt, max_steps=3)

def list_tools():
    """List available tools."""
    if agent is None:
        raise ValueError("Agent is not initialized. Please run the agent first.")
    if not agent.get_tools():
        raise ValueError("No tools available. Please ensure the agent is initialized with tools.")
    #
    return [tool.name for tool in agent.get_tools()]

# Initialize the MCP client and agent
mcp_client = MCPClient({
    "url": "deployed_url_of_hugging_face_space", 
    "transport": "sse"
})

tools = mcp_client.get_tools()

model = InferenceClientModel(
    model_id="mistralai/Mistral-7B-Instruct-v0.1",
    provider="hf-inference",  # Need to find free or create modal provider
)

agent = ToolCallingAgent(model=model, tools=tools)

mcp_client.disconnect()