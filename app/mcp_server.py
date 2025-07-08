from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import requests
from datetime import datetime
import time
import collections
import uuid

from factory import CreateCommand


mcp = FastMCP("Caldera API MCP Server", version="1.0.0")

"""
total_requests data structure:
{
    "endpoint": {
        
        [
            "time_date": "response_code", 
        ]
    }
}
dict[key] = list[dict[str, str]]
"""


class CalderaRequest:
    def __init__(self, url, api_key):
        self.caldera_url = url
        self.api_key = api_key
        self.headers = {"KEY": f"{self.api_key}", "Content-Type": "application/json"}
        self.total_get_requests = collections.defaultdict(list)
        self.total_post_requests = collections.defaultdict(list)

    def make_get_request(self, endpoint):
        response = requests.get(f"{self.caldera_url}{endpoint}", headers=self.headers)
        self.total_get_requests[endpoint].append(
            {
                "time_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "response_code": response.status_code,
            }
        )
        if response.status_code != 200:
            return {"error": f"Request did not return 200. Error: {response.text}"}
        return response.json()

    def make_post_request(self, endpoint, body):
        response = requests.post(
            f"{self.caldera_url}{endpoint}", headers=self.headers, json=body
        )
        self.total_post_requests[endpoint].append(
            {
                "time_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "response_code": response.status_code,
            }
        )
        if response.status_code != 200:
            return {"error": f"Request did not return 200. Error: {response.text}"}
        return response.json()


# caldera_request = CalderaRequest(
#     url="http://localhost:8888/api/v2/",
#     api_key="ADMIN123",
# )


async def get_service_summary(services):
    """
    Return a summary of available core services.
    """
    return {k: str(v.__class__.__name__) for k, v in services.items() if v is not None}


@mcp.tool()
# def health_check():
#     """
#     Returns the health of the Caldera API.
#     """
#     if isinstance(caldera_request.make_get_request("health"), dict):
#         return "Caldera API is UP!"
async def health_check(services):
    """
    Perform a basic health check by pinging core services.
    """
    try:
        data_svc = services.get('data_svc')
        agents = await data_svc.locate('agents')
        return "Caldera API is UP!" if agents is not None else "Caldera API check failed."
    except Exception as e:
        return f"Caldera API is DOWN: {str(e)}"


def filter_abilities(req, tactic: str, atomic: bool):
    stockpile_abilities = []
    if atomic == True:
        atomic_abilities = [item for item in req if item.get("plugin") == "atomic"]
        tactic_abilities = [
            item for item in atomic_abilities if item.get("tactic") == tactic
        ]
        for ability in tactic_abilities:
            ability_stripped = {}
            ability_stripped["ability_id"] = ability["ability_id"]
            ability_stripped["name"] = ability["name"]
            ability_stripped["tactic"] = ability["tactic"]
            ability_stripped["technique"] = ability["technique_name"]
            stockpile_abilities.append(ability_stripped)
    else:
        stockpile_only = [item for item in req if item.get("plugin") == "stockpile"]
        tactic_abilities = [
            item for item in stockpile_only if item.get("tactic") == tactic
        ]
        for ability in tactic_abilities:
            ability_stripped = {}
            ability_stripped["ability_id"] = ability["ability_id"]
            ability_stripped["name"] = ability["name"]
            ability_stripped["tactic"] = ability["tactic"]
            ability_stripped["technique"] = ability["technique_name"]
            stockpile_abilities.append(ability_stripped)
    return stockpile_abilities or []


@mcp.tool()
# def get_abilities_by_tactic(tactic: str):
#     """
#     Returns the stockpile abilities of Caldera specified by the tactic.
#     Possible Tactic Values:
#     - persistence
#     - privilege-escalation
#     - lateral-movement
#     - collection
#     - execution
#     - command-and-control
#     - credential-access
#     - discovery
#     - defense-evasion
#     """
#     # req = caldera_request.make_get_request("abilities")
#     # stockpile_abilities = filter_abilities(req, tactic, atomic=False)
#     # print(f"Stockpile Abilities: {stockpile_abilities}")
#     # if stockpile_abilities:
#     #     return stockpile_abilities
#     # else:
#     #     stockpile_abilities = filter_abilities(req, tactic, atomic=True)
#     #     print(f"Stockpile Abilities: {stockpile_abilities}")
#     #     if len(stockpile_abilities) > 5:
#     #         return stockpile_abilities[:5]
@mcp.tool()
async def get_abilities_by_tactic(services: dict, tactic: str):
    """
    Returns stockpile or atomic abilities filtered by tactic.
    """
    data_svc = services.get('data_svc')
    all_abilities = await data_svc.locate('abilities')

    def filter_abilities(abilities, tactic, plugin_name):
        return [
            {
                "ability_id": a.ability_id,
                "name": a.name,
                "tactic": a.tactic,
                "technique": a.technique_name
            }
            for a in abilities
            if a.tactic == tactic and a.plugin == plugin_name
        ]

    stockpile_abilities = filter_abilities(all_abilities, tactic, 'stockpile')
    if stockpile_abilities:
        return stockpile_abilities
    atomic_abilities = filter_abilities(all_abilities, tactic, 'atomic')
    return atomic_abilities[:5] if len(atomic_abilities) > 5 else atomic_abilities

    


@mcp.tool()
# def get_ability_by_id(id: str):
#     """
#     Returns the ability of the Caldera API specified by the id.
#     """
#     return caldera_request.make_get_request(f"abilities/{id}")
async def get_ability_by_id(services, ability_id: str):
    data_svc = services.get('data_svc')
    results = await data_svc.locate('abilities', match=dict(ability_id=ability_id))
    return results[0].display if results else {}


@mcp.tool()
# def get_adversaries():
#     """
#     Returns all Caldera adversaries.
#     """
#     req = caldera_request.make_get_request("adversaries")
#     adversary_list = []
#     for adversary in req:
#         adversary_stripped = {}
#         adversary_stripped["adversary_id"] = adversary["adversary_id"]
#         adversary_stripped["name"] = adversary["name"]
#         adversary_stripped["description"] = adversary["description"]
#         adversary_list.append(adversary_stripped)
#     return adversary_list
async def get_adversaries(services):
    data_svc = services.get('data_svc')
    all_adversaries = await data_svc.locate('adversaries')
    return [
        {
            "adversary_id": adv.adversary_id,
            "name": adv.name,
            "description": adv.description
        }
        for adv in all_adversaries
    ]


@mcp.tool()
# def get_adversary_by_ability_id(ability_id: str, ability_name: str = None):
#     """
#     Filters all Caldera adversaries by the specifies ability id or ability name.
#     """
#     req = caldera_request.make_get_request("adversaries")
#     adversary_list = []

#     abilities = caldera_request.make_get_request("abilities")
#     if ability_name:
#         named_abilities = [
#             item for item in abilities
#             if item.get("name") == ability_name
#         ]
#         ability_id = None
#         if named_abilities:
#             ability_id = named_abilities[0]["ability_id"]
#             for adversary in req:
#                 for key, value in adversary.items():
#                     if key == "atomic_ordering":
#                         for atomic_ordering in value:
#                             if atomic_ordering == id:
#                                 adversary_stripped = {}
#                                 adversary_stripped["adversary_id"] = adversary["adversary_id"]
#                                 adversary_stripped["name"] = adversary["name"]
#                                 adversary_stripped["description"] = adversary["description"]
#                                 adversary_list.append(adversary_stripped)
#     elif ability_id:
#         for adversary in req:
#             for key, value in adversary.items():
#                 if key == "atomic_ordering":
#                     for atomic_ordering in value:
#                         if atomic_ordering == ability_id:
#                             adversary_stripped = {}
#                             adversary_stripped["adversary_id"] = adversary["adversary_id"]
#                             adversary_stripped["name"] = adversary["name"]
#                             adversary_stripped["description"] = adversary["description"]
#                             adversary_list.append(adversary_stripped)
#     return adversary_list


# async def get_adversary_by_id(services, adversary_id: str):
#     data_svc = services.get('data_svc')
#     matches = await data_svc.locate('adversaries', match=dict(adversary_id=adversary_id))
#     return matches[0].display if matches else {}
async def get_adversary_by_id(services, adversary_id: str):
    data_svc = services.get('data_svc')
    matches = await data_svc.locate('adversaries', match=dict(adversary_id=adversary_id))
    return matches[0].display if matches else {}



@mcp.tool()
# def get_adversary_by_name(name: str):
#     """
#     Returns the Caldera adversary specified by the name.
#     """
#     req = caldera_request.make_get_request("adversaries")
#     found_adversaries = []
#     for adversary in req:
#         if adversary["name"] == name:
#             found_adversaries.append(adversary)
#     return found_adversaries
async def get_adversary_by_name(services, name: str):
    data_svc = services.get('data_svc')
    matches = await data_svc.locate('adversaries', match=dict(name=name))
    return [m.display for m in matches]


@mcp.tool()
# def get_adversary_id(id: str):
#     """
#     Returns the Caldera adversary specified by the id.
#     """
#     req = caldera_request.make_get_request(f"adversaries/{id}")
#     adversary_stripped = {}
#     adversary_stripped["adversary_id"] = req["adversary_id"]
#     adversary_stripped["name"] = req["name"]
#     adversary_stripped["description"] = req["description"]
#     return adversary_stripped
@mcp.tool()
async def get_adversary_id(services, id: str):
    """
    Returns the Caldera adversary specified by the ID,
    including adversary_id, name, and description.
    """
    data_svc = services.get('data_svc')
    adversary = await data_svc.get('adversary', id)
    if not adversary:
        return {"error": f"Adversary with ID {id} not found"}

    return {
        "adversary_id": adversary.adversary_id,
        "name": adversary.name,
        "description": adversary.description
    }


@mcp.tool()
# def get_all_agents():
#     """
#     Returns all active and dead agents.
#     """

#     return caldera_request.make_get_request("agents")
async def get_all_agents(services):
    data_svc = services.get('data_svc')
    agents = await data_svc.locate('agents')
    return [a.display for a in agents]


@mcp.tool()
# def get_agent_by_paw(paw: str):
#     """
#     Returns the agent of the Caldera API specified by the paw.
#     """

#     return caldera_request.make_get_request(f"agents/{paw}")
async def get_agent_by_paw(services, paw: str):
    data_svc = services.get('data_svc')
    matches = await data_svc.locate('agents', match=dict(paw=paw))
    return matches[0].display if matches else {}


@mcp.tool()
# def get_all_operations():
#     """
#     Returns all active and dead operations.
#     """

#     return caldera_request.make_get_request("operations")
async def get_all_operations(services):
    data_svc = services.get('data_svc')
    operations = await data_svc.locate('operations')
    return [op.display for op in operations]


@mcp.tool()
# def get_operation_by_id(id: str):
#     """
#     Return operation by specified id.
#     """

#     return caldera_request.make_get_request(f"operations/{id}")
async def get_operation_by_id(services, operation_id: str):
    data_svc = services.get('data_svc')
    matches = await data_svc.locate('operations', match=dict(id=operation_id))
    return matches[0].display if matches else {}


@mcp.tool()
# def get_operation_links(operation_id: str):
#     """
#     Specify an operation id to get the links of the operation.
#     """

#     return caldera_request.make_get_request(f"operations/{operation_id}/links")
async def get_operation_links(services, operation_id: str):
    data_svc = services.get('data_svc')
    matches = await data_svc.locate('operations', match=dict(id=operation_id))
    if not matches:
        return []
    op = matches[0]
    return [link.display for link in op.chain]


@mcp.tool()
# def get_operation_link(operation_id: str, link_id: str):
#     """
#     Specify an operation id and link id to get the specific link of the specific operation.
#     """

#     return caldera_request.make_get_request(
#         f"operations/{operation_id}/links/{link_id}"
#     )
async def get_operation_link(services, operation_id: str, link_id: str):
    data_svc = services.get('data_svc')
    matches = await data_svc.locate('operations', match=dict(id=operation_id))
    if not matches:
        return {}
    op = matches[0]
    for link in op.chain:
        if str(link.id) == link_id:
            return link.display
    return {}


@mcp.tool()
# def get_operation_link_result(operation_id: str, link_id: str):
#     """
#     Specify an operation id and link id to get the result of the specific link of the specific operation.
#     """

#     return caldera_request.make_get_request(
#         f"operations/{operation_id}/links/{link_id}/result"
#     )
async def get_operation_link_result(services, operation_id: str, link_id: str):
    data_svc = services.get('data_svc')
    matches = await data_svc.locate('operations', match=dict(id=operation_id))
    if not matches:
        return {}
    op = matches[0]
    for link in op.chain:
        if str(link.id) == link_id:
            return {"output": link.output or ""}
    return {}


@mcp.tool()
# def add_link_to_operation(
#     operation_id: str, ability_id: str, ability_executor: str, paw: str
# ):
#     """
#     Add an ability to an existing operation by specifying the operation id, ability id, ability executor, and paw.
#     """
#     return caldera_request.make_post_request(
#         f"operations/{operation_id}/links",
#         {"ability_id": ability_id, "ability_executor": ability_executor, "paw": paw},
#     )
async def add_link_to_operation(services, operation_id: str, ability_id: str, ability_executor: str, paw: str):
    rest_svc = services.get('rest_svc')
    return await rest_svc.add_link_to_operation(
        operation_id=operation_id,
        ability_id=ability_id,
        paw=paw,
        executor=ability_executor
    )


@mcp.tool()
# def create_adversary(name: str, description: str, atomic_ordering: list):
#     """
#     Create a new adversary, specify a name, description, and atomic ordering.
#     Atomic ordering is a list of ability ids that are used to order the abilities of the adversary.
#     Example:
#     "665432a4-42e7-4ee1-af19-a9a8c9455d0c",
#     "95ad5d69-563e-477b-802b-4855bfb3be09",
#     "e99cce5c-cb7e-4a6e-8a09-1609a221b90a",
#     "e3db134c-4aed-4c5a-9607-c50183c9ef9e"
#     """
#     adversary_id = str(uuid.uuid4())

#     return caldera_request.make_post_request(
#         f"adversaries",
#         {
#             "adversary_id": adversary_id,
#             "name": name,
#             "description": description,
#             "atomic_ordering": atomic_ordering,
#         },
#     )
async def create_adversary(services, name: str, description: str, atomic_ordering: list):
    data_svc = services.get('data_svc')
    adversary_id = str(uuid4())
    new_adv = await data_svc.create_adversary(
        adversary_id=adversary_id,
        name=name,
        description=description,
        atomic_ordering=atomic_ordering
    )
    return new_adv.display


@mcp.tool()
# def create_operation(operation_name: str, adversary_name: str):
#     """
#     Create a new operation with the specified name and adversary.

#     Args:
#         operation_name: Name for the operation
#         adversary_id: ID of the adversary to use for this operation

#     Returns:
#         The response from the Caldera API or None if adversary details cannot be fetched
#     """
#     req = caldera_request.make_get_request("adversaries")
#     found_adversaries = []
#     for adversary in req:
#         if adversary["name"] == adversary_name:
#             found_adversaries.append(adversary)

#     adversary_details = found_adversaries[0]

#     operation_body = {
#         "name": operation_name,
#         "adversary": {
#             **{
#                 k: adversary_details.get(k, "")
#                 for k in [
#                     "adversary_id",
#                     "name",
#                     "description",
#                     "atomic_ordering",
#                     "tags",
#                     "plugin",
#                 ]
#             },
#             "objective": "495a9828-cab1-44dd-a0ca-66e58177d8cc",
#         },
#         "planner_id": "aaa7c857-37a0-4c4a-85f7-4e9f7f30e31a",
#         "source_id": "ed32b9c3-9593-4c33-b0db-e2007315096b",
#         "objective_id": "495a9828-cab1-44dd-a0ca-66e58177d8cc",
#         "state": "paused",
#         "autonomous": 1,
#         "auto_close": False,
#         "obfuscator": "plain-text",
#         "jitter": "2/4",
#         "visibility": 51,
#         "use_learning_parsers": True,
#         "group": "",
#     }

#     return caldera_request.make_post_request("operations", operation_body)
async def create_operation(services, operation_name: str, adversary_name: str):
    data_svc = services.get('data_svc')
    adversaries = await data_svc.locate('adversaries', match=dict(name=adversary_name))
    if not adversaries:
        return {"error": "Adversary not found"}

    adversary = adversaries[0]
    op_data = {
        'name': operation_name,
        'adversary_id': adversary.adversary_id,
        'group': '',
        'objective_id': '495a9828-cab1-44dd-a0ca-66e58177d8cc',
        'planner_id': 'aaa7c857-37a0-4c4a-85f7-4e9f7f30e31a',
        'source_id': 'ed32b9c3-9593-4c33-b0db-e2007315096b',
        'state': 'paused',
        'autonomous': 1,
        'auto_close': False,
        'obfuscator': 'plain-text',
        'jitter': '2/4',
        'visibility': 51,
        'use_learning_parsers': True
    }
    new_op = await data_svc.create_operation(**op_data)
    return new_op.display


@mcp.tool()
# def create_command(description: str, platform: str):
#     """
#     create a command by specifying a description of the command(what it does and how it works) and the platform it is for (windows or linux).
#     """

#     create_command = CreateCommand()
#     return create_command(description=description, platform=platform)
async def create_command(description: str, platform: str):
    """
    Create a command using the CreateCommand factory.
    """
    create_command_factory = CreateCommand()
    return await create_command_factory(description=description, platform=platform)


@mcp.tool()
# def create_windows_ability(
#     name: str,
#     description: str,
#     command: str,
#     tactic: str,
#     technique_name: str,
#     technique_id: str = None,
#     payloads: list = None,
# ):
#     """
#     Create a new windows ability with the specified parameters.

#     Args:
#         name: Name of the ability
#         description: Description of what the ability does
#         command: The command to execute
#         tactic: MITRE ATT&CK tactic (e.g., 'privilege-escalation', 'discovery')
#         technique_name: Name of the MITRE ATT&CK technique
#         technique_id: Optional MITRE ATT&CK technique ID (e.g., 'T1548.002')
#         payloads: Optional list of payload files needed

#     Returns:
#         The response from the Caldera API
#     """
#     ability_id = str(uuid.uuid4())

#     # Create the executor object with default values for optional fields
#     executor = {
#         "name": "windows",
#         "platform": "psh",
#         "command": command,
#         "code": None,
#         "language": None,
#         "build_target": None,
#         "payloads": payloads or [],
#         "uploads": [],
#         "timeout": 60,
#         "parsers": [],
#         "cleanup": [],
#         "variations": [],
#         "additional_info": {},
#     }

#     ability_body = {
#         "ability_id": ability_id,
#         "tactic": tactic,
#         "technique_name": technique_name,
#         "technique_id": technique_id,
#         "name": name,
#         "description": description,
#         "executors": [executor],
#         "requirements": [],
#         "privilege": "",
#         "repeatable": False,
#         "buckets": [tactic],
#         "additional_info": {},
#         "access": {},
#         "singleton": False,
#         "plugin": "stockpile",
#         "delete_payload": True,
#     }

#     return caldera_request.make_post_request("abilities", ability_body)
async def create_windows_ability(
    services, name: str, description: str, command: str, tactic: str,
    technique_name: str, technique_id: str = None, payloads: list = None
):
    data_svc = services.get('data_svc')
    ability_id = str(uuid4())

    executor = {
        "name": "psh",
        "platform": "windows",
        "command": command,
        "timeout": 60,
        "payloads": payloads or [],
        "uploads": [],
        "parsers": [],
        "cleanup": [],
        "variations": [],
        "additional_info": {}
    }

    new_ability = await data_svc.create_ability(
        ability_id=ability_id,
        tactic=tactic,
        technique_name=technique_name,
        technique_id=technique_id,
        name=name,
        description=description,
        executors=[executor],
        plugin='stockpile',
        buckets=[tactic],
        delete_payload=True
    )
    return new_ability.display


@mcp.tool()
# def create_linux_ability(
#     name: str,
#     description: str,
#     command: str,
#     tactic: str,
#     technique_name: str,
#     technique_id: str = None,
#     payloads: list = None,
# ):
#     """
#     Create a new ability for linux with the specified parameters.

#     Args:
#         name: Name of the ability
#         description: Description of what the ability does
#         command: The command to execute
#         tactic: MITRE ATT&CK tactic (e.g., 'privilege-escalation', 'discovery')
#         technique_name: Name of the MITRE ATT&CK technique
#         technique_id: Optional MITRE ATT&CK technique ID (e.g., 'T1548.002')
#         payloads: Optional list of payload files needed

#     Returns:
#         The response from the Caldera API
#     """
#     ability_id = str(uuid.uuid4())

#     # Create the executor object with default values for optional fields
#     executor = {
#         "name": "linux",
#         "platform": "sh",
#         "command": command,
#         "code": None,
#         "language": None,
#         "build_target": None,
#         "payloads": payloads or [],
#         "uploads": [],
#         "timeout": 60,
#         "parsers": [],
#         "cleanup": [],
#         "variations": [],
#         "additional_info": {},
#     }

#     ability_body = {
#         "ability_id": ability_id,
#         "tactic": tactic,
#         "technique_name": technique_name,
#         "technique_id": technique_id,
#         "name": name,
#         "description": description,
#         "executors": [executor],
#         "requirements": [],
#         "privilege": "",
#         "repeatable": False,
#         "buckets": [tactic],
#         "additional_info": {},
#         "access": {},
#         "singleton": False,
#         "plugin": "stockpile",
#         "delete_payload": True,
#     }

#     return caldera_request.make_post_request("abilities", ability_body)
async def create_linux_ability(
    services, name: str, description: str, command: str, tactic: str,
    technique_name: str, technique_id: str = None, payloads: list = None
):
    data_svc = services.get('data_svc')
    ability_id = str(uuid4())

    executor = {
        "name": "sh",
        "platform": "linux",
        "command": command,
        "timeout": 60,
        "payloads": payloads or [],
        "uploads": [],
        "parsers": [],
        "cleanup": [],
        "variations": [],
        "additional_info": {}
    }

    new_ability = await data_svc.create_ability(
        ability_id=ability_id,
        tactic=tactic,
        technique_name=technique_name,
        technique_id=technique_id,
        name=name,
        description=description,
        executors=[executor],
        plugin='stockpile',
        buckets=[tactic],
        delete_payload=True
    )
    return new_ability.display


@mcp.tool()
# def get_payloads():
#     """
#     Returns all payloads.
#     """
#     return caldera_request.make_get_request("payloads")
async def get_payloads(services):
    data_svc = services.get('data_svc')
    payloads = await data_svc.locate('payloads')
    return [p.display for p in payloads]


if __name__ == "__main__":
    mcp.run()
