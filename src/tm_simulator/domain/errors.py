"""Excepciones y estructuras de error del dominio de configuración."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Representa un problema individual detectado durante la validación."""

    code: str
    path: str
    message: str

    def format(self) -> str:
        """Devuelve una representación legible y determinista del problema."""
        return f"[{self.code}] {self.path}: {self.message}"


class ConfigurationError(Exception):
    """Excepción base para cualquier fallo al cargar o validar una máquina."""


class YamlLoadError(ConfigurationError):
    """Error al intentar abrir o leer la fuente YAML desde disco."""

    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = Path(path)
        self.reason = reason
        super().__init__(f"No se pudo leer el archivo YAML '{self.path}': {reason}")


class YamlSyntaxError(ConfigurationError):
    """Error de sintaxis al analizar el documento YAML."""

    def __init__(
        self,
        problem: str,
        *,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        self.problem = problem
        self.line = line
        self.column = column
        location = ""
        if line is not None and column is not None:
            location = f" (línea {line}, columna {column})"
        elif line is not None:
            location = f" (línea {line})"
        super().__init__(f"Error de sintaxis YAML{location}: {problem}")


class MachineValidationError(ConfigurationError):
    """Excepción que agrupa uno o más problemas de validación estructural o semántica."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        copied_issues = tuple(issues)
        if not copied_issues:
            raise ValueError("MachineValidationError requiere al menos un ValidationIssue.")
        self._issues = copied_issues
        formatted = "\n".join(f"- {issue.format()}" for issue in copied_issues)
        super().__init__(
            f"La configuración de la Máquina de Turing contiene {len(copied_issues)} "
            f"error(es) de validación:\n{formatted}"
        )

    @property
    def issues(self) -> tuple[ValidationIssue, ...]:
        """Colección inmutable de problemas de validación encontrados."""
        return self._issues
