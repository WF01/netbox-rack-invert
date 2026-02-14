# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2026-02-14

### Fixed
- Enforced object-level permission checks for every affected `Device` and `RackReservation` before toggling rack order.
- Improved permission UX on rack pages: action button now renders disabled with detailed missing-permission tooltip instead of disappearing.
- Converted legacy scaffold migration `0001_initial` to a no-op so fresh installs no longer create an unused plugin model table.
- Added safe legacy scaffold cleanup migration that removes old scaffold table only when empty.
- Pinned `requirements/netbox-plugin.txt` to `v0.1.3` for reproducible installs.

### Added
- Regression tests for constrained object permission scenarios (view rejection and disabled-button behavior with details).
- Installer support for persisting plugin requirement into `local_requirements.txt` via `PERSIST_LOCAL_REQUIREMENTS=1`.

### Changed
- Bumped release version to `0.1.3`.
- Updated `README.md`, `TESTING.md`, and contributor guidance to match current plugin scope and install workflows.
- Simplified `Makefile` lint/format targets to use actual package paths.

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
- Current suite status in local NetBox Docker: `41 passed, 0 failed`.

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
