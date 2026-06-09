from django.core.exceptions import ValidationError
import re


def validate_string(
    val: str,
    field_name: str,
    allow_empty: bool = False,
    trim: bool = True,
    min_length: int = 0,
) -> str:
    """
    Validates a string value.

    :param val: The value to be validated.
    :param field_name: The name of the field to be validated.
    :param allow_empty: Whether the string can be empty or not.
    :param trim: Whether the string should be trimmed or not.
    :param min_length: The minimum length of the string.
    :return: The validated string.
    """
    if not isinstance(val, str):
        raise ValidationError(f"{field_name} must be a string")

    if trim:
        val = val.strip()

    if not allow_empty and len(val) == 0:
        raise ValidationError(f"{field_name} cannot be empty")

    if min_length > 0 and len(val) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long"
        )

    return val


def validate_email(val: str) -> str:
    """
    Validates an email address.

    :param val: The email address to be validated.
    :return: The validated email address.
    """
    val = validate_string(val, "email")
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", val):
        raise ValidationError("Invalid email address")

    return val


def validate_url(url: str):
    """
    Validates a URL.

    :param url: The URL to be validated.
    :return: The validated URL.
    """
    url = validate_string(url, "url")
    if not re.match(r"^(?:http|ftp)s?://", url):
        raise ValidationError("Invalid URL")

    return url


def validate_int(
    val: object,
    field_name: str,
    allow_negative: bool = True,
    allow_zero: bool = True,
) -> int:
    """
    Validates an integer value.

    :param val: The value to be validated.
    :param field_name: The name of the field to be validated.
    :param allow_negative: Whether the integer can be negative or not.
    :param allow_zero: Whether the integer can be zero or not.
    :return: The validated integer.
    """

    try:
        val = int(val)
    except ValueError or TypeError:
        raise ValidationError(f"{field_name} must be an integer")

    if not allow_negative and val < 0:
        raise ValidationError(f"{field_name} cannot be negative")

    if not allow_zero and val == 0:
        raise ValidationError(f"{field_name} cannot be zero")

    return val


def validate_list(val: object, field_name: str, required: bool = True) -> list:
    """
    Validates a list value.

    :param val: The value to be validated.
    :param field_name: The name of the field to be validated.
    :param required: Whether the list is required or not.
    :return: The validated list.
    """

    if not isinstance(val, list) and required:
        raise ValidationError(f"{field_name} must be a list")

    return val or []


def validate_phone_number(val: str, field_name: str) -> str:
    """
    Validates a phone number.

    :param val: The value to be validated.
    :param field_name: The name of the field to be validated.
    :return: The validated number.
    """
    val = validate_string(val, "phone_number")

    if not re.match(
        r"^(?:(?:\+|00)55)?(?:\s*\(?)(?:0?\d{2})?(?:\)?\s*)(?:[-\s]?)(?:\d{4,5})(?:[-\s]?)(?:\d{4})$",
        val,
    ):
        raise ValidationError(f"{field_name} must be a phone number (string)")

    val = val.replace(" ", "")
    val = val.replace("(", "")
    val = val.replace(")", "")
    val = val.replace("-", "")

    return val or None


def validate_cpf_number(val: str, field_name: str = "cpf"):
    """
    Validate a cpf number.
    """

    if not val:
        raise ValidationError(f"The field {field_name} is required.")

    cpf = ''.join(filter(str.isdigit, val))

    if len(cpf) != 11:
        raise ValidationError(f"{field_name.upper()} must have 11 digits.")

    if cpf == cpf[0] * 11:
        raise ValidationError(f"{field_name.upper()} invalid.")

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10

    if not (int(cpf[9]) == digito1 and int(cpf[10]) == digito2):
        raise ValidationError(f"{field_name.upper()} invalid.")


def validate_cnpj_number(val: str, field_name: str = "cnpj"):
    """
    Validate a cnpj number.
    """

    if not val:
        raise ValidationError(f"The field {field_name} is required.")

    cnpj = ''.join(filter(str.isdigit, val))

    if len(cnpj) != 14:
        raise ValidationError(f"{field_name.upper()} must have 14 digits.")

    if cnpj == cnpj[0] * 14:
        raise ValidationError(f"{field_name.upper()} invalid.")

    peso1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    peso2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    soma = sum(int(cnpj[i]) * peso1[i] for i in range(12))
    digito1 = 11 - (soma % 11)
    digito1 = digito1 if digito1 < 10 else 0

    soma = sum(int(cnpj[i]) * peso2[i] for i in range(13))
    digito2 = 11 - (soma % 11)
    digito2 = digito2 if digito2 < 10 else 0

    if not (int(cnpj[12]) == digito1 and int(cnpj[13]) == digito2):
        raise ValidationError(f"{field_name.upper()} invalid.")
