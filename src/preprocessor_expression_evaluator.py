from dataclasses import dataclass
import re
from typing import Any

from src.macro_indexer import (
    get_effective_macro_definitions,
)
from src.macro_resolver import resolve_macro_alias


TOKEN_PATTERN = re.compile(
    r"""
    \s*
    (
        0[xX][0-9A-Fa-f]+[uUlL]*
        |
        \d+[uUlL]*
        |
        [A-Za-z_]\w*
        |
        &&|\|\||==|!=|>=|<=
        |
        [()!<>&|+\-]
    )
    """,
    re.VERBOSE,
)

IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_]\w*$"
)

C_INTEGER_LITERAL_PATTERN = re.compile(
    r"^(0[xX][0-9A-Fa-f]+|\d+)[uUlL]*$"
)

C_NUMERIC_SUFFIX_PATTERN = re.compile(
    r"[uUlL]+$"
)


class ExpressionEvaluationError(Exception):
    """
    Raised when a #if expression cannot be safely evaluated.
    """


@dataclass
class EvaluationValue:
    """
    Represents an evaluated integer value and its resolved text.
    """

    value: int
    resolved_text: str


def evaluate_preprocessor_expression(
    expression: str,
    macro_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Safely evaluates a restricted C preprocessor expression.

    Supported syntax:
    - defined(MACRO)
    - defined MACRO
    - !defined(MACRO)
    - ==, !=, >, >=, <, <=
    - &&, ||
    - unary !
    - parentheses
    - integer literals and resolved macro aliases

    This evaluator intentionally does not use Python eval().
    """

    try:
        tokens = _tokenize_expression(expression)

        parser = ExpressionParser(
            tokens=tokens,
            macro_index=macro_index,
        )

        evaluated_value = parser.parse()

        if parser.has_remaining_tokens():
            raise ExpressionEvaluationError(
                "Unexpected token: "
                f"{parser.current_token()}"
            )

        evaluation_result = bool(evaluated_value.value)

        return {
            "original_expression": expression,
            "resolved_expression": (
                evaluated_value.resolved_text
            ),
            "evaluation": evaluation_result,
            "verdict": (
                "Active branch"
                if evaluation_result
                else "Inactive branch"
            ),
            "evaluation_status": "Evaluated",
            "referenced_macros": (
                parser.referenced_macros
            ),
            "error_message": "",
        }

    except ExpressionEvaluationError as error:
        return {
            "original_expression": expression,
            "resolved_expression": "",
            "evaluation": None,
            "verdict": "Unresolved expression",
            "evaluation_status": "Unresolved",
            "referenced_macros": [],
            "error_message": str(error),
        }


def _tokenize_expression(
    expression: str,
) -> list[str]:
    """
    Converts a preprocessor expression into allowed tokens.

    Any unsupported character or syntax produces a controlled error.
    """

    tokens: list[str] = []
    position = 0

    while position < len(expression):
        match = TOKEN_PATTERN.match(
            expression,
            position,
        )

        if match is None:
            remaining_text = expression[position:].strip()

            if not remaining_text:
                break

            raise ExpressionEvaluationError(
                "Unsupported expression content near: "
                f"{remaining_text[:30]}"
            )

        tokens.append(match.group(1))
        position = match.end()

    if not tokens:
        raise ExpressionEvaluationError(
            "Expression is empty"
        )

    return tokens


class ExpressionParser:
    """
    Restricted recursive-descent parser for supported #if syntax.

    Precedence order:
    1. Parentheses / defined()
    2. Unary !
    3. Additive operators: + and -
    4. Relational comparisons
    5. Equality comparisons
    6. Bitwise AND: &
    7. Bitwise OR: |
    8. Logical AND: &&
    9. Logical OR: ||
    """

    def __init__(
        self,
        tokens: list[str],
        macro_index: dict[str, dict[str, Any]],
    ) -> None:
        self.tokens = tokens
        self.macro_index = macro_index
        self.position = 0
        self.referenced_macros: list[str] = []

    def parse(self) -> EvaluationValue:
        """
        Parses the complete supported expression.
        """

        return self._parse_or_expression()

    def has_remaining_tokens(self) -> bool:
        """
        Returns True when tokens remain after parsing.
        """

        return self.position < len(self.tokens)

    def current_token(self) -> str:
        """
        Returns the current token for diagnostics.
        """

        if not self.has_remaining_tokens():
            return "<end>"

        return self.tokens[self.position]

    def _parse_or_expression(
        self,
    ) -> EvaluationValue:
        value = self._parse_and_expression()

        while self._match("||"):
            right_value = self._parse_and_expression()

            value = EvaluationValue(
                value=int(
                    bool(value.value)
                    or bool(right_value.value)
                ),
                resolved_text=(
                    f"({value.resolved_text} || "
                    f"{right_value.resolved_text})"
                ),
            )

        return value

    def _parse_and_expression(
        self,
    ) -> EvaluationValue:
        value = self._parse_bitwise_or_expression()

        while self._match("&&"):
            right_value = self._parse_bitwise_or_expression()

            value = EvaluationValue(
                value=int(
                    bool(value.value)
                    and bool(right_value.value)
                ),
                resolved_text=(
                    f"({value.resolved_text} && "
                    f"{right_value.resolved_text})"
                ),
            )

        return value

    def _parse_bitwise_or_expression(
        self,
    ) -> EvaluationValue:
        """
        Parses bitwise OR expressions using |.
        """

        value = self._parse_bitwise_and_expression()

        while self._match("|"):
            right_value = self._parse_bitwise_and_expression()

            value = EvaluationValue(
                value=value.value | right_value.value,
                resolved_text=(
                    f"({value.resolved_text} | "
                    f"{right_value.resolved_text})"
                ),
            )

        return value

    def _parse_bitwise_and_expression(
        self,
    ) -> EvaluationValue:
        """
        Parses bitwise AND expressions using &.
        """

        value = self._parse_equality_expression()

        while self._match("&"):
            right_value = self._parse_equality_expression()

            value = EvaluationValue(
                value=value.value & right_value.value,
                resolved_text=(
                    f"({value.resolved_text} & "
                    f"{right_value.resolved_text})"
                ),
            )

        return value

    def _parse_equality_expression(
        self,
    ) -> EvaluationValue:
        value = self._parse_relational_expression()

        while self.current_token() in (
            "==",
            "!=",
        ):
            operator = self._consume_token()
            right_value = self._parse_relational_expression()

            if operator == "==":
                comparison_result = (
                    value.value == right_value.value
                )
            else:
                comparison_result = (
                    value.value != right_value.value
                )

            value = EvaluationValue(
                value=int(comparison_result),
                resolved_text=(
                    f"({value.resolved_text} {operator} "
                    f"{right_value.resolved_text})"
                ),
            )

        return value

    def _parse_relational_expression(
        self,
    ) -> EvaluationValue:
        value = self._parse_additive_expression()

        while self.current_token() in (
            ">",
            ">=",
            "<",
            "<=",
        ):
            operator = self._consume_token()
            right_value = self._parse_additive_expression()

            comparison_result = _evaluate_relation(
                left_value=value.value,
                operator=operator,
                right_value=right_value.value,
            )

            value = EvaluationValue(
                value=int(comparison_result),
                resolved_text=(
                    f"({value.resolved_text} {operator} "
                    f"{right_value.resolved_text})"
                ),
            )

        return value

    def _parse_additive_expression(
        self,
    ) -> EvaluationValue:
        """
        Parses addition and subtraction expressions.
        """

        value = self._parse_unary_expression()

        while self.current_token() in (
            "+",
            "-",
        ):
            operator = self._consume_token()
            right_value = self._parse_unary_expression()

            if operator == "+":
                calculated_value = (
                    value.value + right_value.value
                )
            else:
                calculated_value = (
                    value.value - right_value.value
                )

            value = EvaluationValue(
                value=calculated_value,
                resolved_text=(
                    f"({value.resolved_text} {operator} "
                    f"{right_value.resolved_text})"
                ),
            )

        return value

    def _parse_unary_expression(
        self,
    ) -> EvaluationValue:
        if self._match("!"):
            value = self._parse_unary_expression()

            return EvaluationValue(
                value=int(not bool(value.value)),
                resolved_text=f"!({value.resolved_text})",
            )

        return self._parse_primary_expression()

    def _parse_primary_expression(
        self,
    ) -> EvaluationValue:
        if self._match("("):
            value = self._parse_or_expression()
            self._expect(")")

            return EvaluationValue(
                value=value.value,
                resolved_text=f"({value.resolved_text})",
            )

        if self.current_token() == "defined":
            return self._parse_defined_expression()

        token = self._consume_token()

        if _is_c_integer_literal(token):
            return EvaluationValue(
                value=_parse_c_integer_literal(token),
                resolved_text=token,
            )

        if IDENTIFIER_PATTERN.fullmatch(token):
            return self._resolve_macro_value(token)

        raise ExpressionEvaluationError(
            "Unsupported token: "
            f"{token}"
        )

    def _parse_defined_expression(
        self,
    ) -> EvaluationValue:
        self._expect("defined")

        if self._match("("):
            macro_name = self._consume_identifier()
            self._expect(")")
        else:
            macro_name = self._consume_identifier()

        self._register_macro(macro_name)

        is_defined = macro_name in self.macro_index

        return EvaluationValue(
            value=int(is_defined),
            resolved_text=(
                f"defined({macro_name})"
                f"={int(is_defined)}"
            ),
        )

    def _resolve_macro_value(
        self,
        macro_name: str,
    ) -> EvaluationValue:
        """
        Resolves one macro into an integer literal or recursively
        evaluates its replacement expression.

        This allows definitions such as:

        #define MASK_A 0x01u
        #define MASK_B 0x04u
        #define MASK_COMBINED (MASK_A | MASK_B)
        """

        self._register_macro(macro_name)

        effective_definitions = (
            get_effective_macro_definitions(
                self.macro_index
            )
        )

        resolution = resolve_macro_alias(
            macro_name=macro_name,
            definitions=effective_definitions,
        )

        if resolution["has_cycle"]:
            raise ExpressionEvaluationError(
                "Cyclic macro alias detected for: "
                f"{macro_name}"
            )

        if not resolution["is_resolved"]:
            raise ExpressionEvaluationError(
                "Macro definition not found: "
                f"{macro_name}"
            )

        resolved_value = resolution["resolved_value"]

        if resolved_value is None:
            raise ExpressionEvaluationError(
                "Macro has no resolved value: "
                f"{macro_name}"
            )

        resolved_text = str(resolved_value)

        if _is_c_integer_literal(resolved_text):
            return EvaluationValue(
                value=_parse_c_integer_literal(
                    resolved_text
                ),
                resolved_text=resolved_text,
            )

        nested_tokens = _tokenize_expression(
            resolved_text
        )

        nested_parser = ExpressionParser(
            tokens=nested_tokens,
            macro_index=self.macro_index,
        )

        nested_value = nested_parser.parse()

        if nested_parser.has_remaining_tokens():
            raise ExpressionEvaluationError(
                "Unexpected token in macro expression: "
                f"{nested_parser.current_token()}"
            )

        for referenced_macro in (
            nested_parser.referenced_macros
        ):
            self._register_macro(referenced_macro)

        return EvaluationValue(
            value=nested_value.value,
            resolved_text=nested_value.resolved_text,
        )

    def _register_macro(
        self,
        macro_name: str,
    ) -> None:
        if macro_name not in self.referenced_macros:
            self.referenced_macros.append(macro_name)

    def _match(
        self,
        expected_token: str,
    ) -> bool:
        if self.current_token() != expected_token:
            return False

        self.position += 1
        return True

    def _expect(
        self,
        expected_token: str,
    ) -> None:
        if not self._match(expected_token):
            raise ExpressionEvaluationError(
                f"Expected '{expected_token}', found "
                f"'{self.current_token()}'"
            )

    def _consume_token(self) -> str:
        if not self.has_remaining_tokens():
            raise ExpressionEvaluationError(
                "Unexpected end of expression"
            )

        token = self.tokens[self.position]
        self.position += 1

        return token

    def _consume_identifier(self) -> str:
        token = self._consume_token()

        if not IDENTIFIER_PATTERN.fullmatch(token):
            raise ExpressionEvaluationError(
                "Expected macro identifier, found: "
                f"{token}"
            )

        return token


def _evaluate_relation(
    left_value: int,
    operator: str,
    right_value: int,
) -> bool:
    """
    Applies one permitted relational operator.
    """

    if operator == ">":
        return left_value > right_value

    if operator == ">=":
        return left_value >= right_value

    if operator == "<":
        return left_value < right_value

    if operator == "<=":
        return left_value <= right_value

    raise ExpressionEvaluationError(
        "Unsupported relational operator: "
        f"{operator}"
    )


def _is_c_integer_literal(
    value: str,
) -> bool:
    """
    Returns True when value is a supported C integer literal.
    """

    return C_INTEGER_LITERAL_PATTERN.fullmatch(
        value
    ) is not None


def _parse_c_integer_literal(
    value: str,
) -> int:
    """
    Parses decimal or hexadecimal C integer literals with U/L suffixes.
    """

    numeric_text = C_NUMERIC_SUFFIX_PATTERN.sub(
        "",
        value,
    )

    try:
        return int(
            numeric_text,
            base=0,
        )
    except ValueError as error:
        raise ExpressionEvaluationError(
            "Invalid C integer literal: "
            f"{value}"
        ) from error