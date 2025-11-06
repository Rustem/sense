# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [2025-11-06]

### Added
- Last 3 Days/Week/Month filter buttons for multi-day trend analysis
- Calendar gradient visualization (light/medium/dark blue) based on daily activity levels
- Daily trend charts for active time, interruptions, and context switches
- Stacked bar charts showing top 5 interruption and switch patterns across selected period
- Period display under dashboard title (e.g., "Oct 26, 2025 – Nov 5, 2025")
- Best/worst day insights with explanations for date range selections
- Average per day metrics displayed alongside totals for multi-day ranges

### Changed
- Refactored dashboard.js for better maintainability (extracted constants, DRY principles)
- Removed window usage in favor of module-level variables
- Consolidated filter setup logic into reusable configuration

## [2025-11-02]

### Added
- Instructions for running against production database
