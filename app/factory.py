import dspy
import yaml

with open("/home/kali/coding/caldera/plugins/mcp/conf/default.yml", 'r') as file:
    config = yaml.safe_load(file)
    lm = dspy.LM(config['factory']['model'], api_key=config['factory']['api_key'], temperature=config['factory']['temperature'])
    dspy.configure(lm=lm)

#lm = dspy.LM(model="gpt-4o", api_key="***REDACTED-OPENAI-KEY***")
#dspy.configure(lm=lm)

class RankApproaches(dspy.Signature):
    """Rank the approaches to create the command."""

    description: str = dspy.InputField()
    technologies: list[str] = dspy.InputField()
    approaches: list[str] = dspy.OutputField()

class IdentifyTechnologies(dspy.Signature):
    """
    Identify the technologies that are relevant to the command.
    For windows, the basic shell interpreter is powershell.exe.
    For linux, the basic shell interpreter is bash.
    """
    
    description: str = dspy.InputField()
    platform: str = dspy.InputField()
    technologies: list[str] = dspy.OutputField()

class CreateFullCommand(dspy.Signature):
    """Create the full command. Only produce the command, do not give reasoning or comments.  Do not wrap the response in any tags."""
    technologies: list[str] = dspy.InputField()
    approaches: list[str] = dspy.InputField()
    command: str = dspy.OutputField()

class CreateCommand(dspy.Module):
    def __init__(self):
        self.identify_technologies = dspy.ChainOfThought(IdentifyTechnologies)
        self.rank_approaches = dspy.ChainOfThought(RankApproaches)
        self.create_full_command = dspy.ChainOfThought(CreateFullCommand)
        #self.log = logging.getLogger("plugins.mcp")
        #self.log.info("[MCP] Initialized CreateCommand Module")

    def forward(self, description: str, platform: str):
        identified_technologies = self.identify_technologies(description=description, platform=platform)
        ranked_approaches = self.rank_approaches(description=description, technologies=identified_technologies)
        full_command = self.create_full_command(technologies=identified_technologies, approaches=ranked_approaches)
        return full_command.command
        
