from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ai_structured_response_parameters import AIStructuredResponseParameters


T = TypeVar("T", bound="AIStructuredResponse")


@_attrs_define
class AIStructuredResponse:
    """Structured AI response capturing an action intent and its parameters.

    Attributes:
        intent (str):
        parameters (Union[Unset, AIStructuredResponseParameters]):
    """

    intent: str
    parameters: Union[Unset, "AIStructuredResponseParameters"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        intent = self.intent

        parameters: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "intent": intent,
            }
        )
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ai_structured_response_parameters import AIStructuredResponseParameters

        d = dict(src_dict)
        intent = d.pop("intent")

        _parameters = d.pop("parameters", UNSET)
        parameters: Union[Unset, AIStructuredResponseParameters]
        if isinstance(_parameters, Unset):
            parameters = UNSET
        else:
            parameters = AIStructuredResponseParameters.from_dict(_parameters)

        ai_structured_response = cls(
            intent=intent,
            parameters=parameters,
        )

        ai_structured_response.additional_properties = d
        return ai_structured_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
