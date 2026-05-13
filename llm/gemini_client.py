import google.generativeai as genai

from prompts.system_prompt import SYSTEM_PROMPT
from utils.logger import logger


class GeminiClient:

    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name="gemini-3.1-flash-lite")

    def get_next_action(self, task, previous_actions):
        step_num = len(previous_actions) + 1

        prompt = f"""SYSTEM:
{SYSTEM_PROMPT}

MAIN TASK:
{task}

PREVIOUS ACTIONS ({len(previous_actions)} completed):
{previous_actions}

What is the next action?"""

        logger.info(f"[LLM] Prompt sent to Gemini (step {step_num}):")
        logger.info(f"[LLM]   Task            : {task}")
        logger.info(f"[LLM]   Actions so far  : {len(previous_actions)}")
        if previous_actions:
            last = previous_actions[-1]
            logger.info(f"[LLM]   Last action     : {last['action']}")
            logger.info(f"[LLM]   Last result     : {last['result']}")

        response = self.model.generate_content(prompt)
        return response.text
