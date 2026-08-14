"""Abstract base class for all controlled investigation tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Union
from pydantic import BaseModel, ValidationError
from src.tools.schemas import ToolMetadata


class BaseTool(ABC):
    """Abstract base class establishing the contract for controlled investigation tools."""

    name: str
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]

    def get_metadata(self) -> ToolMetadata:
        """Return structured metadata and schema definitions for the tool."""
        return ToolMetadata(
            name=self.name,
            description=self.description,
            input_schema=self.input_model.model_json_schema(),
            output_schema=self.output_model.model_json_schema(),
        )

    def execute(self, input_data: Union[Dict[str, Any], BaseModel]) -> BaseModel:
        """Validate input payload, execute tool logic, and return structured output."""
        try:
            if isinstance(input_data, dict):
                validated_input = self.input_model.model_validate(input_data)
            elif isinstance(input_data, self.input_model):
                validated_input = input_data
            else:
                return self.output_model(
                    success=False,
                    error=f"Invalid input type: expected {self.input_model.__name__} or dict, got {type(input_data).__name__}",
                )
        except ValidationError as val_err:
            return self.output_model(
                success=False,
                error=f"Input validation error: {str(val_err)}",
            )
        except Exception as ex:
            return self.output_model(
                success=False,
                error=f"Unexpected input processing error: {str(ex)}",
            )

        try:
            return self._run(validated_input)
        except Exception as run_err:
            return self.output_model(
                success=False,
                error=f"Tool execution failure in '{self.name}': {str(run_err)}",
            )

    @abstractmethod
    def _run(self, validated_input: Any) -> BaseModel:
        """Internal execution method implemented by concrete tool classes."""
        pass
