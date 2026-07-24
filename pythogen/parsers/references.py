from dataclasses import dataclass
from typing import Any


@dataclass
class ResolvedRef:
    ref_data: Any
    ref_id: str


class RefResolver:
    """
    Отвечает за получение данных из указанного $ref пути.
    """

    def __init__(self, openapi_data: dict[str, Any]) -> None:
        self._openapi_data = openapi_data

    def _resolve_name_from_path(self, ref: str) -> str:
        from pythogen.parsers.operations import OperationParser

        _, path = ref.split("#/")
        _, endpoint_name, method, _, status_code, *_ = path.split("/")
        endpoint_name = endpoint_name.replace("~1", "/").replace("~0", "~")
        operation_id = OperationParser.parse_operation_id(ref, method, self._openapi_data["paths"][endpoint_name][method])

        return f"{operation_id}Response{status_code}"

    def resolve(self, ref: str) -> ResolvedRef:
        """
        Получить данные из указзаного $ref-пути

        Parameters
        ----------
        ref
            Путь до объекта. Пример: "#/components/schemas/PutObjectData"
        optional_name
            Название объекта, если необходимо
        """
        _, path = ref.split("#/")
        segments = path.split("/")
        target = self._openapi_data
        while segments:
            current = segments.pop(0).replace("~1", "/").replace("~0", "~")
            if current not in target:
                raise Exception(f'Unable to resolve "{ref}", document section "{current}" not found')
            target = target[current]
        ref_id = self._resolve_name_from_path(ref) if "paths" in ref else ref.split("/")[-1]
        return ResolvedRef(ref_data=target, ref_id=ref_id)
