# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-02-13

### Fixed
- Limited the rack toggle button to rack objects only.
- Added permission-aware button rendering (button is hidden unless the user can run the action).
- Removed unrelated scaffold plugin surface from user-facing navigation and routes.

### Changed
- Bumped release version to `0.1.2`.
- Updated documentation for installation and feature scope.

### Testing
- Added template-content tests for rack-only rendering and permission-based visibility.
- Current suite status in local NetBox Docker: `24 passed, 0 failed`.

## [0.1.1] - 2026-02-13

### Fixed
- Added row locking for rack/device/reservation toggle operations.
- Switched from bulk update calls to model `save()` calls for position/unit writes.
- Added initial migration for plugin model table creation.

### Added
- Toggle round-trip tests for mixed-height devices.
- Tests for non-default `starting_unit`.
- Tests for reservations and no-reservations cases.
- Test coverage for preserving relationships and `custom_field_data`.

## [0.1.0] - 2026-02-13

### Added
- Initial plugin scaffold generated from cookiecutter.
