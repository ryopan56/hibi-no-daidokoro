import json


WEEKLY_PRAISE_INPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "feature": {
            "type": "string",
            "enum": ["weekly_praise"],
        },
        "period": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
            },
            "required": ["start_date", "end_date"],
        },
        "logs": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "log_date": {"type": "string"},
                    "result": {
                        "type": ["string", "null"],
                        "enum": ["COOKED", "NOT_COOKED", "BOUGHT", "EAT_OUT", "FROZEN", "LEFTOVER", None],
                    },
                    "cook_granularity": {
                        "type": ["string", "null"],
                        "enum": ["FULL", "SIMPLE", "WARMED", "CUT_ONLY", "PLATED", None],
                    },
                    "minimum_mode": {"type": ["boolean", "null"]},
                    "comment": {"type": ["string", "null"]},
                    "weather": {
                        "type": ["string", "null"],
                        "enum": ["SUNNY", "RAINY", "SNOWY", "WINDY", None],
                    },
                    "temp_feel": {
                        "type": ["string", "null"],
                        "enum": ["COLD", "JUST", "HOT", None],
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "log_date",
                    "result",
                    "cook_granularity",
                    "minimum_mode",
                    "comment",
                    "weather",
                    "temp_feel",
                    "tags",
                ],
            },
        },
    },
    "required": ["feature", "period", "logs"],
}

WEEKLY_PRAISE_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["headline", "message"],
}

WEEKLY_PRAISE_PROMPT = (
    "1週間のログを随筆調にふりかえってください。"
    "数字で評価せず、グラフ的にしないでください。"
    "空白日を責めず、継続・判断・ケア・感性のどれかに触れてください。"
    "少しだけ文学的でもよいですが、気取りすぎないでください。"
)

WEEKLY_PRAISE_FALLBACK = {
    "headline": "今週の台所",
    "message": "今週もおつかれさまでした。小さな積み重ねが、ちゃんと前に進んでいます。",
}


class WeeklyPraiseError(Exception):
    def __init__(self, message, error_type="api_error"):
        super().__init__(message)
        self.error_type = error_type


class WeeklyPraiseTimeoutError(WeeklyPraiseError):
    def __init__(self, message="timeout"):
        super().__init__(message, error_type="timeout")


def generate_weekly_praise(payload):
    try:
        from openai import APITimeoutError, OpenAI
    except ImportError as exc:
        raise WeeklyPraiseError("OpenAI SDK is not available") from exc

    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": WEEKLY_PRAISE_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": json.dumps(payload, ensure_ascii=False)}],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "weekly_praise_output",
                    "strict": True,
                    "schema": WEEKLY_PRAISE_OUTPUT_SCHEMA,
                }
            },
            timeout=15,
        )
    except APITimeoutError as exc:
        raise WeeklyPraiseTimeoutError() from exc
    except Exception as exc:
        raise WeeklyPraiseError(str(exc), error_type="api_error") from exc

    output_text = getattr(response, "output_text", "")
    if not output_text:
        raise WeeklyPraiseError("missing output_text", error_type="validation")

    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise WeeklyPraiseError("output is not valid JSON", error_type="validation") from exc

    if not isinstance(parsed, dict):
        raise WeeklyPraiseError("output is not object", error_type="validation")
    if not isinstance(parsed.get("headline"), str) or not isinstance(parsed.get("message"), str):
        raise WeeklyPraiseError("missing required keys", error_type="validation")

    return parsed
