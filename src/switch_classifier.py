from typing import Any

import re

CATEGORY_KEYWORDS = {
    "DEBUG": [
        "DEBUG",
        "DBG",
        "TRACE",
        "LOG",
    ],
    "TEST": [
        "UNIT_TEST",
        "SYSTEM_TEST",
        "TEST_MODE",
        "TEST",
        "SIL",
    ],
    "INTEGRATION": [
        "INTEGRATION",
        "INTEG",
    ],
    "FEATURE": [
        "FEATURE",
        "ENABLE",
        "DISABLE",
        "OPTION",
        "CONFIG",
    ],
}

MEMMAP_KEYWORDS = [
    "START_SEC",
    "STOP_SEC",
    "MEMMAP",
]

TOOLCHAIN_KEYWORDS = [
    "__GNUC__",
    "__CLANG__",
    "__ICCARM__",
    "__ARMCC_VERSION",
    "__cplusplus",
    "_CORE_CM0PLUS_",
    "_CORE_CM4_",
    "_CORE_CM7_",
    "ARM_MATH_",
    "CPU_TYPE",
    "__ARM_ARCH_",
    "__ARM_FEATURE_",
    "CY_CPU_CORTEX_",
    "__GHS__",
]

VENDOR_CMSIS_KEYWORDS = [
    "__VENDOR_SYSTICKCONFIG",
]

PLATFORM_CAPABILITY_PREFIXES = (
    "ACT_PLATFORM_",
)

CMSIS_FRAMEWORK_FILE_PREFIXES = (
    "cmsis_",
    "core_cm",
)

CMSIS_FRAMEWORK_FILE_NAMES = (
    "mpu_armv7.h",
)

STATIC_ANALYSIS_KEYWORDS = [
    "LINT",
    "PC_LINT",
    "PRQA",
    "MISRA",
    "COVERITY",
    "POLYSPACE",
]

TEST_FRAMEWORK_KEYWORDS = [
    "TESSY",
]

GENERATED_TEST_PREFIXES = (
    "CDD_TEST_",
    "BSW_TEST_",
    "MCAL_TEST_",
    "FBL",
)

GENERATED_TEST_KEYWORDS = [
    "DUMMY",
    "ATOMIC",
    "CPUTYPE",
    "COMPILER",
    "PROCESSOR_",
    "COMP_",
    "GEN_GENERATOR",
    "POSTBUILD_VARIANT",
]


HEADER_GUARD_SUFFIXES = (
    "_H",
    "_H_",
    "_HH",
    "_HPP",
)


def classify_preprocessor_finding(
    finding: dict[str, Any],
) -> dict[str, Any]:
    """
    Classifies a preprocessor finding and identifies common
    false-positive conditions.

    Expected finding fields from preprocessor_parser.py:
    - path
    - file_name
    - line_number
    - directive
    - expression
    - macros
    """

    expression = str(
        finding.get("expression", "")
    )

    directive = str(
        finding.get("directive", "")
    )

    file_name = str(
        finding.get("file_name", "")
    )

    line_number = int(
        finding.get("line_number", 0)
    )

    macros = _get_macros(
        finding=finding,
        expression=expression,
    )

    searchable_text = " ".join(
        [
            expression,
            directive,
            *macros,
        ]
    ).upper()

    category, matched_keywords = _get_category(
        searchable_text
    )

    is_header_guard = _is_header_guard(
        directive=directive,
        macros=macros,
        file_name=file_name,
        line_number=line_number,
    )

    is_memmap = _contains_keyword(
        searchable_text,
        MEMMAP_KEYWORDS,
    )

    is_toolchain_condition = _contains_keyword(
        searchable_text,
        TOOLCHAIN_KEYWORDS,
    )


    is_device_selection_condition = (
        _is_device_selection_condition(
            file_name=file_name,
            macros=macros,
        )
    )
    
    is_vendor_cmsis_condition = _contains_keyword(
        searchable_text,
        VENDOR_CMSIS_KEYWORDS,
    )

    is_cmsis_framework_condition = (
        _is_cmsis_framework_condition(
            file_name=file_name,
        )
    )

    is_platform_capability_condition = (
        _is_platform_capability_condition(
            macros=macros,
        )
    )

    is_static_analysis_condition = _contains_keyword(
        searchable_text,
        STATIC_ANALYSIS_KEYWORDS,
    )

    is_test_framework_condition = _contains_keyword(
        searchable_text,
        TEST_FRAMEWORK_KEYWORDS,
    )

    is_generated_test_condition = (
        _is_generated_test_condition(
            macros=macros,
            searchable_text=searchable_text,
        )
    )

    is_generated_configuration_variant = (
        _is_generated_configuration_variant(
            macros=macros,
        )
    )

    filter_reason = _get_filter_reason(
        is_header_guard=is_header_guard,
        is_memmap=is_memmap,
        is_toolchain_condition=(
            is_toolchain_condition
            or is_device_selection_condition
        ),
        is_vendor_cmsis_condition=(
            is_vendor_cmsis_condition
        ),
        is_cmsis_framework_condition=(
            is_cmsis_framework_condition
        ),
        is_platform_capability_condition=(
            is_platform_capability_condition
        ),
        is_static_analysis_condition=(
            is_static_analysis_condition
        ),
        is_test_framework_condition=(
            is_test_framework_condition
        ),
        is_generated_test_condition=(
            is_generated_test_condition
        ),
        is_generated_configuration_variant=(
            is_generated_configuration_variant
        ),
    )
    is_relevant = (
        category != "OTHER"
        and not filter_reason
    )

    return {
        "category": category,
        "matched_keywords": matched_keywords,
        "is_header_guard": is_header_guard,
        "is_memmap": is_memmap,
        "is_toolchain_condition": (
            is_toolchain_condition
        ),
        "is_device_selection_condition": (
            is_device_selection_condition
        ),
        "is_vendor_cmsis_condition": (
            is_vendor_cmsis_condition
        ),
        "is_cmsis_framework_condition": (
            is_cmsis_framework_condition
        ),
        "is_platform_capability_condition": (
            is_platform_capability_condition
        ),
        "is_static_analysis_condition": (
            is_static_analysis_condition
        ),
        "is_test_framework_condition": (
            is_test_framework_condition
        ),
        "is_generated_test_condition": (
            is_generated_test_condition
        ),
        "is_generated_configuration_variant": (
            is_generated_configuration_variant
        ),
        "is_relevant": is_relevant,
        "filter_reason": filter_reason,
    }


def _get_macros(
    finding: dict[str, Any],
    expression: str,
) -> list[str]:
    """
    Gets macros from the parser result. Falls back to the expression
    when the parser did not return macros.
    """

    raw_macros = finding.get("macros", [])

    if isinstance(raw_macros, list):
        return [
            str(macro)
            for macro in raw_macros
        ]

    if raw_macros:
        return [str(raw_macros)]

    return [expression] if expression else []


def _get_category(
    searchable_text: str,
) -> tuple[str, list[str]]:
    """
    Returns the first matching functional-switch category.

    INTEGRATION has priority over TEST because a condition such as
    INTEGRATION_WATCHDOG_TESTS is more specifically an integration
    condition than a generic test condition.

    SIL is matched as an independent token. This avoids false
    positives in identifiers such as COMM_SILENT_COMMUNICATION.
    """

    category_order = [
        "DEBUG",
        "INTEGRATION",
        "TEST",
        "FEATURE",
    ]

    for category in category_order:
        keywords = CATEGORY_KEYWORDS[category]

        matched_keywords = [
            keyword
            for keyword in keywords
            if _matches_category_keyword(
                searchable_text=searchable_text,
                keyword=keyword,
            )
        ]

        if matched_keywords:
            return category, matched_keywords

    return "OTHER", []

def _matches_category_keyword(
    searchable_text: str,
    keyword: str,
) -> bool:
    """
    Matches a category keyword against a preprocessor condition.

    SIL requires token-aware matching so SILENT, ASILVAR, and other
    larger identifiers do not become TEST conditions accidentally.
    """

    normalized_keyword = keyword.upper()

    if normalized_keyword == "SIL":
        return re.search(
            r"(?<![A-Z0-9])SIL(?![A-Z0-9])",
            searchable_text,
        ) is not None

    return normalized_keyword in searchable_text

def _is_header_guard(
    directive: str,
    macros: list[str],
    file_name: str,
    line_number: int,
) -> bool:
    """
    Detects probable C/C++ header guards.

    A probable header guard must:
    - occur in a .h or .hpp file;
    - use #ifndef;
    - appear near the beginning of the file;
    - contain exactly one macro;
    - use a conventional header suffix, such as _H or _H_.
    """

    is_header_file = file_name.lower().endswith(
        (".h", ".hpp")
    )

    if not is_header_file:
        return False

    if directive.strip().lower() != "#ifndef":
        return False

    if line_number > 30:
        return False

    if len(macros) != 1:
        return False

    macro_name = macros[0].upper()

    return macro_name.endswith(
        HEADER_GUARD_SUFFIXES
    )

def _is_device_selection_condition(
    file_name: str,
    macros: list[str],
) -> bool:
    """
    Detects Cypress/Infineon device-selection conditions in the
    vendor device-header file.

    Examples:
    - CYT2B77CAE
    - CYT2B78BAS
    - CYT2B78CAE

    The file restriction prevents project-specific macros with a
    similar name from being excluded unintentionally.
    """

    if file_name.lower() != "cy_device_headers.h":
        return False

    return any(
        macro.upper().startswith("CYT")
        for macro in macros
    )

def _is_cmsis_framework_condition(
    file_name: str,
) -> bool:
    """
    Detects conditions located in known CMSIS framework headers.

    These headers contain compiler, architecture, FPU, intrinsic,
    and Cortex-core infrastructure checks rather than application
    compiler switches.

    The filename restriction prevents application conditions using
    similar macro names from being filtered automatically.
    """

    normalized_file_name = file_name.lower()

    return (
        normalized_file_name.startswith(
            CMSIS_FRAMEWORK_FILE_PREFIXES
        )
        or normalized_file_name
        in CMSIS_FRAMEWORK_FILE_NAMES
    )

def _is_generated_test_condition(
    macros: list[str],
    searchable_text: str,
) -> bool:
    """
    Detects internal/generated test conditions commonly found in
    AUTOSAR, BSW, CDD, or MCAL generated code.

    The macro must use a known generated-test prefix and include
    an implementation-oriented keyword.
    """

    normalized_macros = [
        macro.upper()
        for macro in macros
    ]

    has_generated_test_prefix = any(
        macro.startswith(GENERATED_TEST_PREFIXES)
        for macro in normalized_macros
    )

    has_internal_test_keyword = _contains_keyword(
        searchable_text,
        GENERATED_TEST_KEYWORDS,
    )

    return (
        has_generated_test_prefix
        and has_internal_test_keyword
    )

def _is_platform_capability_condition(
    macros: list[str],
) -> bool:
    """
    Detects platform capability macros used by the ACT/SecPrim
    implementation layer.

    Examples:
    - ACT_PLATFORM_ALIGNMENT
    - ACT_PLATFORM_CPUTYPE_32BIT
    - ACT_PLATFORM_UINT64_AVAILABLE

    These conditions describe compiler/platform capabilities rather
    than functional product switches.
    """

    normalized_macros = [
        macro.upper()
        for macro in macros
    ]

    return any(
        macro.startswith(PLATFORM_CAPABILITY_PREFIXES)
        for macro in normalized_macros
    )

def _is_generated_configuration_variant(
    macros: list[str],
) -> bool:
    """
    Detects generated build/configuration-variant conditions.

    These macros select generated compile-time or post-build variants
    instead of enabling a functional product feature.

    Examples:
    - CDDOSPH_CONFIGURATION_VARIANT_PRECOMPILE
    - FBLBMHDR_CONFIGURATION_VARIANT_LINKTIME
    - CANIF_CONFIG_VARIANT
    - CANIF_POSTBUILD_VARIANT_SUPPORT
    """

    variant_keywords = (
        "CONFIGURATION_VARIANT",
        "CONFIG_VARIANT",
        "POSTBUILD_VARIANT",
    )

    normalized_macros = [
        macro.upper()
        for macro in macros
    ]

    return any(
        any(
            keyword in macro
            for keyword in variant_keywords
        )
        for macro in normalized_macros
    )

def _contains_keyword(
    searchable_text: str,
    keywords: list[str],
) -> bool:
    """
    Checks whether any configured keyword appears in the text.
    """

    return any(
        keyword.upper() in searchable_text
        for keyword in keywords
    )


def _get_filter_reason(
    is_header_guard: bool,
    is_memmap: bool,
    is_toolchain_condition: bool,
    is_vendor_cmsis_condition: bool,
    is_cmsis_framework_condition: bool,
    is_platform_capability_condition: bool,
    is_static_analysis_condition: bool,
    is_test_framework_condition: bool,
    is_generated_test_condition: bool,
    is_generated_configuration_variant: bool,
) -> str:
    """
    Returns the primary reason why a condition is excluded.
    """

    if is_header_guard:
        return "Header guard"

    if is_memmap:
        return "MemMap section marker"

    if is_toolchain_condition:
        return "Toolchain or architecture condition"

    if is_vendor_cmsis_condition:
        return "Vendor CMSIS configuration condition"

    if is_cmsis_framework_condition:
        return "CMSIS framework condition"

    if is_platform_capability_condition:
        return "Platform capability condition"

    if is_static_analysis_condition:
        return "Static-analysis condition"

    if is_test_framework_condition:
        return "Test framework or instrumentation condition"

    if is_generated_test_condition:
        return "Generated or internal test condition"

    if is_generated_configuration_variant:
        return (
            "Generated configuration-variant condition"
        )

    return ""