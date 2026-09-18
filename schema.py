"""
Esquema de salida estructurada para la extracción de información
clínica cardiológica a partir de texto libre en castellano.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ExtraccionClinica(BaseModel):
    edad: Optional[int] = Field(None, description="Edad del paciente en años")
    sexo: Optional[str] = Field(None, description="'M', 'F' o null si no se especifica ni se deduce por concordancia gramatical")
    diagnostico_principal: Optional[str] = Field(
        None, description="Motivo de consulta o diagnóstico TAL COMO aparece en el texto. No infieras diagnósticos no escritos."
    )
    fevi_porcentaje: Optional[float] = Field(
        None, description="Fracción de eyección del ventrículo izquierdo, en %. Solo si el texto da un NÚMERO explícito; 'conservada'/'normal' sin número -> null."
    )
    medicacion: List[str] = Field(
        default_factory=list, description="Fármacos que el paciente toma ACTUALMENTE, sin dosis ni posología"
    )
    alergias: Optional[List[str]] = Field(
        None, description="Lista de alergias. null si el texto no menciona el tema en absoluto; [] si menciona explícitamente que no tiene"
    )


JSON_SCHEMA_DESCRIPTION = """
{
  "edad": int | null,
  "sexo": "M" | "F" | null,
  "diagnostico_principal": string | null,
  "fevi_porcentaje": float | null,
  "medicacion": [string, ...],
  "alergias": [string, ...] | null
}
""".strip()
