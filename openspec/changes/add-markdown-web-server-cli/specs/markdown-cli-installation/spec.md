## ADDED Requirements

### Requirement: Shell script installs the CLI
The system SHALL provide a shell script that installs or links the Markdown web server CLI for local use.

#### Scenario: Install from repository root
- **WHEN** the user runs the install shell script from the repository root
- **THEN** the script installs dependencies, builds the project, and makes the CLI command available

#### Scenario: Install reports command name
- **WHEN** the install shell script completes successfully
- **THEN** it prints the installed CLI command name and a command the user can run to verify installation

### Requirement: Installed CLI runs from Markdown folders
The installed CLI SHALL be runnable from a folder that contains Markdown files without requiring project-internal commands.

#### Scenario: Run installed CLI in Markdown folder
- **WHEN** the user runs the installed CLI from a folder containing Markdown files
- **THEN** the CLI starts the web server with that folder as the content root

#### Scenario: Render pages after installed startup
- **WHEN** the installed CLI starts successfully in a Markdown folder
- **THEN** the browser UI shows the indexed Markdown files and can render selected files as web pages

### Requirement: Install script fails clearly
The install shell script SHALL fail with clear guidance when required tools or steps are unavailable.

#### Scenario: Missing Python runtime
- **WHEN** the install shell script runs without a required Python 3 runtime available
- **THEN** it exits with a non-zero status and prints the missing prerequisite

#### Scenario: Missing Poetry
- **WHEN** the install shell script runs without Poetry available
- **THEN** it exits with a non-zero status and prints the missing prerequisite

#### Scenario: Build failure
- **WHEN** Poetry dependency installation or package installation fails
- **THEN** the install shell script exits with a non-zero status and preserves the failing command output
