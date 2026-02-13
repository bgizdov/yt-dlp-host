"""Integration tests for download + ID3 tag workflow"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from mutagen.mp3 import MP3

from tests.fixtures.mp3_generator import create_minimal_mp3

# Mock os.makedirs before importing YTDownloader
with patch('os.makedirs'):
    from src.yt_handler import YTDownloader
    from src.models import TaskStatus, TaskType


@pytest.mark.integration
class TestDownloadWithID3:
    """Integration tests for complete download + ID3 tag workflow"""

    @pytest.fixture
    def downloader(self):
        """Create YTDownloader instance for testing"""
        with patch('os.makedirs'):
            return YTDownloader()

    @pytest.fixture
    def mock_audio_task(self):
        """Mock task dictionary for audio download"""
        return {
            'task_id': 'test-task-123',
            'task_type': TaskType.GET_AUDIO.value,
            'url': 'https://youtube.com/watch?v=test',
            'key_name': 'test-key',
            'audio_format': 'bestaudio',
            'output_format': 'mp3',
            'status': TaskStatus.WAITING.value
        }

    @pytest.fixture
    def mock_video_task(self):
        """Mock task dictionary for video download"""
        return {
            'task_id': 'test-video-456',
            'task_type': TaskType.GET_VIDEO.value,
            'url': 'https://youtube.com/watch?v=test',
            'key_name': 'test-key',
            'video_format': 'bestvideo',
            'audio_format': 'bestaudio',
            'status': TaskStatus.WAITING.value
        }

    @pytest.fixture
    def create_mock_mp3(self, tmp_path):
        """Helper fixture to create mock MP3 file using the generator"""
        def _create(filename="audio.mp3"):
            mp3_path = str(tmp_path / filename)
            create_minimal_mp3(mp3_path)
            return mp3_path
        return _create

    @patch('src.yt_handler.yt_dlp.YoutubeDL')
    @patch('src.yt_handler.storage')
    @patch('src.yt_handler.memory_manager')
    def test_audio_download_sets_id3_tags(
        self,
        mock_memory,
        mock_storage,
        mock_ytdlp,
        downloader,
        mock_audio_task,
        create_mock_mp3,
        tmp_path
    ):
        """Test that audio download triggers ID3 tag update with correct values"""
        # Arrange
        mock_storage.load_tasks.return_value = {'test-task-123': mock_audio_task}
        mock_storage.load_keys.return_value = {'test-key': {'key': 'api-key-value', 'permissions': []}}

        # Mock memory manager
        mock_memory.check_quota.return_value = (True, "")
        mock_memory.allocate.return_value = None
        mock_memory.release.return_value = None

        # Mock yt-dlp
        mock_ydl_instance = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl_instance

        # Mock extract_info to return video title
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Test Artist - Test Track',
            'duration': 180
        }

        # Create task directory
        task_dir = tmp_path / 'test-task-123'
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create mock MP3 file in task directory
        mp3_file = str(task_dir / "audio.mp3")
        create_minimal_mp3(mp3_file)

        # Mock _get_task_dir to return our test directory
        with patch.object(downloader, '_get_task_dir', return_value=str(task_dir)):
            # Mock os.listdir to return our MP3 file
            with patch('os.listdir', return_value=['audio.mp3']):
                # Act
                downloader.download_media('test-task-123')

        # Assert - verify ID3 tags were set
        audio = MP3(str(mp3_file))
        assert audio.tags.get('TPE1') is not None, "Artist tag (TPE1) should be set"
        assert audio.tags.get('TPE1').text[0] == "Test Artist"
        assert audio.tags.get('TIT2') is not None, "Title tag (TIT2) should be set"
        assert audio.tags.get('TIT2').text[0] == "Test Track"

    @patch('src.yt_handler.yt_dlp.YoutubeDL')
    @patch('src.yt_handler.storage')
    @patch('src.yt_handler.memory_manager')
    def test_video_download_skips_id3_tags(
        self,
        mock_memory,
        mock_storage,
        mock_ytdlp,
        downloader,
        mock_video_task,
        tmp_path
    ):
        """Test that video downloads do not trigger ID3 tag updates"""
        # Arrange
        mock_storage.load_tasks.return_value = {'test-video-456': mock_video_task}
        mock_storage.load_keys.return_value = {'test-key': {'key': 'api-key', 'permissions': []}}

        # Mock memory manager
        mock_memory.check_quota.return_value = (True, "")
        mock_memory.allocate.return_value = None
        mock_memory.release.return_value = None

        # Mock yt-dlp
        mock_ydl_instance = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Video Title',
            'duration': 180
        }

        # Create task directory
        task_dir = tmp_path / 'test-video-456'
        task_dir.mkdir(parents=True, exist_ok=True)

        # Mock _get_task_dir
        with patch.object(downloader, '_get_task_dir', return_value=str(task_dir)):
            # Mock os.listdir to return video file
            with patch('os.listdir', return_value=['video.mp4']):
                # Mock _update_mp3_id3_tags to track if it's called
                with patch.object(downloader, '_update_mp3_id3_tags') as mock_update:
                    # Act
                    downloader.download_media('test-video-456')

                    # Assert - _update_mp3_id3_tags should NOT be called
                    mock_update.assert_not_called()

    @patch('src.yt_handler.yt_dlp.YoutubeDL')
    @patch('src.yt_handler.storage')
    @patch('src.yt_handler.memory_manager')
    def test_custom_filename_audio_gets_tags(
        self,
        mock_memory,
        mock_storage,
        mock_ytdlp,
        downloader,
        tmp_path
    ):
        """Test that audio with custom output filename still gets ID3 tags"""
        # Arrange
        custom_task = {
            'task_id': 'custom-task-789',
            'task_type': TaskType.GET_AUDIO.value,
            'url': 'https://youtube.com/watch?v=test',
            'key_name': 'test-key',
            'audio_format': 'bestaudio',
            'output_format': 'mp3',
            'output_filename': 'my_custom_song.mp3',
            'status': TaskStatus.WAITING.value
        }

        mock_storage.load_tasks.return_value = {'custom-task-789': custom_task}
        mock_storage.load_keys.return_value = {'test-key': {'key': 'api-key', 'permissions': []}}

        # Mock memory manager
        mock_memory.check_quota.return_value = (True, "")
        mock_memory.allocate.return_value = None
        mock_memory.release.return_value = None

        # Mock yt-dlp
        mock_ydl_instance = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            'title': 'Custom Artist - Custom Track',
            'duration': 200
        }

        # Create task directory with custom filename
        task_dir = tmp_path / 'custom-task-789'
        task_dir.mkdir(parents=True, exist_ok=True)

        mp3_file = str(task_dir / "my_custom_song.mp3")
        create_minimal_mp3(mp3_file)

        # Mock _get_task_dir
        with patch.object(downloader, '_get_task_dir', return_value=str(task_dir)):
            with patch('os.listdir', return_value=['my_custom_song.mp3']):
                # Act
                downloader.download_media('custom-task-789')

        # Assert - verify ID3 tags were set on custom filename
        audio = MP3(str(mp3_file))
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == "Custom Artist"
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "Custom Track"
