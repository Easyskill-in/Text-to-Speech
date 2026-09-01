import os
import re
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, TextClip, ColorClip
)


class VideoGenerator:
    """Generate YouTube-ready videos from text with TTS narration."""

    THEMES = {
        'dark': {
            'bg_color': (30, 30, 46),
            'text_color': (226, 232, 240),
            'accent_color': (124, 58, 237),
            'subtitle_bg': (42, 42, 62),
        },
        'light': {
            'bg_color': (255, 255, 255),
            'text_color': (30, 30, 46),
            'accent_color': (124, 58, 237),
            'subtitle_bg': (240, 240, 245),
        },
        'blue': {
            'bg_color': (15, 23, 42),
            'text_color': (226, 232, 240),
            'accent_color': (59, 130, 246),
            'subtitle_bg': (30, 41, 59),
        },
        'green': {
            'bg_color': (15, 23, 42),
            'text_color': (226, 232, 240),
            'accent_color': (34, 197, 94),
            'subtitle_bg': (30, 41, 59),
        },
        'red': {
            'bg_color': (15, 23, 42),
            'text_color': (226, 232, 240),
            'accent_color': (239, 68, 68),
            'subtitle_bg': (30, 41, 59),
        },
    }

    def __init__(self, tts_engine=None):
        self.tts = tts_engine
        self.sample_rate = 24000

    def split_into_scenes(self, text, max_chars=200):
        """Split text into scenes for video."""
        paragraphs = re.split(r'\n\s*\n', text)
        scenes = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(paragraph) <= max_chars:
                scenes.append(paragraph)
            else:
                sentences = re.split(r'(?<=[.!?।])\s+', paragraph)
                current_chunk = ""

                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= max_chars:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk.strip():
                            scenes.append(current_chunk.strip())
                        current_chunk = sentence + " "

                if current_chunk.strip():
                    scenes.append(current_chunk.strip())

        return scenes

    def create_scene_image(self, text, width=1920, height=1080, theme='dark',
                           font_size=48, scene_number=None, total_scenes=None):
        """Create a single scene image with text."""
        theme_colors = self.THEMES.get(theme, self.THEMES['dark'])

        img = Image.new('RGB', (width, height), theme_colors['bg_color'])
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
            small_font = ImageFont.truetype("arial.ttf", 24)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except OSError:
                font = ImageFont.load_default()
                small_font = font

        margin = 120
        max_text_width = width - 2 * margin

        wrapper = textwrap.TextWrapper(width=int(max_text_width / (font_size * 0.5)))
        wrapped_lines = []
        for line in text.split('\n'):
            if line.strip():
                wrapped_lines.extend(wrapper.wrap(line.strip()))
            else:
                wrapped_lines.append('')

        line_height = font_size + 12
        total_text_height = len(wrapped_lines) * line_height
        y_start = (height - total_text_height) // 2

        for i, line in enumerate(wrapped_lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_start + i * line_height

            draw.text((x, y), line, fill=theme_colors['text_color'], font=font)

        if scene_number and total_scenes:
            counter_text = f"{scene_number}/{total_scenes}"
            draw.text((width - 100, height - 50), counter_text,
                      fill=theme_colors['accent_color'], font=small_font)

        accent_y = height - 30
        draw.rectangle([(50, accent_y), (width - 50, accent_y + 4)],
                       fill=theme_colors['accent_color'])

        return img

    def create_subtitle_image(self, text, width=1920, height=200, theme='dark'):
        """Create subtitle overlay image."""
        theme_colors = self.THEMES.get(theme, self.THEMES['dark'])

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            except OSError:
                font = ImageFont.load_default()

        margin = 60
        wrapper = textwrap.TextWrapper(width=int((width - 2 * margin) / (36 * 0.5)))
        lines = wrapper.wrap(text) if text else [""]

        line_height = 44
        total_height = len(lines) * line_height
        y_start = (height - total_height) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_start + i * line_height

            draw.rounded_rectangle(
                [(x - 15, y - 5), (x + text_width + 15, y + line_height - 8)],
                radius=8,
                fill=(*theme_colors['subtitle_bg'], 200)
            )
            draw.text((x, y), line, fill=(*theme_colors['text_color'], 255), font=font)

        return img

    def generate_video(self, text, output_file="output_video.mp4", theme='dark',
                       font_size=48, lang=None, voice=None, fps=24,
                       resolution=(1920, 1080)):
        """Generate complete video with TTS narration."""
        if self.tts is None:
            raise ValueError("TTS engine not provided")

        scenes = self.split_into_scenes(text)
        if not scenes:
            raise ValueError("No scenes to generate")

        width, height = resolution
        temp_dir = os.path.join(os.path.dirname(output_file), "temp_scenes")
        os.makedirs(temp_dir, exist_ok=True)

        temp_audio = os.path.join(temp_dir, "temp_audio.wav")

        print(f"Generating TTS for {len(scenes)} scenes...")
        full_text = "\n\n".join(scenes)
        self.tts.synthesize(full_text, temp_audio, lang=lang, voice=voice)

        print("Creating scene images...")
        scene_images = []
        for i, scene_text in enumerate(scenes):
            img = self.create_scene_image(
                scene_text, width, height, theme, font_size,
                scene_number=i + 1, total_scenes=len(scenes)
            )
            img_path = os.path.join(temp_dir, f"scene_{i:04d}.png")
            img.save(img_path)
            scene_images.append(img_path)

        print("Assembling video...")
        audio_clip = AudioFileClip(temp_audio)
        total_duration = audio_clip.duration

        scene_duration = total_duration / len(scenes)

        video_clips = []
        for img_path in scene_images:
            img_clip = ImageClip(img_path).with_duration(scene_duration)
            video_clips.append(img_clip)

        video = concatenate_videoclips(video_clips, method="compose")
        video = video.with_audio(audio_clip)

        print(f"Exporting video to {output_file}...")
        video.write_videofile(
            output_file,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=4,
        )

        for img_path in scene_images:
            if os.path.exists(img_path):
                os.remove(img_path)
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

        print(f"Video generated: {output_file}")
        return output_file

    def generate_video_with_subtitles(self, text, output_file="output_video.mp4",
                                       theme='dark', font_size=48, lang=None,
                                       voice=None, fps=24, resolution=(1920, 1080)):
        """Generate video with subtitles overlay."""
        if self.tts is None:
            raise ValueError("TTS engine not provided")

        scenes = self.split_into_scenes(text)
        if not scenes:
            raise ValueError("No scenes to generate")

        width, height = resolution
        temp_dir = os.path.join(os.path.dirname(output_file), "temp_scenes")
        os.makedirs(temp_dir, exist_ok=True)

        temp_audio = os.path.join(temp_dir, "temp_audio.wav")

        print(f"Generating TTS for {len(scenes)} scenes...")
        full_text = "\n\n".join(scenes)
        self.tts.synthesize(full_text, temp_audio, lang=lang, voice=voice)

        print("Creating video with subtitles...")
        audio_clip = AudioFileClip(temp_audio)
        total_duration = audio_clip.duration
        scene_duration = total_duration / len(scenes)

        theme_colors = self.THEMES.get(theme, self.THEMES['dark'])
        bg_clip = ColorClip(size=resolution, color=theme_colors['bg_color'])
        bg_clip = bg_clip.with_duration(total_duration)

        subtitle_clips = []
        for i, scene_text in enumerate(scenes):
            start_time = i * scene_duration
            end_time = (i + 1) * scene_duration

            sub_img = self.create_subtitle_image(scene_text, width, 200, theme)
            sub_path = os.path.join(temp_dir, f"sub_{i:04d}.png")
            sub_img.save(sub_path)

            sub_clip = ImageClip(sub_path).with_duration(scene_duration)
            sub_clip = sub_clip.with_start(start_time)
            sub_clip = sub_clip.with_position(("center", height - 250))
            subtitle_clips.append(sub_clip)

        all_clips = [bg_clip] + subtitle_clips
        video = CompositeVideoClip(all_clips)
        video = video.with_audio(audio_clip)

        print(f"Exporting video to {output_file}...")
        video.write_videofile(
            output_file,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=4,
        )

        for f in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, f))
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

        print(f"Video generated: {output_file}")
        return output_file
