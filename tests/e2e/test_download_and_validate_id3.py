"""End-to-end test: Download MP3 and validate ID3 tags are present"""
import os
import pytest
import time
import requests
from mutagen.mp3 import MP3
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.slow
class TestDownloadAndValidateID3:
    """E2E tests that validate ID3 tags after actual downloads"""

    # API endpoint (adjust if running on different host/port)
    BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5050')
    # Download directory (inside container it's /app/downloads)
    DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR_HOST', '/tmp/test-downloads'))

    @pytest.fixture(autouse=True)
    def setup_download_dir(self):
        """Ensure download directory exists and is clean"""
        self.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup after test
        for file in self.DOWNLOAD_DIR.glob('*.mp3'):
            try:
                file.unlink()
            except Exception:
                pass

    def wait_for_task_completion(self, task_id: str, timeout: int = 60) -> dict:
        """Poll task status until completion or timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.BASE_URL}/status/{task_id}")
                if response.status_code == 200:
                    task = response.json()
                    status = task.get('status')

                    if status == 'completed':
                        return task
                    elif status == 'error':
                        raise Exception(f"Task failed: {task.get('error')}")

                    # Still processing, wait and retry
                    time.sleep(2)
                else:
                    time.sleep(2)
            except requests.RequestException as e:
                print(f"Request error: {e}")
                time.sleep(2)

        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

    def find_downloaded_mp3(self, task: dict) -> Path:
        """Find the downloaded MP3 file based on task info"""
        file_path = task.get('file')
        if not file_path:
            raise Exception("Task has no file path")

        # file_path is like '/files/task_id/filename.mp3' or '/files/filename.mp3'
        # We need to map this to actual filesystem path
        filename = file_path.split('/')[-1]

        # Search in download directory
        mp3_files = list(self.DOWNLOAD_DIR.glob('**/*.mp3'))

        # Try to find by filename
        for mp3_file in mp3_files:
            if mp3_file.name == filename:
                return mp3_file

        # If not found by exact name, return the most recent MP3
        if mp3_files:
            return max(mp3_files, key=lambda p: p.stat().st_mtime)

        raise FileNotFoundError(f"No MP3 file found for task. Expected: {filename}")

    @pytest.mark.skipif(
        os.getenv('SKIP_E2E_TESTS', 'true').lower() == 'true',
        reason="E2E tests disabled by default (set SKIP_E2E_TESTS=false to enable)"
    )
    def test_download_audio_and_verify_id3_tags(self):
        """
        E2E Test: Download audio, extract to MP3, and validate ID3 tags

        This test requires:
        - API server running at BASE_URL
        - Valid API key configured
        - Internet connection for YouTube download
        """
        # Step 1: Create download task
        api_key = os.getenv('TEST_API_KEY', 'test-api-key')

        task_payload = {
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Short test video
            'audio_format': 'bestaudio',
            'output_format': 'mp3'
        }

        headers = {'X-API-Key': api_key}

        print(f"[E2E] Creating download task for: {task_payload['url']}")
        response = requests.post(
            f"{self.BASE_URL}/get_audio",
            json=task_payload,
            headers=headers
        )

        assert response.status_code == 200, f"Failed to create task: {response.text}"
        task_id = response.json().get('task_id')
        assert task_id, "No task_id returned"
        print(f"[E2E] Task created: {task_id}")

        # Step 2: Wait for download to complete
        print(f"[E2E] Waiting for task completion...")
        task = self.wait_for_task_completion(task_id, timeout=120)
        print(f"[E2E] Task completed: {task.get('file')}")

        # Step 3: Find the downloaded MP3 file
        mp3_file = self.find_downloaded_mp3(task)
        print(f"[E2E] Found MP3 file: {mp3_file}")

        assert mp3_file.exists(), f"MP3 file not found: {mp3_file}"
        assert mp3_file.suffix == '.mp3', f"File is not MP3: {mp3_file}"

        # Step 4: Validate ID3 tags are present
        print(f"[E2E] Reading ID3 tags from: {mp3_file}")
        audio = MP3(str(mp3_file))

        # Assert that ID3 tags exist
        assert audio.tags is not None, "MP3 file has no ID3 tags"

        # Check for TIT2 (title) tag - this should ALWAYS be present
        tit2_tag = audio.tags.get('TIT2')
        assert tit2_tag is not None, "MP3 file missing TIT2 (title) tag"

        title_text = tit2_tag.text[0] if tit2_tag.text else ""
        print(f"[E2E] ✓ TIT2 (Title): {title_text}")

        # Check for TPE1 (artist) tag - present if title has " - " separator
        tpe1_tag = audio.tags.get('TPE1')
        if tpe1_tag:
            artist_text = tpe1_tag.text[0] if tpe1_tag.text else ""
            print(f"[E2E] ✓ TPE1 (Artist): {artist_text}")
        else:
            print(f"[E2E] ℹ TPE1 (Artist) not set (title has no ' - ' separator)")

        # Validate UTF-8 encoding
        if tit2_tag:
            assert tit2_tag.encoding == 3, f"TIT2 encoding should be 3 (UTF-8), got {tit2_tag.encoding}"

        if tpe1_tag:
            assert tpe1_tag.encoding == 3, f"TPE1 encoding should be 3 (UTF-8), got {tpe1_tag.encoding}"

        print(f"[E2E] ✓ All ID3 tag validations passed")

    def test_download_with_artist_track_format(self):
        """
        E2E Test: Download a video with 'Artist - Track' title format

        This specifically tests that the title is parsed correctly and
        both TPE1 (artist) and TIT2 (track) tags are set.
        """
        pytest.skip("Manual E2E test - requires specific YouTube video with 'Artist - Track' format")

        # Example implementation:
        # 1. Find a YouTube video with title like "Artist Name - Song Title"
        # 2. Download it
        # 3. Verify TPE1 = "Artist Name"
        # 4. Verify TIT2 = "Song Title"

    def test_download_with_unicode_title(self):
        """
        E2E Test: Download a video with Unicode characters in title

        Tests that UTF-8 encoding (encoding=3) works correctly.
        """
        pytest.skip("Manual E2E test - requires specific YouTube video with Unicode title")

        # Example implementation:
        # 1. Find a YouTube video with Japanese/Chinese/Emoji in title
        # 2. Download it
        # 3. Verify tags contain correct Unicode characters
        # 4. Verify encoding=3 (UTF-8)
