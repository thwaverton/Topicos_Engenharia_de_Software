"""
Testes unitários para o validador de CPF.
"""
import pytest

from src.validators.cpf_validator import CPFValidator


class TestCPFValidator:
    """Testes para a classe CPFValidator."""
    
    def test_cpf_valido(self):
        """Testa validação de CPF válido."""
        # CPF válido: 123.456.789-09
        is_valid, error = CPFValidator.validate("12345678909")
        assert is_valid is True
        assert error is None
    
    def test_cpf_valido_com_formatacao(self):
        """Testa validação de CPF válido com formatação."""
        is_valid, error = CPFValidator.validate("123.456.789-09")
        assert is_valid is True
        assert error is None
    
    def test_cpf_invalido_tamanho(self):
        """Testa CPF com tamanho inválido."""
        is_valid, error = CPFValidator.validate("123456789")
        assert is_valid is False
        assert "11 dígitos" in error
    
    def test_cpf_invalido_todos_digitos_iguais(self):
        """Testa CPF com todos os dígitos iguais."""
        is_valid, error = CPFValidator.validate("11111111111")
        assert is_valid is False
        assert "todos os dígitos iguais" in error
    
    def test_cpf_invalido_primeiro_digito(self):
        """Testa CPF com primeiro dígito verificador inválido."""
        is_valid, error = CPFValidator.validate("12345678900")
        assert is_valid is False
        assert "primeiro dígito" in error.lower()
    
    def test_cpf_invalido_segundo_digito(self):
        """Testa CPF com segundo dígito verificador inválido."""
        is_valid, error = CPFValidator.validate("12345678908")
        assert is_valid is False
        assert "segundo dígito" in error.lower()
    
    def test_clean_cpf(self):
        """Testa limpeza de CPF."""
        cpf_clean = CPFValidator.clean_cpf("123.456.789-09")
        assert cpf_clean == "12345678909"
    
    def test_format_cpf(self):
        """Testa formatação de CPF."""
        cpf_formatted = CPFValidator.format_cpf("12345678909")
        assert cpf_formatted == "123.456.789-09"
    
    def test_is_valid_shortcut(self):
        """Testa método is_valid (atalho)."""
        assert CPFValidator.is_valid("12345678909") is True
        assert CPFValidator.is_valid("11111111111") is False
    
    @pytest.mark.parametrize("cpf,expected", [
        ("12345678909", True),
        ("11111111111", False),
        ("00000000000", False),
        ("123", False),
        ("12345678900", False),
    ])
    def test_multiple_cpfs(self, cpf, expected):
        """Testa múltiplos CPFs."""
        is_valid, _ = CPFValidator.validate(cpf)
        assert is_valid is expected

