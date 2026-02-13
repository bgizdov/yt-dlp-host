# Testing Guide for yt-dlp-host

This document describes the testing infrastructure and how to run tests for the yt-dlp-host project.

## Table of Contents

- [Test Types](#test-types)
- [Quick Start](#quick-start)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [End-to-End Tests](#end-to-end-tests)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)

## Test Types

### 🔹 Unit Tests (`tests/unit/`)
Fast, isolated tests for individual functions and components.
- **Target:** 100% pass rate
- **Coverage:** 80%+ for critical functions
- **Runtime:** <1 second per test

### 🔸 Integration Tests (`tests/integration/`)
Tests for interactions between components with mocked external dependencies.
- **Target:** Core workflows validated
- **Runtime:** 1-5 seconds per test

### 🔶 End-to-End Tests (`tests/e2e/`)
Complete workflow tests with real downloads and validation.
- **Target:** Critical paths validated
- **Runtime:** 30-120 seconds per test
- **Requirements:** Running API, internet connection

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run all tests (unit + integration, E2E skipped by default)
pytest

# Run specific test type
pytest tests/unit/        # Unit tests only
pytest tests/integration/ # Integration tests only
pytest tests/e2e/        # E2E tests (will be skipped unless configured)
```

### Run Tests Without Coverage

```bash
pytest --no-cov
```

## Unit Tests

### ID3 Tag Tests (`tests/unit/test_id3_tags.py`)

Comprehensive tests for the `_update_mp3_id3_tags()` function.

**Test Coverage:**
- ✅ Artist-Track parsing ("Artist - Track" format)
- ✅ Title-only (no artist separator)
- ✅ Multiple separators (splits on first " - ")
- ✅ Whitespace trimming
- ✅ UTF-8 encoding for international characters
- ✅ Tag deduplication
- ✅ Edge cases (missing files, non-MP3, empty strings)
- ✅ Special characters and emojis
- ✅ Very long titles
- ✅ MP3 files without ID3 headers

**Running Unit Tests:**

```bash
# All unit tests
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_id3_tags.py -v

# Specific test
pytest tests/unit/test_id3_tags.py::TestID3Tags::test_artist_track_format_success -v

# With coverage
pytest tests/unit/ --cov=src/yt_handler --cov-report=term-missing
```

**Example Output:**

```
tests/unit/test_id3_tags.py::TestID3Tags::test_artist_track_format_success PASSED
tests/unit/test_id3_tags.py::TestID3Tags::test_title_only_no_separator PASSED
tests/unit/test_id3_tags.py::TestID3Tags::test_utf8_encoding_support PASSED
...
======================== 12 passed in 0.37s ========================
```

## Integration Tests

### Download + ID3 Workflow (`tests/integration/test_download_with_id3.py`)

Tests the complete download and ID3 tagging workflow with mocked external dependencies.

**Test Coverage:**
- ✅ Audio download triggers ID3 tag updates
- ✅ Video download skips ID3 tag updates
- ⚠️ Custom filename handling (needs workflow fixes)

**Running Integration Tests:**

```bash
# All integration tests
pytest tests/integration/ -v

# Specific test
pytest tests/integration/test_download_with_id3.py::TestDownloadWithID3::test_video_download_skips_id3_tags -v
```

## End-to-End Tests

### Complete Workflow Validation (`tests/e2e/test_download_and_validate_id3.py`)

E2E tests perform real downloads and validate ID3 tags on actual MP3 files.

**Test Coverage:**
- 🔄 Download audio and verify ID3 tags
- 🔄 Artist-Track format parsing (manual)
- 🔄 Unicode title handling (manual)

### Prerequisites

1. API server running at `http://localhost:5050`
2. Valid API key configured
3. Internet connection for YouTube downloads
4. Download directory accessible

### Configuration

Set environment variables:

```bash
export SKIP_E2E_TESTS="false"           # Enable E2E tests
export API_BASE_URL="http://localhost:5050"
export TEST_API_KEY="your-api-key"
export DOWNLOAD_DIR_HOST="./downloads"
```

### Running E2E Tests

```bash
# Using the helper script (recommended)
./run_e2e_tests.sh

# Manually with pytest
export SKIP_E2E_TESTS="false"
pytest tests/e2e/ -v -m e2e --no-cov

# Specific E2E test
pytest tests/e2e/test_download_and_validate_id3.py::TestDownloadAndValidateID3::test_download_audio_and_verify_id3_tags -v --no-cov
```

### E2E Test Output

```
[E2E] Creating download task for: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[E2E] Task created: abc123
[E2E] Waiting for task completion...
[E2E] Task completed: /files/abc123/audio.mp3
[E2E] Found MP3 file: ./downloads/abc123/audio.mp3
[E2E] Reading ID3 tags from: ./downloads/abc123/audio.mp3
[E2E] ✓ TIT2 (Title): Rick Astley - Never Gonna Give You Up
[E2E] ✓ TPE1 (Artist): Rick Astley
[E2E] ✓ All ID3 tag validations passed
PASSED [100%]
```

See [tests/e2e/README.md](tests/e2e/README.md) for detailed E2E testing documentation.

## Coverage Reports

### Generate Coverage Reports

```bash
# Terminal report
pytest tests/unit/ --cov=src --cov-report=term-missing

# HTML report
pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Coverage Targets

- **Overall:** 80% minimum (configured in `pytest.ini`)
- **ID3 function:** 87.1% achieved ✅
- **Critical paths:** 100% for core functionality

### Current Coverage

```
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
src/yt_handler.py     320    237    26%   [full report]
-------------------------------------------------
_update_mp3_id3_tags  62      8    87%   60-63, 93-96
```

Missing lines in ID3 function:
- Lines 60-63: Edge case when tags is None
- Lines 93-96: Exception traceback printing

## Running Tests by Marker

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only (must enable first)
export SKIP_E2E_TESTS="false"
pytest -m e2e

# Slow tests only
pytest -m slow
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Troubleshooting

### Tests Not Found

```bash
# Ensure you're in the project root
cd /workspaces/yt-dlp-host

# Clear pytest cache
rm -rf .pytest_cache __pycache__ */__pycache__

# Re-run
pytest --cache-clear
```

### Import Errors

```bash
# Install all dependencies
pip install -r requirements.txt

# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### E2E Tests Always Skipped

```bash
# Check environment variable
echo $SKIP_E2E_TESTS

# Enable E2E tests
export SKIP_E2E_TESTS="false"

# Verify
pytest tests/e2e/ -v --no-cov
```

### MP3 File Not Found in E2E Tests

- Verify `DOWNLOAD_DIR_HOST` points to correct directory
- Check Docker volume mounts in `docker-compose.yml`
- Ensure download directory has write permissions

## Test Development Guidelines

### Writing New Tests

1. **Choose the right test type:**
   - Unit: Testing a single function in isolation
   - Integration: Testing component interactions
   - E2E: Testing complete workflows

2. **Follow naming conventions:**
   - File: `test_*.py`
   - Class: `Test*`
   - Function: `test_*`

3. **Use descriptive names:**
   ```python
   def test_artist_track_format_success(self):  # Good
   def test_tags(self):  # Bad
   ```

4. **Add appropriate markers:**
   ```python
   @pytest.mark.unit
   @pytest.mark.slow
   def test_example(self):
       pass
   ```

5. **Use fixtures for setup:**
   ```python
   @pytest.fixture
   def mock_mp3_file(self, tmp_path):
       mp3_path = tmp_path / "test.mp3"
       create_minimal_mp3(str(mp3_path))
       return str(mp3_path)
   ```

### Test Structure (AAA Pattern)

```python
def test_example(self):
    # Arrange - Set up test data
    title = "Artist - Track"

    # Act - Execute the function
    result = function_under_test(title)

    # Assert - Verify expectations
    assert result == expected_value
```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Mutagen Documentation](https://mutagen.readthedocs.io/)
- [E2E Testing Guide](tests/e2e/README.md)

## Summary

```bash
# Quick test commands
pytest                              # All tests (E2E skipped)
pytest tests/unit/ -v              # Unit tests with verbose output
pytest tests/unit/ --cov=src       # Unit tests with coverage
pytest --no-cov                    # Skip coverage for speed
./run_e2e_tests.sh                # Run E2E tests (if API running)
```

**Test Status:**
- ✅ Unit Tests: 12/12 passing (100%)
- ✅ Integration Tests: 1/3 passing (33%)
- 🔄 E2E Tests: Configured, requires manual execution

**Coverage:**
- ✅ ID3 Function: 87.1% (exceeds 80% target)
- ⚠️ Overall: 26.75% (needs improvement)
