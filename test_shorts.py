import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import shorts


class GuardTests(unittest.TestCase):
    def test_missing_image_blocks_voice_and_removes_old_video(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / 'short.mp4'
            output.write_bytes(b'old')
            with patch('shorts.run') as run:
                with self.assertRaises(ValueError):
                    shorts.generate({'sentences': ['Hola']}, output)
                run.assert_not_called()
            self.assertFalse(output.exists())

    def test_invalid_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            image = Path(d) / 'bad.jpg'
            image.write_text('not an image')
            with self.assertRaises(Exception):
                shorts.validate_image(image)

    def test_silent_audio_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            audio = Path(d) / 'silent.wav'
            shorts.run('ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'anullsrc', '-t', '1', str(audio))
            with self.assertRaisesRegex(ValueError, 'silencioso'):
                shorts.validate_audio(audio)

    def test_missing_audio_blocks_render(self):
        with tempfile.TemporaryDirectory() as d:
            image = Path(d) / 'image.jpg'
            image.write_bytes(b'fixture')
            output = Path(d) / 'short.mp4'
            with patch('shorts.validate_image'), patch('shorts.run') as run:
                with self.assertRaises(ValueError):
                    shorts.generate({'sentences': ['Hola'], 'image_path': str(image)}, output)
                self.assertEqual(run.call_count, 1)
            self.assertFalse(output.exists())

    def test_subtitle_timestamp(self):
        self.assertEqual(shorts.stamp(61.125), '00:01:01,125')


if __name__ == '__main__':
    unittest.main()
