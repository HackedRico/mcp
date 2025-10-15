# Caldera MCP 

## Summary
An end-to-end system that orchestrates long-running LLM workflows to create Caldera abilities and adversaries. It optionally enriches those workflows with Retrieval-Augmented Generation (RAG) using Cyber Threat Intelligence (CTI) STIX JSON files. MLflow is used to track runs, status, stages, and “thoughts,” enabling insight into the LLM processes and exact tool calls. 

## Quick start
- Start caldera with
  - `python3 server.py --insecure`
- Ensure MCP plugin is registered with Caldera
- Choose your pathway:
  - Ability Factory
  - Planner 
- Enter your API-key and chosen model, the current system supports (most) many inference providers and frontier lab models
- Enter your prompt!

## Core pieces
- Frontend (Vue)
  - Lets users enter a prompt and model settings.
  - Manages RAG files: upload, list, select specific files per run, and set RAG options (embedding model, top-K).
  - Submits a job and polls MLflow for status, stage, and trajectory to render progress and results.
- Backend API (aiohttp)
  - Starts a run and returns a run_id.
  - Exposes run status via MLflow.
  - Handles RAG file upload/listing.
- Service Orchestration (MCPService)
  - Creates MLflow runs and manages background execution.
  - Configures DSPy’s LLM (from user-provided config).
  - When RAG files are selected, builds a per-run RAG corpus, embeds it, and produces contextual signals for downstream logic.
- DSPy Clients (Factory/Planner)
  - Drive tool-using workflows (via MCP) to generate abilities/adversaries.
  - Consume RAG context when provided.
  - Log reasoning, results, and trajectory to MLflow.
- RAG (RAGService)
  - Loads selected STIX JSON files, extracts relevant text, and embeds them.
  - Provides a retriever and task-specific context (search results, details, thoughts).

## RAG behavior (high-level)
- RAG is opt-in per run: users select which uploaded STIX JSON files to include.
- The backend embeds only the selected files for that run, then produces a concise context for the DSPy client.
- This context informs ability/adversary creation with CTI-aware insights (e.g., attack patterns, tools, actors).

## MLFlow
- MLFlow is accessible on Caldera startup via http://localhost:5000
- Navigate in the MLflow UI to the traces section under the caldera client experiment grouping
