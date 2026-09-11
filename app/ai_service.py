import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")




def analyze_expense(
    amount,
    category_name: str,
    description: str,
) -> dict:
    
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=60.0,
        max_retries=0,
    )

    prompt = f"""
You are reviewing an employee expense claim.

Amount: {amount} USD
Category: {category_name}
Description: {description}

Return JSON with exactly these fields:

{{
  "summary": "1-2 sentence summary",
  "flagged": true or false,
  "reason": "short explanation or null"
}}

Flag the expense only if the amount, category, or description appear inconsistent with each other.

Example:
Category: Office
Description: Flight ticket to London
This should be flagged because the description looks like Travel rather than Office.

Do not approve or reject the claim.
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    text = response.output_text

    return json.loads(text)