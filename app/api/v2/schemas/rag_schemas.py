"""
RAG (Retrieval-Augmented Generation) schemas for MCP plugin.
Handles file upload and listing for context/knowledge documents.
"""

from marshmallow import Schema, fields


class UploadRagResponseSchema(Schema):
    """Response schema for RAG file upload"""

    message = fields.Str(
        required=True,
        description="Upload status message"
    )
    filename = fields.Str(
        required=True,
        description="Uploaded filename"
    )
    size = fields.Int(
        required=True,
        description="File size in bytes"
    )
    path = fields.Str(
        required=True,
        description="Server-side file path"
    )


class RagFileSchema(Schema):
    """RAG file information"""

    filename = fields.Str(
        required=True,
        description="File name"
    )
    size = fields.Int(
        required=True,
        description="File size in bytes"
    )
    modified = fields.Str(
        required=True,
        description="Last modified timestamp (ISO 8601 format)"
    )


class ListRagResponseSchema(Schema):
    """Response schema for listing RAG files"""

    files = fields.List(
        fields.Nested(RagFileSchema),
        required=True,
        description="List of available RAG files"
    )

