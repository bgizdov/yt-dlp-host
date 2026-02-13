# End-to-End (E2E) Tests for ID3 Tag Validation

This directory contains E2E tests that validate the complete download workflow including ID3 tag writing and validation.

## Overview

The E2E tests perform actual downloads from YouTube, extract audio to MP3, and verify that ID3 tags are correctly written to the files.

## Prerequisites

1. **Running API Server**: The yt-dlp-host API must be running
2. **Valid API Key**: An API key must be configured
3. **Internet Connection**: Required for YouTube downloads
4. **Docker Environment**: Tests expect the service to be running in Docker

## Environment Variables

Configure these environment variables before running E2E tests:

```bash
# API endpoint (default: http://localhost:5050)
export API_BASE_URL="http://localhost:5050"

# API key for authentication (default: test-api-key)
export TEST_API_KEY="your-api-key-here"

# Download directory on host (maps to /app/downloads in container)
export DOWNLOAD_DIR_HOST="/path/to/downloads"

# Enable E2E tests (disabled by default)
export SKIP_E2E_TESTS="false"
```

## Running E2E Tests

### Run All E2E Tests

```bash
# Enable E2E tests
export SKIP_E2E_TESTS="false"

# Run E2E tests only
pytest tests/e2e/ -v -m e2e

# Run E2E tests without coverage (faster)
pytest tests/e2e/ -v -m e2e --no-cov
```

### Run Specific E2E Test

```bash
pytest tests/e2e/test_download_and_validate_id3.py::TestDownloadAndValidateID3::test_download_audio_and_verify_id3_tags -v --no-cov
```

### Run with Docker Compose

If using Docker Compose setup:

```bash
# Start services
docker compose up -d

# Wait for service to be ready
sleep 5

# Set environment variables
export API_BASE_URL="http://localhost:5050"
export TEST_API_KEY="test-api-key"
export DOWNLOAD_DIR_HOST="./downloads"
export SKIP_E2E_TESTS="false"

# Run E2E tests
pytest tests/e2e/ -v -m e2e --no-cov

# Stop services
docker compose down
```

## Test Coverage

The E2E tests validate:

### ✅ `test_download_audio_and_verify_id3_tags`
- Creates download task via API
- Waits for task completion
- Finds downloaded MP3 file
- Validates ID3 tags are present:
  - TIT2 (title) tag exists
  - TPE1 (artist) tag exists if title has " - " separator
  - UTF-8 encoding (encoding=3) is used
  - Tags contain expected text values

### 🔄 `test_download_with_artist_track_format` (Manual)
- Tests specific "Artist - Track" title parsing
- Validates TPE1 and TIT2 are correctly split
- Requires manual execution with specific YouTube URL

### 🔄 `test_download_with_unicode_title` (Manual)
- Tests Unicode character handling
- Validates UTF-8 encoding works correctly
- Requires manual execution with specific YouTube URL

## Example Output

Successful E2E test run:

```
tests/e2e/test_download_and_validate_id3.py::TestDownloadAndValidateID3::test_download_audio_and_verify_id3_tags
[E2E] Creating download task for: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[E2E] Task created: abc123xyz
[E2E] Waiting for task completion...
[E2E] Task completed: /files/abc123xyz/audio.mp3
[E2E] Found MP3 file: /tmp/test-downloads/abc123xyz/audio.mp3
[E2E] Reading ID3 tags from: /tmp/test-downloads/abc123xyz/audio.mp3
[E2E] ✓ TIT2 (Title): Rick Astley - Never Gonna Give You Up
[E2E] ✓ TPE1 (Artist): Rick Astley
[E2E] ✓ All ID3 tag validations passed
PASSED                                                                    [100%]
```

## Troubleshooting

### E2E Tests Skipped

```
SKIPPED [1] tests/e2e/test_download_and_validate_id3.py:70: E2E tests disabled by default
```

**Solution:** Set `SKIP_E2E_TESTS=false` environment variable.

### Connection Error

```
Request error: Connection refused
```

**Solution:** Ensure the API server is running at the configured `API_BASE_URL`.

### Authentication Error

```
Failed to create task: Unauthorized
```

**Solution:** Verify `TEST_API_KEY` is correctly set and matches a valid API key in the system.

### MP3 File Not Found

```
FileNotFoundError: No MP3 file found for task
```

**Solution:** Check that `DOWNLOAD_DIR_HOST` points to the correct download directory that maps to the container's `/app/downloads`.

### Task Timeout

```
TimeoutError: Task abc123 did not complete within 60 seconds
```

**Solution:**
- Check internet connection
- Increase timeout in `wait_for_task_completion()`
- Check API server logs for errors

## CI/CD Integration

E2E tests are disabled by default to prevent CI failures. To enable in CI:

```yaml
# .github/workflows/test.yml
- name: Run E2E Tests
  env:
    SKIP_E2E_TESTS: false
    API_BASE_URL: http://localhost:5050
    TEST_API_KEY: ${{ secrets.TEST_API_KEY }}
  run: |
    docker compose up -d
    sleep 10
    pytest tests/e2e/ -v -m e2e --no-cov
    docker compose down
```

## Contributing

When adding new E2E tests:

1. Mark with `@pytest.mark.e2e` decorator
2. Add `@pytest.mark.slow` if test takes >10 seconds
3. Clean up downloaded files in `setup_download_dir` fixture
4. Use descriptive assertion messages
5. Add test documentation to this README
