"""
Validador de CPF (Cadastro de Pessoa Física).
Implementa o algoritmo de validação de dígitos verificadores do CPF brasileiro.
"""
from typing import Optional


class CPFValidator:
    """Validador de CPF com verificação de dígitos verificadores."""
    
    # CPFs inválidos conhecidos (todos os dígitos iguais)
    INVALID_CPFS = {
        "00000000000", "11111111111", "22222222222", "33333333333",
        "44444444444", "55555555555", "66666666666", "77777777777",
        "88888888888", "99999999999"
    }
    
    @staticmethod
    def clean_cpf(cpf: str) -> str:
        """
        Remove caracteres não numéricos do CPF.
        
        Args:
            cpf: CPF com ou sem formatação
        
        Returns:
            CPF apenas com dígitos
        """
        return ''.join(filter(str.isdigit, cpf))
    
    @staticmethod
    def calculate_digit(cpf_partial: str, weights: list[int]) -> int:
        """
        Calcula um dígito verificador do CPF.
        
        Args:
            cpf_partial: Parte do CPF para calcular o dígito
            weights: Pesos para o cálculo
        
        Returns:
            Dígito verificador calculado
        """
        total = sum(int(digit) * weight for digit, weight in zip(cpf_partial, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    @classmethod
    def validate(cls, cpf: str) -> tuple[bool, Optional[str]]:
        """
        Valida um CPF completo.
        
        Args:
            cpf: CPF a ser validado (com ou sem formatação)
        
        Returns:
            Tupla (is_valid, error_message)
        """
        # Remove formatação
        cpf_clean = cls.clean_cpf(cpf)
        
        # Verifica tamanho
        if len(cpf_clean) != 11:
            return False, f"CPF deve conter 11 dígitos, recebido {len(cpf_clean)}"
        
        # Verifica se não é um CPF inválido conhecido
        if cpf_clean in cls.INVALID_CPFS:
            return False, "CPF inválido (todos os dígitos iguais)"
        
        # Calcula primeiro dígito verificador
        first_digit = cls.calculate_digit(cpf_clean[:9], list(range(10, 1, -1)))
        if first_digit != int(cpf_clean[9]):
            return False, "Primeiro dígito verificador inválido"
        
        # Calcula segundo dígito verificador
        second_digit = cls.calculate_digit(cpf_clean[:10], list(range(11, 1, -1)))
        if second_digit != int(cpf_clean[10]):
            return False, "Segundo dígito verificador inválido"
        
        return True, None
    
    @classmethod
    def is_valid(cls, cpf: str) -> bool:
        """
        Verifica se um CPF é válido (versão simplificada).
        
        Args:
            cpf: CPF a ser validado
        
        Returns:
            True se válido, False caso contrário
        """
        is_valid, _ = cls.validate(cpf)
        return is_valid
    
    @classmethod
    def format_cpf(cls, cpf: str) -> str:
        """
        Formata um CPF no padrão XXX.XXX.XXX-XX.
        
        Args:
            cpf: CPF sem formatação
        
        Returns:
            CPF formatado
        """
        cpf_clean = cls.clean_cpf(cpf)
        if len(cpf_clean) != 11:
            return cpf
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"

