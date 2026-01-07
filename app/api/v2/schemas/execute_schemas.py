"""
Execution schemas for MCP plugin.
Handles AI agent execution requests and responses.
"""

from marshmallow import Schema, fields
from plugins.mcp.app.api.v2.schemas.base_schemas import ModelConfigSchema


class ExecuteRequestSchema(Schema):
    """Request schema for executing AI agent tasks"""

    text = fields.Str(
        required=True,
        description="The prompt/task to execute"
    )
    execution_type = fields.Str(
        data_key="type",
        description="Execution focus type: 'factory', 'planner', or 'server'",
        default="factory"
    )
    config = fields.Nested(
        ModelConfigSchema,
        description="Optional model configuration overrides"
    )


class ExecuteResponseSchema(Schema):
    """Response schema for execution requests"""

    run_id = fields.Str(
        required=True,
        description="MLflow run ID for tracking execution"
    )
    status = fields.Str(
        description="Execution status"
    )
    result = fields.Str(
        description="Execution result or output"
    )
    message = fields.Str(
        description="Status message"
    )

