"""Unit tests for ID3 tag functionality in yt_handler.py"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, ID3NoHeaderError

from tests.fixtures.mp3_generator import create_minimal_mp3

# Mock os.makedirs before importing YTDownloader
with patch('os.makedirs'):
    from src.yt_handler import YTDownloader


@pytest.mark.unit
class TestID3Tags:
    """Unit tests for _update_mp3_id3_tags() function"""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create YTDownloader instance for testing"""
        with patch('os.makedirs'):
            return YTDownloader()

    @pytest.fixture
    def mock_mp3_file(self, tmp_path):
        """Create a mock MP3 file with valid structure and ID3 tags"""
        mp3_path = str(tmp_path / "test_audio.mp3")
        create_minimal_mp3(mp3_path)
        return mp3_path

    def test_artist_track_format_success(self, downloader, mock_mp3_file):
        """Test parsing 'artist - track' format and setting tags correctly"""
        # Arrange
        title = "The Beatles - Hey Jude"

        # Act
        downloader._update_mp3_id3_tags(mock_mp3_file, title)

        # Assert
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == "The Beatles"
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "Hey Jude"

    def test_title_only_no_separator(self, downloader, mock_mp3_file):
        """Test title without artist separator - should set title only"""
        # Arrange
        title = "Just A Title"

        # Act
        downloader._update_mp3_id3_tags(mock_mp3_file, title)

        # Assert
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "Just A Title"
        assert audio.tags.get('TPE1') is None

    def test_multiple_separators_splits_on_first(self, downloader, mock_mp3_file):
        """Test splitting on first ' - ' only when multiple separators exist"""
        # Arrange
        title = "Artist Name - Track Title - Remix"

        # Act
        downloader._update_mp3_id3_tags(mock_mp3_file, title)

        # Assert
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == "Artist Name"
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "Track Title - Remix"

    def test_whitespace_trimming(self, downloader, mock_mp3_file):
        """Test that whitespace is trimmed from artist and track names"""
        # Arrange
        title = "  Artist  -  Track  "

        # Act
        downloader._update_mp3_id3_tags(mock_mp3_file, title)

        # Assert
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == "Artist"
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "Track"

    def test_missing_file_error_handling(self, downloader, tmp_path, capsys):
        """Test graceful handling of missing file without raising exception"""
        # Arrange
        non_existent = tmp_path / "does_not_exist.mp3"

        # Act - should not raise exception
        downloader._update_mp3_id3_tags(str(non_existent), "Title")

        # Assert - check that error was logged
        captured = capsys.readouterr()
        assert "ERROR: File does not exist" in captured.out or "ERROR updating ID3 tags" in captured.out

    def test_non_mp3_file_skipped(self, downloader, tmp_path, capsys):
        """Test that non-MP3 files are skipped with appropriate logging"""
        # Arrange
        text_file = tmp_path / "test.txt"
        text_file.write_text("not an mp3")

        # Act
        downloader._update_mp3_id3_tags(str(text_file), "Title")

        # Assert
        captured = capsys.readouterr()
        assert "Skipping non-MP3 file" in captured.out

    def test_mp3_without_id3_header(self, downloader, tmp_path):
        """Test MP3 without ID3 header gets new header and tags added"""
        # Arrange - create MP3 file, then remove ID3 tags
        mp3_path = str(tmp_path / "no_id3.mp3")
        create_minimal_mp3(mp3_path)

        # Remove ID3 tags if they exist
        try:
            audio = MP3(mp3_path)
            if audio.tags:
                audio.delete()
        except Exception:
            pass

        # Act
        downloader._update_mp3_id3_tags(mp3_path, "Artist - Track")

        # Assert
        audio = MP3(mp3_path)
        assert audio.tags is not None
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == "Artist"
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "Track"

    def test_utf8_encoding_support(self, downloader, mock_mp3_file):
        """Test UTF-8 encoding for international characters (Japanese)"""
        # Arrange
        title = "日本語アーティスト - 日本語トラック"

        # Act
        downloader._update_mp3_id3_tags(mock_mp3_file, title)

        # Assert
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == "日本語アーティスト"
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "日本語トラック"
        # Encoding 3 = UTF-8
        assert audio.tags.get('TPE1').encoding == 3
        assert audio.tags.get('TIT2').encoding == 3

    def test_existing_tags_deleted_before_update(self, downloader, mock_mp3_file):
        """Test that old tags are deleted before adding new ones (no duplicates)"""
        # Arrange - set existing tags
        audio = MP3(mock_mp3_file)
        audio.tags.add(TPE1(encoding=3, text="Old Artist"))
        audio.tags.add(TIT2(encoding=3, text="Old Track"))
        audio.save()

        # Verify old tags exist
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TPE1').text[0] == "Old Artist"
        assert audio.tags.get('TIT2').text[0] == "Old Track"

        # Act - update with new tags
        downloader._update_mp3_id3_tags(mock_mp3_file, "New Artist - New Track")

        # Assert - should have exactly one of each tag with new values
        audio = MP3(mock_mp3_file)
        assert len(audio.tags.getall('TPE1')) == 1
        assert len(audio.tags.getall('TIT2')) == 1
        assert audio.tags.get('TPE1').text[0] == "New Artist"
        assert audio.tags.get('TIT2').text[0] == "New Track"

    def test_empty_string_title(self, downloader, mock_mp3_file):
        """Test empty title string edge case - should not crash"""
        # Act - should not raise exception
        downloader._update_mp3_id3_tags(mock_mp3_file, "")

        # Assert - function should complete without error
        # Note: mutagen may not save empty text tags, so we just verify no crash
        audio = MP3(mock_mp3_file)
        # If TIT2 exists, it should be empty; if it doesn't exist, that's also acceptable
        tit2 = audio.tags.get('TIT2')
        if tit2 is not None:
            assert tit2.text[0] == ""

    def test_special_characters_in_title(self, downloader, mock_mp3_file):
        """Test handling of special characters and emojis in titles"""
        # Arrange
        title = "Artist 🎵 - Track (feat. Guest) [2024]"

        # Act
        downloader._update_mp3_id3_tags(mock_mp3_file, title)

        # Assert
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == "Artist 🎵"
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == "Track (feat. Guest) [2024]"

    def test_very_long_title(self, downloader, mock_mp3_file):
        """Test handling of very long titles (edge case)"""
        # Arrange
        long_artist = "A" * 200
        long_track = "T" * 200
        title = f"{long_artist} - {long_track}"

        # Act
        downloader._update_mp3_id3_tags(mock_mp3_file, title)

        # Assert
        audio = MP3(mock_mp3_file)
        assert audio.tags.get('TPE1') is not None
        assert audio.tags.get('TPE1').text[0] == long_artist
        assert audio.tags.get('TIT2') is not None
        assert audio.tags.get('TIT2').text[0] == long_track
