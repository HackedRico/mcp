"""
Base schemas for MCP plugin API documentation.
Common schemas used across multiple endpoints.
"""

from marshmallow import Schema, fields


class ErrorResponseSchema(Schema):
    """Standard error response"""

    error = fields.Str(required=True, description="Error message")


class ModelConfigSchema(Schema):
    """LLM model configuration"""

    model = fields.Str(description="Model name/identifier (e.g., 'gpt-4', 'claude-3-5-sonnet')")
    temperature = fields.Float(description="Sampling temperature (0.0-1.0)")
    max_tokens = fields.Int(description="Maximum tokens to generate")
    api_key = fields.Str(description="API key for model provider. Recommended: configure server-side via DSPY_API_KEY environment variable")
    api_base = fields.Str(description="Base URL for API endpoint")
    timeout = fields.Int(description="Request timeout in seconds")

