"""Helper to create minimal valid MP3 files for testing"""
from mutagen.mp3 import MP3
from mutagen.id3 import ID3


def create_minimal_mp3(filepath):
    """
    Create a minimal valid MP3 file.

    This creates a very small MP3 file with a valid frame structure
    that mutagen can read and write ID3 tags to.
    """
    # Minimal valid MP3 frame structure
    # Based on MPEG-1 Layer III specification

    # Frame sync (11 bits all 1): 0xFFE
    # Version: MPEG 1 (2 bits): 11
    # Layer: Layer III (2 bits): 01
    # Protection: No CRC (1 bit): 1
    # = 0xFFFB (first two bytes)

    # Bitrate index: 0x9 = 128 kbps (4 bits)
    # Sample rate: 00 = 44.1 kHz (2 bits)
    # Padding: 0 (1 bit)
    # Private: 0 (1 bit)
    # = 0x90

    # Channel mode: Stereo (2 bits): 00
    # Mode extension: 00 (2 bits)
    # Copyright: 0 (1 bit)
    # Original: 0 (1 bit)
    # Emphasis: 00 (2 bits)
    # = 0x00

    # Create multiple frames for a valid MP3 file
    frame_header = bytes([0xFF, 0xFB, 0x90, 0x00])

    # Frame size at 128 kbps, 44.1 kHz is 417 bytes
    # Fill with zero data
    frame_data = b'\x00' * 413  # 417 - 4 (header)

    full_frame = frame_header + frame_data

    # Write 10 frames (about 0.25 seconds of "silence")
    with open(filepath, 'wb') as f:
        for _ in range(10):
            f.write(full_frame)

    # Add ID3 tags
    try:
        audio = MP3(filepath)
        audio.add_tags()
        audio.save()
    except Exception:
        # If mutagen can't read it, that's OK for test purposes
        pass

    return filepath
