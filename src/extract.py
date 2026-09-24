import json

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY

_client = Anthropic(api_key=ANTHROPIC_API_KEY)

_PROMPT = """You are given the raw extracted text of a credit card statement.
Return ONLY a JSON array of transactions, no prose. Each item:
{{"date": "YYYY-MM-DD", "merchant": "string", "amount": number, "type": "debit"|"credit"}}

Ignore summary/totals lines, interest/fee schedules, and anything that is not
an individual transaction line. Amount is always positive; use "type" for
direction. If a value is unclear, make your best judgement from context.

STATEMENT TEXT:
{text}
"""


def extract_transactions(statement_text: str, model: str = "claude-haiku-4-5-20251001") -> list[dict]:
    response = _client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": _PROMPT.format(text=statement_text)}],
    )
    raw = response.content[0].text.strip()

    # Model occasionally wraps output in a ```json fence despite instructions.
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("[") :]

    return json.loads(raw)
