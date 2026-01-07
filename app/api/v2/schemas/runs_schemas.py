"""
Run management schemas for MCP plugin.
Handles listing and detailed viewing of MLflow runs.
"""

from marshmallow import Schema, fields


class ListRunsRequestSchema(Schema):
    """Request schema for listing runs with pagination"""

    limit = fields.Int(
        description="Maximum number of runs to return",
        default=100,
        metadata={"location": "query"},
    )
    offset = fields.Int(
        description="Offset for pagination",
        default=0,
        metadata={"location": "query"},
    )


class RunRecordSchema(Schema):
    """Basic run information for list view"""

    run_id = fields.Str(
        required=True,
        description="MLflow run ID"
    )
    experiment_id = fields.Str(
        required=True,
        description="MLflow experiment ID"
    )
    status = fields.Str(
        required=True,
        description="Run status (RUNNING, FINISHED, FAILED, etc.)"
    )
    start_time = fields.Int(
        description="Start timestamp (milliseconds since epoch)"
    )
    end_time = fields.Int(
        description="End timestamp (milliseconds since epoch)"
    )
    run_name = fields.Str(
        description="Run name"
    )
    prompt = fields.Str(
        description="Original prompt/task"
    )
    stage = fields.Str(
        description="Execution stage"
    )
    model = fields.Str(
        description="Model used"
    )
    process_result = fields.Str(
        description="Final result"
    )


class ListRunsResponseSchema(Schema):
    """Response schema for listing runs"""

    runs = fields.List(
        fields.Nested(RunRecordSchema),
        required=True,
        description="List of runs"
    )
    total = fields.Int(
        required=True,
        description="Total number of runs available"
    )
    limit = fields.Int(
        required=True,
        description="Limit used for pagination"
    )
    offset = fields.Int(
        required=True,
        description="Offset used for pagination"
    )


class GetRunDetailRequestSchema(Schema):
    """Request schema for getting detailed run information"""

    run_id = fields.Str(
        required=True,
        description="MLflow run ID to retrieve details for"
    )


class GetRunDetailResponseSchema(Schema):
    """Response schema for detailed run information"""

    run_id = fields.Str(
        required=True,
        description="MLflow run ID"
    )
    status = fields.Str(
        required=True,
        description="Run status"
    )
    start_time = fields.Int(
        description="Start timestamp (milliseconds since epoch)"
    )
    end_time = fields.Int(
        description="End timestamp (milliseconds since epoch)"
    )
    run_name = fields.Str(
        description="Run name"
    )
    experiment_id = fields.Str(
        description="Experiment ID"
    )
    params = fields.Dict(
        keys=fields.Str(),
        values=fields.Str(),
        description="Run parameters"
    )
    tags = fields.Dict(
        keys=fields.Str(),
        values=fields.Str(),
        description="Run tags"
    )
    trajectory = fields.Dict(
        keys=fields.Str(),
        values=fields.Str(),
        description="Full execution trajectory with thoughts, observations, and tool calls"
    )
    stage = fields.Str(
        description="Execution stage"
    )
    reasoning = fields.Str(
        description="Agent reasoning"
    )
    prompt = fields.Str(
        description="Original prompt"
    )
    process_result = fields.Str(
        description="Final processed result"
    )

