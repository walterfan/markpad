## ADDED Requirements

### Requirement: Recursive Markdown file discovery
The system SHALL discover Markdown files under the selected content root and its subdirectories.

#### Scenario: Nested Markdown file
- **WHEN** the content root contains a Markdown file in a nested subdirectory
- **THEN** the index includes that file with a root-relative path

#### Scenario: Non-Markdown file
- **WHEN** the content root contains a file without a Markdown extension
- **THEN** the index excludes that file

### Requirement: Supported Markdown extensions
The system SHALL include files with `.md`, `.markdown`, and `.mdown` extensions case-insensitively.

#### Scenario: Uppercase extension
- **WHEN** the content root contains `Notes.MD`
- **THEN** the index includes `Notes.MD`

#### Scenario: Alternate Markdown extension
- **WHEN** the content root contains `guide.markdown`
- **THEN** the index includes `guide.markdown`

### Requirement: Deterministic index ordering
The system SHALL return indexed Markdown files in deterministic path order.

#### Scenario: Multiple files
- **WHEN** the content root contains Markdown files in multiple directories
- **THEN** the index orders them by normalized root-relative path

### Requirement: Index metadata
The system SHALL include metadata needed for navigation and freshness checks for each indexed Markdown file.

#### Scenario: Indexed file metadata
- **WHEN** the index includes a Markdown file
- **THEN** the entry includes root-relative path, display name, directory, file size, and last modified time

### Requirement: Default ignored directories
The system SHALL skip common generated or dependency directories while indexing.

#### Scenario: Dependency directory
- **WHEN** the content root contains Markdown files under `node_modules`
- **THEN** the index excludes those files by default

#### Scenario: Git directory
- **WHEN** the content root contains Markdown files under `.git`
- **THEN** the index excludes those files by default
