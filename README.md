# Automation Tool for Compiler Switches and Conditional Compilation Verification

## Description

Python tool developed to support the analysis of compiler switches and conditional compilation directives in embedded software projects.

The initial scope focuses on the **Release_DMS** project, specifically the **Core1 / Release** configuration.

## MVP Objective

The first version of the tool will:

- Read `compile_opt.mk` and extract compiler options.
- Identify macros declared through `-D` flags.
- Scan C/C++ source files recursively.
- Detect `#if`, `#ifdef`, `#ifndef`, and `#elif` directives.
- Generate an initial Excel or CSV report with the findings.

## Project Structure

```text
automation_tool/
├── config/
│   └── project_paths.yaml
├── src/
├── tests/
│   └── fixtures/
│       ├── compile_opt_example.mk
│       ├── ExampleModule.c
│       ├── ExampleModule.h
│       └── ExampleModule_Cfg.h
├── output/
├── main.py
├── requirements.txt
└── .gitignore