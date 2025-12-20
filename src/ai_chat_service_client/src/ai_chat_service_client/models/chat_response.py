from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.chat_response_response_type_1 import ChatResponseResponseType1


T = TypeVar("T", bound="ChatResponse")


@_attrs_define
class ChatResponse:
    """Standardized chat response mirroring ai_chat_api output.

    Attributes:
        response (ChatResponseResponseType1 | str):

    """

    response: ChatResponseResponseType1 | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.chat_response_response_type_1 import ChatResponseResponseType1

        response: dict[str, Any] | str
        if isinstance(self.response, ChatResponseResponseType1):
            response = self.response.to_dict()
        else:
            response = self.response

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "response": response,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.chat_response_response_type_1 import ChatResponseResponseType1

        d = dict(src_dict)

        def _parse_response(data: object) -> ChatResponseResponseType1 | str:
            try:
                if not isinstance(data, dict):
                    raise TypeError
                response_type_1 = ChatResponseResponseType1.from_dict(data)

                return response_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast("ChatResponseResponseType1 | str", data)

        response = _parse_response(d.pop("response"))

        chat_response = cls(
            response=response,
        )

        chat_response.additional_properties = d
        return chat_response

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
