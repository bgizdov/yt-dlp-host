"""Shared pytest fixtures for all tests"""
import pytest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from mutagen.mp3 import MP3


# Mock config before any imports
@pytest.fixture(scope="session", autouse=True)
def mock_storage_at_import():
    """Mock storage config before yt_handler is imported"""
    # Create a temporary directory for the session
    tmpdir = tempfile.mkdtemp()

    # Mock the config.storage module
    mock_storage = MagicMock()
    mock_storage.DOWNLOAD_DIR = tmpdir

    # Patch before any imports
    with patch.dict('sys.modules', {'config': MagicMock(storage=mock_storage)}):
        yield tmpdir


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def create_mp3_file():
    """Factory fixture to create valid MP3 files with or without ID3 tags

    Usage:
        mp3_path = create_mp3_file('/path/to/file.mp3', with_tags=True)
    """
    def _create(path, with_tags=True):
        # Create minimal valid MP3 file
        # MP3 frame header: 0xFFFB (MPEG-1 Layer 3, 128 kbps, 44.1 kHz)
        mp3_data = b'\xff\xfb' + b'\x00' * 1000

        with open(path, 'wb') as f:
            f.write(mp3_data)

        if with_tags:
            audio = MP3(path)
            audio.add_tags()
            audio.save()

        return path

    return _create


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch, tmp_path):
    """Reset environment for each test to prevent side effects"""
    # Prevent tests from writing to production directories
    test_download_dir = str(tmp_path / "test-downloads")
    os.makedirs(test_download_dir, exist_ok=True)
    monkeypatch.setenv('DOWNLOAD_DIR', test_download_dir)
