"""Tool Registry for registering, discovering, and executing controlled tools."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from src.tools.base import BaseTool
from src.tools.document_tool import DocumentRetrievalTool
from src.tools.schemas import ToolMetadata
from src.tools.sql_tool import SQLInvestigationTool


class ToolRegistry:
    """Registry maintaining available controlled tools and metadata."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Expected BaseTool instance, got {type(tool).__name__}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a registered tool by its unique name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolMetadata]:
        """List metadata and schema descriptions for all registered tools."""
        return [tool.get_metadata() for tool in self._tools.values()]

    def list_tool_names(self) -> List[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())

    def execute(self, tool_name: str, input_data: Union[Dict[str, Any], BaseModel]) -> Any:
        """Execute a registered tool by name with input data.
        
        Raises KeyError if the tool is not registered.
        """
        tool = self.get(tool_name)
        if not tool:
            raise KeyError(
                f"Tool '{tool_name}' is not registered. Available tools: {self.list_tool_names()}"
            )
        return tool.execute(input_data)


def create_default_tool_registry(
    db_url: Optional[str] = None,
    doc_dir: Optional[Any] = None,
) -> ToolRegistry:
    """Factory creating a registry loaded with default investigation tools."""
    registry = ToolRegistry()
    registry.register(SQLInvestigationTool(db_url=db_url))
    registry.register(DocumentRetrievalTool(doc_dir=doc_dir))
    return registry
