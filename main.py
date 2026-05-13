import os

from dotenv import load_dotenv

from agent.agent_loop import AgentLoop
from llm.gemini_client import GeminiClient
from mcp_server.tools import TOOLS

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Set it in your .env file.")


def main():
    task = input("Enter task: ")

    llm = GeminiClient(GEMINI_API_KEY)
    agent = AgentLoop(llm_client=llm, tools=TOOLS)

    agent.run(task)


if __name__ == "__main__":
    main()
