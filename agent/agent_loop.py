import time

from llm.action_parser import parse_action
from utils.logger import logger

_DIVIDER = "=" * 60


class AgentLoop:

    def __init__(self, llm_client, tools):
        self.llm = llm_client
        self.tools = tools

    def run(self, task):
        previous_actions = []
        step = 0

        logger.info(_DIVIDER)
        logger.info("AGENT STARTED")
        logger.info(f"Task: {task}")
        logger.info(_DIVIDER)

        while True:
            step += 1
            logger.info("")
            logger.info(f"--- STEP {step} ---")
            logger.info(f"History so far: {len(previous_actions)} action(s) completed")

            # ── LLM call ──────────────────────────────────────────────
            logger.info("[LLM] Sending task + history to Gemini...")
            t0 = time.perf_counter()

            response = self.llm.get_next_action(task, previous_actions)

            elapsed = time.perf_counter() - t0
            logger.info(f"[LLM] Response received in {elapsed:.2f}s")
            logger.info(f"[LLM] Raw response:\n{response.strip()}")

            # ── Parse ─────────────────────────────────────────────────
            action_json = parse_action(response)
            action_name = action_json["action"]
            logger.info(f"[PARSE] Action: '{action_name}'  |  Full JSON: {action_json}")

            # ── Finish check ──────────────────────────────────────────
            if action_name == "finish":
                logger.info("")
                logger.info(_DIVIDER)
                logger.info(f"AGENT FINISHED after {step} step(s)")
                logger.info(_DIVIDER)
                break

            # ── Execute tool ──────────────────────────────────────────
            tool = self.tools[action_name]
            logger.info(f"[TOOL] Executing: '{action_name}'")

            t1 = time.perf_counter()

            if action_name == "add_text":
                result = tool(action_json["text"])
            elif action_name == "set_color":
                result = tool(action_json["color_name"])
            elif action_name in ("pick_color", "fill_color"):
                result = tool(action_json["x"], action_json["y"])
            else:
                result = tool()

            tool_elapsed = time.perf_counter() - t1
            logger.info(f"[TOOL] '{action_name}' completed in {tool_elapsed:.2f}s  |  Result: {result}")

            previous_actions.append({
                "action": action_json,
                "result": result,
            })
