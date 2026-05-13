import json

def parse_action(response_text):

    response_text = response_text.strip()

    try:
        action = json.loads(response_text)
        return action

    except Exception as e:
        raise ValueError(
            f"Could not parse LLM response: {response_text}"
        )