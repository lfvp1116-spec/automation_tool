from src.switch_classifier import (
    classify_preprocessor_finding,
)


def test_classifies_debug_condition() -> None:
    finding = {
        "file_name": "Det.c",
        "line_number": 10,
        "directive": "#if",
        "expression": (
            "DET_DEBUG_ENABLED == STD_ON"
        ),
        "macros": [
            "DET_DEBUG_ENABLED",
            "STD_ON",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "DEBUG"
    assert result["is_relevant"] is True
    assert result["filter_reason"] == ""


def test_classifies_test_condition() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 10,
        "directive": "#if",
        "expression": "defined(TEST_MODE)",
        "macros": ["TEST_MODE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "TEST"
    assert result["is_relevant"] is True


def test_classifies_integration_condition() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 20,
        "directive": "#if",
        "expression": (
            "defined(INTEGRATION_TEST_MODE)"
        ),
        "macros": ["INTEGRATION_TEST_MODE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "INTEGRATION"
    assert result["is_relevant"] is True


def test_classifies_feature_condition() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 30,
        "directive": "#ifdef",
        "expression": "FEATURE_X",
        "macros": ["FEATURE_X"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "FEATURE"
    assert result["is_relevant"] is True


def test_marks_header_guard_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.h",
        "line_number": 1,
        "directive": "#ifndef",
        "expression": "EXAMPLE_MODULE_H",
        "macros": ["EXAMPLE_MODULE_H"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_header_guard"] is True
    assert result["is_relevant"] is False
    assert result["filter_reason"] == "Header guard"


def test_marks_memmap_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 50,
        "directive": "#ifdef",
        "expression": "START_SEC_CODE",
        "macros": ["START_SEC_CODE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_memmap"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "MemMap section marker"
    )


def test_marks_toolchain_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 60,
        "directive": "#ifdef",
        "expression": "__GNUC__",
        "macros": ["__GNUC__"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_toolchain_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Toolchain or architecture condition"
    )


def test_marks_static_analysis_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 70,
        "directive": "#ifdef",
        "expression": "PRQA_S 1234",
        "macros": ["PRQA_S"],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_static_analysis_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Static-analysis condition"
    )


def test_marks_other_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 80,
        "directive": "#if",
        "expression": "VALUE > 0",
        "macros": ["VALUE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "OTHER"
    assert result["is_relevant"] is False
    assert result["filter_reason"] == ""

def test_marks_generated_test_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "Cdd_test_Cbk.h",
        "line_number": 64,
        "directive": "#ifndef",
        "expression": "CDD_TEST_DUMMY_STATEMENT",
        "macros": [
            "CDD_TEST_DUMMY_STATEMENT",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "TEST"
    assert (
        result["is_generated_test_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated or internal test condition"
    )


def test_keeps_regular_test_condition_relevant() -> None:
    finding = {
        "file_name": "Watchdog.c",
        "line_number": 84,
        "directive": "#if",
        "expression": (
            "INTEGRATION_WATCHDOG_TESTS == WDG_STD_ON"
        ),
        "macros": [
            "INTEGRATION_WATCHDOG_TESTS",
            "WDG_STD_ON",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "INTEGRATION"
    assert (
        result["is_generated_test_condition"]
        is False
    )
    assert result["is_relevant"] is True
    assert result["filter_reason"] == ""

def test_marks_arm_cmsis_capability_as_not_relevant() -> None:
    finding = {
        "file_name": "cmsis_iccarm.h",
        "line_number": 69,
        "directive": "#if",
        "expression": (
            "defined(__ARM_FEATURE_CMSE)"
        ),
        "macros": ["__ARM_FEATURE_CMSE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_toolchain_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Toolchain or architecture condition"
    )


def test_marks_vendor_cmsis_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "core_cm4.h",
        "line_number": 214,
        "directive": "#ifndef",
        "expression": "__Vendor_SysTickConfig",
        "macros": ["__Vendor_SysTickConfig"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_vendor_cmsis_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Vendor CMSIS configuration condition"
    )


def test_marks_extended_generated_test_condition() -> None:
    finding = {
        "file_name": "Cdd_test_Cbk.h",
        "line_number": 79,
        "directive": "#ifndef",
        "expression": "CDD_TEST_PROCESSOR_CYT2B75CXX",
        "macros": [
            "CDD_TEST_PROCESSOR_CYT2B75CXX",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_generated_test_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated or internal test condition"
    )


def test_marks_generated_configuration_variant() -> None:
    finding = {
        "file_name": "CddOsph_Cfg.h",
        "line_number": 117,
        "directive": "#ifndef",
        "expression": (
            "CDDOSPH_CONFIGURATION_VARIANT_PRECOMPILE"
        ),
        "macros": [
            "CDDOSPH_CONFIGURATION_VARIANT_PRECOMPILE",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_generated_configuration_variant"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated configuration-variant condition"
    )

def test_marks_generic_configuration_variant_as_not_relevant(
) -> None:
    finding = {
        "file_name": "FblBmHdr_Cfg.h",
        "line_number": 88,
        "directive": "#ifndef",
        "expression": (
            "FBLBMHDR_CONFIGURATION_VARIANT_PRECOMPILE"
        ),
        "macros": [
            "FBLBMHDR_CONFIGURATION_VARIANT_PRECOMPILE",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_generated_configuration_variant"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated configuration-variant condition"
    )

def test_marks_fbl_generated_internal_condition(
) -> None:
    finding = {
        "file_name": "FblBmHdr_Cfg.h",
        "line_number": 64,
        "directive": "#ifndef",
        "expression": "FBLBMHDR_DUMMY_STATEMENT",
        "macros": [
            "FBLBMHDR_DUMMY_STATEMENT",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_generated_test_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated or internal test condition"
    )

def test_marks_cypress_cortex_cpu_as_not_relevant() -> None:
    finding = {
        "file_name": "cy_syslib.h",
        "line_number": 90,
        "directive": "#if",
        "expression": "(CY_CPU_CORTEX_M7)",
        "macros": ["CY_CPU_CORTEX_M7"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_toolchain_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Toolchain or architecture condition"
    )

def test_marks_cypress_device_selection_as_not_relevant(
) -> None:
    finding = {
        "file_name": "cy_device_headers.h",
        "line_number": 54,
        "directive": "#elif",
        "expression": "defined(CYT2B77CAE)",
        "macros": ["CYT2B77CAE"],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_device_selection_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Toolchain or architecture condition"
    )

def test_keeps_project_cyt_macro_outside_vendor_header(
) -> None:
    finding = {
        "file_name": "ApplicationFeature.c",
        "line_number": 42,
        "directive": "#ifdef",
        "expression": "CYT_FEATURE_ENABLE",
        "macros": ["CYT_FEATURE_ENABLE"],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_device_selection_condition"]
        is False
    )
    assert result["is_relevant"] is True
    assert result["filter_reason"] == ""

def test_marks_green_hills_compiler_condition_as_not_relevant(
) -> None:
    finding = {
        "file_name": "cy_syslib.h",
        "line_number": 270,
        "directive": "#elif",
        "expression": "defined(__ghs__)",
        "macros": ["__ghs__"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_toolchain_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Toolchain or architecture condition"
    )

def test_marks_cmsis_framework_condition_as_not_relevant(
) -> None:
    finding = {
        "file_name": "cmsis_compiler.h",
        "line_number": 121,
        "directive": "#ifndef",
        "expression": "__ALIGNED",
        "macros": ["__ALIGNED"],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_cmsis_framework_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "CMSIS framework condition"
    )


def test_keeps_non_cmsis_macro_without_cmsis_filter(
) -> None:
    finding = {
        "file_name": "ApplicationModule.c",
        "line_number": 42,
        "directive": "#ifdef",
        "expression": "__ALIGNED",
        "macros": ["__ALIGNED"],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_cmsis_framework_condition"]
        is False
    )
    assert result["filter_reason"] == ""

def test_marks_act_platform_capability_as_not_relevant(
) -> None:
    finding = {
        "file_name": "actPlatformTypes.h",
        "line_number": 87,
        "directive": "#elif",
        "expression": (
            "defined(ACT_PLATFORM_CPUTYPE_32BIT)"
        ),
        "macros": [
            "ACT_PLATFORM_CPUTYPE_32BIT",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_platform_capability_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Platform capability condition"
    )


def test_keeps_act_speed_setting_for_review() -> None:
    finding = {
        "file_name": "actAES.c",
        "line_number": 844,
        "directive": "#elif",
        "expression": "actAES_SPEED_UP == 3",
        "macros": ["actAES_SPEED_UP"],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_platform_capability_condition"]
        is False
    )
    assert result["filter_reason"] == ""


def test_marks_config_variant_as_not_relevant() -> None:
    finding = {
        "file_name": "CanIf.c",
        "line_number": 2053,
        "directive": "#if",
        "expression": (
            "CANIF_CONFIG_VARIANT == "
            "CANIF_CFGVAR_POSTBUILDTIME"
        ),
        "macros": [
            "CANIF_CONFIG_VARIANT",
            "CANIF_CFGVAR_POSTBUILDTIME",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_generated_configuration_variant"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated configuration-variant condition"
    )


def test_marks_postbuild_variant_as_not_relevant() -> None:
    finding = {
        "file_name": "CanIf.c",
        "line_number": 1940,
        "directive": "#if",
        "expression": (
            "CANIF_POSTBUILD_VARIANT_SUPPORT == STD_ON"
        ),
        "macros": [
            "CANIF_POSTBUILD_VARIANT_SUPPORT",
            "STD_ON",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_generated_configuration_variant"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated configuration-variant condition"
    )


def test_marks_postbuild_variant_as_not_relevant() -> None:
    finding = {
        "file_name": "CanIf.c",
        "line_number": 1940,
        "directive": "#if",
        "expression": (
            "CANIF_POSTBUILD_VARIANT_SUPPORT == STD_ON"
        ),
        "macros": [
            "CANIF_POSTBUILD_VARIANT_SUPPORT",
            "STD_ON",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_generated_configuration_variant"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated configuration-variant condition"
    )

def test_marks_tessy_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "RomTest.c",
        "line_number": 129,
        "directive": "#if",
        "expression": (
            "TESSY_CONFIGURATION_VALIDATION_TEST"
        ),
        "macros": [
            "TESSY_CONFIGURATION_VALIDATION_TEST",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "TEST"
    assert (
        result["is_test_framework_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Test framework or instrumentation condition"
    )


def test_does_not_classify_silent_mode_as_test() -> None:
    finding = {
        "file_name": "Can.c",
        "line_number": 991,
        "directive": "#if",
        "expression": "CAN_SILENT_MODE == STD_ON",
        "macros": [
            "CAN_SILENT_MODE",
            "STD_ON",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "OTHER"
    assert result["matched_keywords"] == []
    assert result["is_relevant"] is False
    assert result["filter_reason"] == ""


def test_classifies_sil_token_as_test() -> None:
    finding = {
        "file_name": "SilSimulation.c",
        "line_number": 42,
        "directive": "#ifdef",
        "expression": "SIL_SIMULATION",
        "macros": ["SIL_SIMULATION"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "TEST"
    assert result["matched_keywords"] == ["SIL"]
    assert result["is_relevant"] is True