"""
Validador de estruturas FHIR R4 para hemogramas.
Valida conformidade com o perfil da SES-GO.
"""
from typing import Any, Dict, List, Optional, Tuple

from src.core.config import settings
from src.core.logging import get_logger
from src.domain.models import LoincCode, ValidationError
from src.validators.cpf_validator import CPFValidator

logger = get_logger(__name__)


class FHIRValidator:
    """Validador de Bundle FHIR para hemogramas completos."""
    
    # Códigos LOINC obrigatórios para exames simples (24 itens)
    REQUIRED_LOINC_CODES = {
        LoincCode.HEMACEAS.value,
        LoincCode.HEMOGLOBINA.value,
        LoincCode.HEMATOCRITO.value,
        LoincCode.VCM.value,
        LoincCode.HCM.value,
        LoincCode.CHCM.value,
        LoincCode.RDW.value,
        LoincCode.LEUCOCITOS.value,
        LoincCode.PROMIELOCITOS.value,
        LoincCode.MIELOCITOS.value,
        LoincCode.METAMIELOCITOS.value,
        LoincCode.BASTONETES.value,
        LoincCode.SEGMENTADOS.value,
        LoincCode.MONOCITOS.value,
        LoincCode.EOSINOFILOS.value,
        LoincCode.BASOFILOS.value,
        LoincCode.LINFOCITOS.value,
        LoincCode.LINFOCITOS_ATIPICOS.value,
        LoincCode.PRO_LINFOCITOS.value,
        LoincCode.BLASTOS.value,
        LoincCode.PLAQUETAS.value,
        LoincCode.PLAQUETOCRITO.value,
        LoincCode.VPM.value,
        LoincCode.PDW.value,
    }
    
    def __init__(self):
        """Inicializa o validador FHIR."""
        self.errors: List[ValidationError] = []
        self.cpf_validator = CPFValidator()
    
    def validate_bundle_structure(self, bundle: Dict[str, Any]) -> bool:
        """
        Valida a estrutura básica do Bundle FHIR.
        
        Args:
            bundle: Dicionário representando o Bundle FHIR
        
        Returns:
            True se válido, False caso contrário
        """
        # Valida resourceType
        if bundle.get("resourceType") != "Bundle":
            self.errors.append(ValidationError(
                field="resourceType",
                expected="Bundle",
                received=str(bundle.get("resourceType", "null")),
                description="Tipo de recurso deve ser Bundle"
            ))
            return False
        
        # Valida meta.profile
        meta = bundle.get("meta", {})
        profiles = meta.get("profile", [])
        if not profiles or settings.fhir_profile_url not in profiles:
            self.errors.append(ValidationError(
                field="meta.profile",
                expected=settings.fhir_profile_url,
                received=str(profiles),
                description="Bundle deve conter o perfil da SES-GO"
            ))
            return False
        
        # Valida type
        if bundle.get("type") != "collection":
            self.errors.append(ValidationError(
                field="type",
                expected="collection",
                received=str(bundle.get("type", "null")),
                description="Tipo do Bundle deve ser 'collection'"
            ))
            return False
        
        # Valida presença de entries
        entries = bundle.get("entry", [])
        if not entries:
            self.errors.append(ValidationError(
                field="entry",
                expected="array com 25 elementos",
                received="array vazio",
                description="Bundle deve conter entries"
            ))
            return False
        
        return True
    
    def validate_composite_exam(self, resource: Dict[str, Any]) -> bool:
        """
        Valida o exame composto (CBC panel).
        
        Args:
            resource: Recurso Observation do exame composto
        
        Returns:
            True se válido, False caso contrário
        """
        # Valida código LOINC do exame composto
        code = resource.get("code", {})
        codings = code.get("coding", [])
        
        if not codings:
            self.errors.append(ValidationError(
                field="code.coding",
                expected="array com código LOINC",
                received="array vazio",
                description="Exame composto deve ter código LOINC"
            ))
            return False
        
        loinc_code = codings[0].get("code")
        if loinc_code != LoincCode.CBC_PANEL.value:
            self.errors.append(ValidationError(
                field="code.coding[0].code",
                expected=LoincCode.CBC_PANEL.value,
                received=str(loinc_code),
                description="Código LOINC do exame composto deve ser 58410-2 (CBC panel)"
            ))
            return False
        
        # Valida hasMember (deve ter 24 referências)
        has_member = resource.get("hasMember", [])
        if len(has_member) != settings.fhir_required_exams_count:
            self.errors.append(ValidationError(
                field="hasMember",
                expected=f"array com {settings.fhir_required_exams_count} elementos",
                received=f"array com {len(has_member)} elementos",
                description=f"Exame composto deve referenciar {settings.fhir_required_exams_count} exames simples"
            ))
            return False
        
        return True

    def validate_simple_exams(self, bundle: Dict[str, Any]) -> bool:
        """
        Valida os 24 exames simples obrigatórios.

        Args:
            bundle: Bundle FHIR completo

        Returns:
            True se válido, False caso contrário
        """
        entries = bundle.get("entry", [])
        found_loinc_codes = set()

        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Observation":
                continue

            # Extrai código LOINC
            code = resource.get("code", {})
            codings = code.get("coding", [])

            for coding in codings:
                if coding.get("system") == "http://loinc.org":
                    loinc_code = coding.get("code")
                    if loinc_code in self.REQUIRED_LOINC_CODES:
                        found_loinc_codes.add(loinc_code)

        # Verifica se todos os códigos obrigatórios foram encontrados
        missing_codes = self.REQUIRED_LOINC_CODES - found_loinc_codes
        if missing_codes:
            self.errors.append(ValidationError(
                field="entry[].resource.code.coding[].code",
                expected=f"24 códigos LOINC obrigatórios",
                received=f"{len(found_loinc_codes)} códigos encontrados",
                description=f"Códigos LOINC faltando: {', '.join(sorted(missing_codes))}"
            ))
            return False

        return True

    def validate_identifiers(self, bundle: Dict[str, Any]) -> bool:
        """
        Valida identificadores (CPF, CNES).

        Args:
            bundle: Bundle FHIR completo

        Returns:
            True se válido, False caso contrário
        """
        entries = bundle.get("entry", [])

        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Observation":
                continue

            # Valida CPF do paciente
            subject = resource.get("subject", {})
            identifier = subject.get("identifier", {})

            if identifier.get("system") == "https://fhir.saude.go.gov.br/sid/cpf":
                cpf = identifier.get("value", "")
                is_valid, error_msg = self.cpf_validator.validate(cpf)

                if not is_valid:
                    self.errors.append(ValidationError(
                        field="subject.identifier.value",
                        expected="CPF válido (11 dígitos com verificadores corretos)",
                        received=cpf,
                        description=f"CPF inválido: {error_msg}"
                    ))
                    return False

            # Valida CNES do laboratório
            performers = resource.get("performer", [])
            for performer in performers:
                if performer.get("id") == "laboratorio":
                    lab_identifier = performer.get("identifier", {})
                    if lab_identifier.get("system") == "https://fhir.saude.go.gov.br/sid/cnes":
                        cnes = lab_identifier.get("value", "")
                        if not cnes.isdigit() or len(cnes) != 7:
                            self.errors.append(ValidationError(
                                field="performer[laboratorio].identifier.value",
                                expected="CNES válido (7 dígitos)",
                                received=cnes,
                                description="CNES deve conter exatamente 7 dígitos numéricos"
                            ))
                            return False

        return True

    def validate_specimen(self, resource: Dict[str, Any]) -> bool:
        """
        Valida a amostra (Specimen) contida no exame.

        Args:
            resource: Recurso Observation

        Returns:
            True se válido, False caso contrário
        """
        # Valida referência para amostra
        specimen_ref = resource.get("specimen", {})
        reference = specimen_ref.get("reference")

        if not reference or not reference.startswith("#"):
            self.errors.append(ValidationError(
                field="specimen.reference",
                expected="#amostra (referência interna)",
                received=str(reference),
                description="Exame deve referenciar amostra contida"
            ))
            return False

        # Valida amostra em contained
        contained = resource.get("contained", [])
        specimen_found = False

        for item in contained:
            if item.get("resourceType") == "Specimen":
                specimen_found = True

                # Valida tipo da amostra (deve ser sangue - BLD)
                specimen_type = item.get("type", {})
                codings = specimen_type.get("coding", [])

                if codings:
                    code = codings[0].get("code")
                    if code != "BLD":
                        self.errors.append(ValidationError(
                            field="contained[Specimen].type.coding[0].code",
                            expected="BLD (sangue)",
                            received=str(code),
                            description="Tipo de amostra deve ser sangue (BLD)"
                        ))
                        return False

                # Valida data de coleta
                collection = item.get("collection", {})
                if not collection.get("collectedDateTime"):
                    self.errors.append(ValidationError(
                        field="contained[Specimen].collection.collectedDateTime",
                        expected="Data/hora de coleta (ISO 8601)",
                        received="null",
                        description="Amostra deve ter data de coleta"
                    ))
                    return False

        if not specimen_found:
            self.errors.append(ValidationError(
                field="contained",
                expected="Specimen resource",
                received="não encontrado",
                description="Exame deve conter amostra (Specimen) em contained[]"
            ))
            return False

        return True

    def validate(self, bundle: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Valida um Bundle FHIR completo.

        Args:
            bundle: Dicionário representando o Bundle FHIR

        Returns:
            Tupla (is_valid, errors)
        """
        self.errors = []

        # Validação 1: Estrutura do Bundle
        if not self.validate_bundle_structure(bundle):
            return False, self.errors

        # Validação 2: Exames simples (24 códigos LOINC)
        if not self.validate_simple_exams(bundle):
            return False, self.errors

        # Validação 3: Identificadores (CPF, CNES)
        if not self.validate_identifiers(bundle):
            return False, self.errors

        # Validação 4: Exame composto e amostra
        entries = bundle.get("entry", [])
        composite_found = False

        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") != "Observation":
                continue

            # Verifica se é exame composto
            code = resource.get("code", {})
            codings = code.get("coding", [])

            if codings and codings[0].get("code") == LoincCode.CBC_PANEL.value:
                composite_found = True
                if not self.validate_composite_exam(resource):
                    return False, self.errors

            # Valida amostra em todos os exames
            if not self.validate_specimen(resource):
                return False, self.errors

        if not composite_found:
            self.errors.append(ValidationError(
                field="entry[].resource",
                expected="Exame composto (LOINC 58410-2)",
                received="não encontrado",
                description="Bundle deve conter exame composto (CBC panel)"
            ))
            return False, self.errors

        logger.info("Bundle FHIR validado com sucesso",
                   total_entries=len(entries),
                   loinc_codes_found=len(self.REQUIRED_LOINC_CODES))

        return True, []
