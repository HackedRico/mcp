"""
Status tracking schemas for MCP plugin.
Handles run status queries and trajectory information.
"""

from marshmallow import Schema, fields


class StatusRequestSchema(Schema):
    """Request schema for checking execution status"""

    run_id = fields.Str(
        required=True,
        description="MLflow run ID to check status for"
    )


class StatusResponseSchema(Schema):
    """Response schema for status queries"""

    run_id = fields.Str(
        required=True,
        description="MLflow run ID"
    )
    status = fields.Str(
        required=True,
        description="Run status (RUNNING, FINISHED, FAILED, etc.)"
    )
    stage = fields.Str(
        description="Current execution stage"
    )
    prompt = fields.Str(
        description="Original prompt/task"
    )
    reasoning = fields.Str(
        description="Agent reasoning or decision-making process"
    )
    process_result = fields.Str(
        description="Final processed result"
    )
    trajectory = fields.Dict(
        keys=fields.Str(),
        values=fields.Str(),
        description="Execution trajectory with thoughts, observations, and tool calls"
    )

