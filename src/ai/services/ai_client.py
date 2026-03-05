import json


OUTPUT_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'message': {'type': 'string'},
        'suggestions': {
            'type': 'array',
            'items': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'title': {'type': 'string'},
                    'why': {'type': 'string'},
                    'estimated_time_minutes': {'type': ['integer', 'null']},
                    'ingredients': {'type': 'array', 'items': {'type': 'string'}},
                    'steps': {'type': 'array', 'items': {'type': 'string'}},
                },
                'required': [
                    'title',
                    'why',
                    'estimated_time_minutes',
                    'ingredients',
                    'steps',
                ],
            },
        },
    },
    'required': ['message', 'suggestions'],
}


class AIClientError(Exception):
    def __init__(self, message, error_type='api_error'):
        super().__init__(message)
        self.error_type = error_type


class AITimeoutError(AIClientError):
    def __init__(self, message='timeout'):
        super().__init__(message, error_type='timeout')


class AIResponseValidationError(AIClientError):
    def __init__(self, message='invalid structured output'):
        super().__init__(message, error_type='validation')


class OpenAIStructuredClient:
    def suggest(self, mode, payload):
        try:
            from openai import APITimeoutError, OpenAI
        except ImportError as exc:
            raise AIClientError('OpenAI SDK is not available') from exc

        prompt = (
            'あなたは家庭料理の提案アシスタントです。'
            f' mode={mode}。'
            '必ず schema 準拠 JSON のみを返してください。'
            'minimum は提案 1 件（最大 2 件）、recommend は 2〜3 件。'
        )

        try:
            client = OpenAI()
            response = client.responses.create(
                model='gpt-4.1-mini',
                input=[
                    {
                        'role': 'system',
                        'content': [{'type': 'input_text', 'text': prompt}],
                    },
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'input_text',
                                'text': json.dumps(payload, ensure_ascii=False),
                            }
                        ],
                    },
                ],
                text={
                    'format': {
                        'type': 'json_schema',
                        'name': 'ai_meal_suggestions',
                        'strict': True,
                        'schema': OUTPUT_SCHEMA,
                    }
                },
                timeout=15,
            )
        except APITimeoutError as exc:
            raise AITimeoutError() from exc
        except Exception as exc:
            raise AIClientError(str(exc), error_type='api_error') from exc

        raw_text = getattr(response, 'output_text', '')
        if not raw_text:
            raise AIResponseValidationError('missing output_text')

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AIResponseValidationError('output is not valid JSON') from exc

        if not isinstance(parsed, dict):
            raise AIResponseValidationError('output is not object')

        suggestions = parsed.get('suggestions')
        message = parsed.get('message')
        if not isinstance(message, str) or not isinstance(suggestions, list):
            raise AIResponseValidationError('missing required keys')

        return {
            'message': message,
            'suggestions': suggestions,
        }
