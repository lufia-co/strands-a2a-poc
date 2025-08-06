import inspect
from typing import Any, Dict, Optional, List, Union
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider


class AgentConfigManager:
    """
    Manages dynamic agent configuration from database or other sources.
    Handles varying parameter sets and provides intelligent defaults.
    """
    
    @staticmethod
    def get_agent_signature_params() -> Dict[str, Any]:
        """
        Extract the signature parameters of the Agent class constructor.
        This helps us understand what parameters are available.
        """
        sig = inspect.signature(Agent.__init__)
        params = {}
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            params[name] = {
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'annotation': param.annotation,
                'required': param.default == inspect.Parameter.empty
            }
        return params
    
    @staticmethod
    def load_agent_config_from_db(agent_id: str) -> Dict[str, Any]:
        """
        Load agent configuration from database.
        This is a placeholder - replace with your actual database logic.
        """
        # Example database configurations for different agents
        sample_configs = {
            "qa_agent": {
                "system_prompt": '''
                You are a Q&A bot. 
                Answer questions based on the provided context and available tools. 
                You can rely on A2A Client tool provider that manages multiple A2A agents and exposes synchronous tools to find an agent that can retrieve information 
                necessary to answer the question.

                You just need to call the tool forwarding the user input to the agents available to you.
                ''',
                "record_direct_tool_call": False,
                "model_config": {
                    "type": "bedrock",
                    "temperature": 0
                }
            },
            "simple_agent": {
                "system_prompt": "You are a helpful assistant.",
                "model_config": {
                    "type": "bedrock",
                    "temperature": 0.7
                }
            },
            "creative_agent": {
                "name": "creative-writer",
                "agent_id": "creative-writer",
                "description": "Creative Writing Agent",
                "system_prompt": "You are a creative writing assistant. Help users with storytelling, poetry, and creative content.",
                "record_direct_tool_call": True,
                "max_iterations": 10,
                "timeout": 30,
                "model_config": {
                    "type": "bedrock",
                    "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "temperature": 0.8
                }
            },
            "analytical_agent": {
                "name": "data-analyst",
                "description": "Data Analysis Agent",
                "system_prompt": "You are a data analysis expert. Help users analyze data, create reports, and provide insights.",
                "model_config": {
                    "type": "bedrock",
                    "temperature": 0.1
                },
                "tools_config": {
                    "a2a_client": {
                        "known_agent_urls": ["https://analytics-agent.example.com"]
                    }
                }
            }
        }
        
        # TODO: Replace with actual database query
        
        return sample_configs.get(agent_id, {})
    
    @staticmethod
    def create_model_from_config(model_config: Dict[str, Any]) -> Any:
        """
        Create a model instance based on configuration.
        Supports different model types and their specific parameters.
        """
        model_type = model_config.get("type", "bedrock")
        
        if model_type == "bedrock":
            # Extract bedrock-specific parameters
            bedrock_params = {}
            
            # Map configuration parameters to BedrockModel parameters
            param_mapping = {
                "model_id": "model_id",
                "temperature": "temperature",
                "max_tokens": "max_tokens",
                "top_p": "top_p",
                "top_k": "top_k",
                "stop_sequences": "stop_sequences"
            }
            
            for config_key, param_key in param_mapping.items():
                if config_key in model_config:
                    bedrock_params[param_key] = model_config[config_key]
            
            return BedrockModel(**bedrock_params)
        
        # Add other model types as needed
        elif model_type == "anthropic":
            # Example for Anthropic models
            # from strands.models.anthropic import AnthropicModel
            # anthropic_params = {}
            # if "api_key" in model_config:
            #     anthropic_params["api_key"] = model_config["api_key"]
            # if "temperature" in model_config:
            #     anthropic_params["temperature"] = model_config["temperature"]
            # return AnthropicModel(**anthropic_params)
            raise ValueError("Anthropic model support not implemented yet")
        
        elif model_type == "openai":
            # Example for OpenAI models
            # from strands.models.openai import OpenAIModel
            # openai_params = {}
            # if "api_key" in model_config:
            #     openai_params["api_key"] = model_config["api_key"]
            # if "temperature" in model_config:
            #     openai_params["temperature"] = model_config["temperature"]
            # return OpenAIModel(**openai_params)
            raise ValueError("OpenAI model support not implemented yet")
        
        raise ValueError(f"Unsupported model type: {model_type}")
    
    @staticmethod
    def create_tools_from_config(tools_config: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Create tools based on configuration.
        Supports different tool types and their specific parameters.
        """
        if not tools_config:
            return []
        
        tools = []
        
        # Handle A2A client tools
        if "a2a_client" in tools_config:
            a2a_config = tools_config["a2a_client"]
            known_urls = a2a_config.get("known_agent_urls", [])
            if known_urls:
                provider = A2AClientToolProvider(known_agent_urls=known_urls)
                tools.extend(provider.tools)
        
        # Handle MCP tools
        if "mcp_tools" in tools_config:
            # Example for MCP tools
            # from strands.tools.mcp import MCPClient
            # mcp_config = tools_config["mcp_tools"]
            # for mcp_tool_config in mcp_config:
            #     mcp_client = MCPClient(...)
            #     tools.extend(mcp_client.list_tools())
            pass
        
        # Handle custom tools
        if "custom_tools" in tools_config:
            # Example for custom tools
            # custom_config = tools_config["custom_tools"]
            # tools.extend(load_custom_tools(custom_config))
            pass
        
        # Add other tool types as needed
        # if "web_search" in tools_config:
        #     from strands.tools.web_search import WebSearchTool
        #     web_config = tools_config["web_search"]
        #     tools.append(WebSearchTool(**web_config))
        
        return tools
    
    @classmethod
    def create_agent_from_config(cls, agent_id: str, additional_tools: Optional[List[Any]] = None) -> Agent:
        """
        Create an Agent instance dynamically from database configuration.
        
        Args:
            agent_id: The ID of the agent to load from database
            additional_tools: Additional tools to include (e.g., from external providers)
        
        Returns:
            Configured Agent instance
            
        Raises:
            ValueError: If agent configuration is not found or agent creation fails
        """
        # Load configuration from database
        config = cls.load_agent_config_from_db(agent_id)
        
        if not config:
            raise ValueError(f"No configuration found for agent: {agent_id}")
        
        # Get available Agent parameters to ensure we only pass valid parameters
        agent_params = cls.get_agent_signature_params()
        
        # Prepare agent arguments
        agent_kwargs = {}
        
        # Handle model configuration (required for most agents)
        if "model_config" in config:
            agent_kwargs["model"] = cls.create_model_from_config(config["model_config"])
        
        # Handle tools configuration
        tools = []
        if "tools_config" in config:
            tools.extend(cls.create_tools_from_config(config["tools_config"]))
        
        # Add additional tools if provided
        if additional_tools:
            tools.extend(additional_tools)
        
        if tools:
            agent_kwargs["tools"] = tools
        
        # Map configuration keys to agent parameters
        # This mapping ensures flexibility in database schema vs Agent constructor
        config_to_param_mapping = {
            "system_prompt": "system_prompt",
            "name": "name",
            "agent_id": "agent_id", 
            "description": "description",
            "record_direct_tool_call": "record_direct_tool_call",
            "max_iterations": "max_iterations",
            "timeout": "timeout",
            "memory": "memory",
            "stream": "stream"
        }
        
        # Add parameters that exist in both config and agent signature
        for config_key, param_name in config_to_param_mapping.items():
            if config_key in config and param_name in agent_params:
                agent_kwargs[param_name] = config[config_key]
        
        # Remove None values and parameters not accepted by Agent constructor
        filtered_kwargs = {
            k: v for k, v in agent_kwargs.items() 
            if v is not None and k in agent_params
        }
        
        try:
            return Agent(**filtered_kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create agent {agent_id}: {str(e)}")
    
    @classmethod
    def list_available_agents(cls) -> List[str]:
        """
        List all available agent IDs from the configuration.
        In a real implementation, this would query the database.
        
        Returns:
            List of available agent IDs
        """
        # TODO: Replace with actual database query
        # return db.query("SELECT DISTINCT agent_id FROM agent_configs")
        
        # For now, return the sample agent IDs
        sample_configs = cls.load_agent_config_from_db("")  # Get all configs
        return list(sample_configs.keys()) if sample_configs else []
    
    @classmethod
    def get_agent_info(cls, agent_id: str) -> Dict[str, Any]:
        """
        Get basic information about an agent without creating it.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dictionary with agent information (name, description, etc.)
        """
        config = cls.load_agent_config_from_db(agent_id)
        if not config:
            raise ValueError(f"No configuration found for agent: {agent_id}")
        
        # Return basic info without sensitive data
        info = {
            "agent_id": agent_id,
            "name": config.get("name", agent_id),
            "description": config.get("description", "No description available"),
            "model_type": config.get("model_config", {}).get("type", "unknown"),
            "has_tools": bool(config.get("tools_config")),
            "system_prompt_preview": config.get("system_prompt", "")[:100] + "..." if len(config.get("system_prompt", "")) > 100 else config.get("system_prompt", "")
        }
        
        return info


class DynamicAgentFactory:
    """
    Factory class for creating and managing dynamic agents.
    Provides a higher-level interface for agent management.
    """
    
    def __init__(self):
        self.config_manager = AgentConfigManager()
        self.agent_cache: Dict[str, Agent] = {}
    
    def create_agent(self, agent_id: str, additional_tools: Optional[List[Any]] = None, force_recreate: bool = False) -> Agent:
        """
        Create or retrieve a cached agent instance.
        
        Args:
            agent_id: The ID of the agent to create
            additional_tools: Additional tools to include
            force_recreate: Whether to recreate the agent even if cached
            
        Returns:
            Agent instance
        """
        if not force_recreate and agent_id in self.agent_cache:
            return self.agent_cache[agent_id]
        
        agent = self.config_manager.create_agent_from_config(agent_id, additional_tools)
        self.agent_cache[agent_id] = agent
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get a cached agent instance.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Agent instance if cached, None otherwise
        """
        return self.agent_cache.get(agent_id)
    
    def list_cached_agents(self) -> List[str]:
        """
        List all currently cached agent IDs.
        
        Returns:
            List of cached agent IDs
        """
        return list(self.agent_cache.keys())
    
    def clear_cache(self, agent_id: Optional[str] = None) -> None:
        """
        Clear the agent cache.
        
        Args:
            agent_id: Specific agent ID to clear, or None to clear all
        """
        if agent_id:
            self.agent_cache.pop(agent_id, None)
        else:
            self.agent_cache.clear()
    
    def list_available_agents(self) -> List[str]:
        """
        List all available agent IDs from configuration.
        
        Returns:
            List of available agent IDs
        """
        return self.config_manager.list_available_agents()
    
    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """
        Get basic information about an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dictionary with agent information
        """
        return self.config_manager.get_agent_info(agent_id)


# Example usage
if __name__ == "__main__":
    # Initialize the factory
    factory = DynamicAgentFactory()
    
    # List available agents
    print("Available agents:", factory.list_available_agents())
    
    # Get agent info
    try:
        qa_info = factory.get_agent_info("qa_agent")
        print("QA Agent info:", qa_info)
    except ValueError as e:
        print(f"Error: {e}")
    
    # Create an agent
    try:
        qa_agent = factory.create_agent("qa_agent")
        print(f"Created agent: {qa_agent}")
        
        # Create another agent with different configuration
        simple_agent = factory.create_agent("simple_agent")
        print(f"Created simple agent: {simple_agent}")
        
    except ValueError as e:
        print(f"Error creating agent: {e}")
