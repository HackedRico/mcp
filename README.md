# Caldera-MCP

## Model Context Protocol for Caldera!

mcp_server.py contains code that wraps the current caldera API into an accessible 
format for LLMs.

## Install

In python virtualenv | requires specific version of dspy
```
pip install dspy[mcp] 
```

## DEMOS

### Caldera Director | screen-capture(1).webm
mcp_client.py showcases an LLM acting as a director over caldera abilities, adversaries,
and operations.  

Example Starting Prompt
```
Find some abilities that constitutes a stealer adversary which includes credential-access and exfiltration, then create an adversary with those abilities, then create an operation with the adversary
```

The large language model can inspect abilities, inspect adversaries, and create new ones on the spot.  After an acceptable adversary is identified or created it starts an operation with the specified new adversary.

### Caldera Ability Factory | screen-capture.webm
mcp_factory_client.py showcases an LLM acting as a Caldera ability developer, creating new abilities where needed on the spot.

Example Starting Prompt
```
I want to create a few abilities related to persistence with WMI for windows, then create an adversary with those abilities.  Please create more than one ability.
```

The LLM can perform all the actions in the previous demo, but likely will use the create_windows_ability, create_linux_ability, and create_command actions exported by the MCP server.
