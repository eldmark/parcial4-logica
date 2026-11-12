"""Carga segura de documentos YAML desde archivo o texto en memoria."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
import yaml.constructor

from tm_simulator.domain.errors import (
    MachineValidationError,
    ValidationIssue,
    YamlLoadError,
    YamlSyntaxError,
)


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """SafeLoader que rechaza claves duplicadas dentro de un mismo mapeo YAML."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
            seen_keys: set[Any] = set()
            for key_node, _ in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    is_duplicate = key in seen_keys
                except TypeError:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        "found unhashable key",
                        key_node.start_mark,
                    ) from None
                if is_duplicate:
                    raise yaml.constructor.ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        f"clave YAML duplicada {key!r}",
                        key_node.start_mark,
                    )
                seen_keys.add(key)
        return super().construct_mapping(node, deep=deep)


def load_raw_yaml_from_file(path: str | Path) -> dict[str, Any]:
    """Lee un archivo YAML codificado en UTF-8 y devuelve el mapeo raíz sin procesar."""
    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise YamlLoadError(file_path, "El archivo no existe.") from None
    except IsADirectoryError:
        raise YamlLoadError(
            file_path, "La ruta corresponde a un directorio, no a un archivo."
        ) from None
    except PermissionError:
        if file_path.is_dir():
            raise YamlLoadError(
                file_path, "La ruta corresponde a un directorio, no a un archivo."
            ) from None
        raise YamlLoadError(file_path, "Permisos insuficientes para leer el archivo.") from None
    except UnicodeDecodeError as exc:
        raise YamlLoadError(
            file_path,
            f"El archivo no tiene una codificación UTF-8 válida ({exc.reason}).",
        ) from None
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise YamlLoadError(file_path, reason) from None

    return load_raw_yaml_from_text(content)


def load_raw_yaml_from_text(content: str) -> dict[str, Any]:
    """Analiza de forma segura un texto YAML y verifica que su raíz sea un mapeo no vacío."""
    if not content.strip():
        parsed: Any = None
    else:
        try:
            parsed = yaml.load(content, Loader=_UniqueKeySafeLoader)
        except yaml.MarkedYAMLError as exc:
            mark = exc.problem_mark
            line = mark.line + 1 if mark is not None else None
            column = mark.column + 1 if mark is not None else None
            problem = exc.problem or "Estructura YAML inválida."
            raise YamlSyntaxError(problem, line=line, column=column) from None
        except yaml.YAMLError as exc:
            raise YamlSyntaxError(str(exc) or "Estructura YAML inválida.") from None

    if parsed is None:
        raise MachineValidationError(
            [
                ValidationIssue(
                    code="empty_document",
                    path="root",
                    message="El documento YAML está vacío.",
                )
            ]
        )

    if not isinstance(parsed, Mapping):
        raise MachineValidationError(
            [
                ValidationIssue(
                    code="invalid_root_type",
                    path="root",
                    message="La raíz del documento YAML debe ser un mapeo (diccionario).",
                )
            ]
        )

    if any(not isinstance(key, str) for key in parsed):
        raise MachineValidationError(
            [
                ValidationIssue(
                    code="invalid_root_key_type",
                    path="root",
                    message=(
                        "Todas las claves de la raíz del documento YAML deben ser cadenas de texto."
                    ),
                )
            ]
        )

    return dict(parsed)
