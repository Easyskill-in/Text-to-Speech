import os
import sys
import wave
import struct
import subprocess
import io
import re
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from piper import PiperVoice
from piper.config import SynthesisConfig


class TextPreprocessor:
    """Analyzes text and splits into segments with emotion and pause info."""

    EXCITED_WORDS = {
        'wow', 'amazing', 'incredible', 'awesome', 'fantastic', 'great',
        'wonderful', 'love', 'excited', 'brilliant', 'excellent', 'superb',
        'unbelievable', 'perfect', 'best', 'yay', 'hurray', 'celebrate',
        'congratulations', 'congrats', 'hooray', 'yes', 'absolutely',
        'definitely', 'certainly', 'obviously', 'clearly',
    }

    SAD_WORDS = {
        'unfortunately', 'sadly', 'sorry', 'regret', 'loss', 'lost',
        'failed', 'failure', 'disappointed', 'disappointing', 'tragic',
        'heartbreaking', 'mourn', 'grief', 'sorrow', 'painful', 'suffer',
        'terrible', 'horrible', 'awful', 'dreadful', 'miserable',
        'depressed', 'depressing', 'gloomy', 'bleak', 'hopeless',
    }

    SERIOUS_WORDS = {
        'warning', 'caution', 'important', 'critical', 'urgent', 'danger',
        'alert', 'attention', 'notice', 'mandatory', 'required', 'must',
        'necessary', 'essential', 'vital', 'crucial', 'severe', 'strict',
        'forbidden', 'prohibited', 'immediately', 'emergency',
    }

    SURPRISE_WORDS = {
        'wait', 'really', 'what', 'how', 'seriously', 'actually',
        'literally', 'unbelievable', 'impossible', 'insane', 'crazy',
        'shocking', 'astonishing', 'stunning', 'speechless',
    }

    HINDI_EXCITED = {
        '\u0936\u093E\u0928\u094D\u0926\u093E\u0930', '\u0915\u094D\u092E\u093E\u0932',
        '\u092C\u0939\u0941\u0924 \u0939\u0948', '\u0905\u0921\u093C\u094D\u0921',
        '\u091c\u093c\u0930\u094D\u0926\u093E\u0938\u094D\u0924',
    }

    HINDI_SAD = {
        '\u0926\u0941\u0903\u0915', '\u092e\u093e\u0924\u092E',
        '\u0916\u0947\u0926', '\u092a\u0930\u0947\u0936\u093E\u0928',
    }

    def __init__(self):
        self.sample_rate = 22050

    def detect_emotion(self, sentence):
        text_lower = sentence.lower().strip()
        has_exclaim = '!' in text_lower
        has_question = '?' in text_lower
        has_ellipsis = '...' in text_lower

        words = set(re.findall(r'\b\w+\b', text_lower))
        hindi_words = set(re.findall(r'[\u0900-\u097F]+', sentence))

        excited_score = len(words & self.EXCITED_WORDS) + len(hindi_words & self.HINDI_EXCITED)
        sad_score = len(words & self.SAD_WORDS) + len(hindi_words & self.HINDI_SAD)
        serious_score = len(words & self.SERIOUS_WORDS)
        surprise_score = len(words & self.SURPRISE_WORDS)

        if has_ellipsis:
            return 'dramatic_pause'
        if serious_score > 0 and has_exclaim:
            return 'serious_warning'
        if excited_score > 0 and has_exclaim:
            return 'excited'
        if has_exclaim and excited_score > 0:
            return 'excited'
        if has_exclaim:
            return 'energetic'
        if has_question:
            return 'question'
        if sad_score > 0:
            return 'sad'
        if serious_score > 0:
            return 'serious'
        if surprise_score > 0:
            return 'surprise'

        return 'neutral'

    def get_emotion_config(self, emotion):
        configs = {
            'excited': {
                'length_scale': 0.88,
                'volume': 1.15,
                'noise_scale': 0.667,
                'pause_ms': 250,
            },
            'energetic': {
                'length_scale': 0.92,
                'volume': 1.1,
                'noise_scale': 0.667,
                'pause_ms': 300,
            },
            'question': {
                'length_scale': 0.95,
                'volume': 1.0,
                'noise_scale': 0.667,
                'pause_ms': 350,
            },
            'sad': {
                'length_scale': 1.12,
                'volume': 0.85,
                'noise_scale': 0.667,
                'pause_ms': 450,
            },
            'serious': {
                'length_scale': 0.93,
                'volume': 1.05,
                'noise_scale': 0.667,
                'pause_ms': 350,
            },
            'serious_warning': {
                'length_scale': 0.85,
                'volume': 1.2,
                'noise_scale': 0.667,
                'pause_ms': 400,
            },
            'surprise': {
                'length_scale': 0.9,
                'volume': 1.1,
                'noise_scale': 0.667,
                'pause_ms': 500,
            },
            'dramatic_pause': {
                'length_scale': 1.05,
                'volume': 0.95,
                'noise_scale': 0.667,
                'pause_ms': 700,
            },
            'neutral': {
                'length_scale': 1.0,
                'volume': 1.0,
                'noise_scale': 0.667,
                'pause_ms': 200,
            },
        }
        return configs.get(emotion, configs['neutral'])

    def split_sentences(self, text):
        text = text.strip()
        if not text:
            return []

        parts = []
        paragraphs = re.split(r'\n\s*\n', text)

        for p_idx, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            sents = re.split(r'(?<=[.!?।])\s+', paragraph)

            for s_idx, sent in enumerate(sents):
                sent = sent.strip()
                if not sent:
                    continue

                is_heading = (
                    sent.startswith('#')
                    or sent.isupper()
                    or (len(sent) < 60 and not sent.endswith(('.', '!', '?', '।')))
                )

                parts.append({
                    'text': sent,
                    'is_heading': is_heading,
                    'is_first': p_idx == 0 and s_idx == 0,
                    'is_last': False,
                })

        if parts:
            parts[-1]['is_last'] = True

        return parts

    def process(self, text):
        sentences = self.split_sentences(text)
        segments = []

        for i, sent_info in enumerate(sentences):
            sent_text = sent_info['text']

            emotion = self.detect_emotion(sent_text)
            config = self.get_emotion_config(emotion)

            pause_after = config['pause_ms']

            if sent_info['is_heading']:
                pause_after = max(pause_after, 500)

            if sent_info['is_first']:
                pause_before = 0
            elif sent_info['is_heading']:
                pause_before = 400
            else:
                pause_before = config['pause_ms']

            if sent_info['is_last']:
                pause_after = 0

            segments.append({
                'text': sent_text,
                'emotion': emotion,
                'config': config,
                'pause_before_ms': pause_before,
                'pause_after_ms': pause_after,
            })

        return segments


class TextToSpeech:
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        self.sample_rate = 22050

        self.voices = {
            "en": {
                "default": {
                    "model": os.path.join(models_dir, "en", "en_US", "lessac", "medium", "en_US-lessac-medium.onnx"),
                    "config": os.path.join(models_dir, "en", "en_US", "lessac", "medium", "en_US-lessac-medium.onnx.json"),
                },
                "amy": {
                    "model": os.path.join(models_dir, "en", "en_US", "amy", "medium", "en_US-amy-medium.onnx"),
                    "config": os.path.join(models_dir, "en", "en_US", "amy", "medium", "en_US-amy-medium.onnx.json"),
                },
                "libritts": {
                    "model": os.path.join(models_dir, "en", "en_US", "libritts_r", "medium", "en_US-libritts_r-medium.onnx"),
                    "config": os.path.join(models_dir, "en", "en_US", "libritts_r", "medium", "en_US-libritts_r-medium.onnx.json"),
                },
            },
            "hi": {
                "default": {
                    "model": os.path.join(models_dir, "hi", "hi_IN", "pratham", "medium", "hi_IN-pratham-medium.onnx"),
                    "config": os.path.join(models_dir, "hi", "hi_IN", "pratham", "medium", "hi_IN-pratham-medium.onnx.json"),
                },
                "priyamvada": {
                    "model": os.path.join(models_dir, "hi", "hi_IN", "priyamvada", "medium", "hi_IN-priyamvada-medium.onnx"),
                    "config": os.path.join(models_dir, "hi", "hi_IN", "priyamvada", "medium", "hi_IN-priyamvada-medium.onnx.json"),
                },
            },
        }
        self.loaded_voices = {}
        self.preprocessor = TextPreprocessor()

    def detect_language(self, text):
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        total_chars = len(text.strip())
        if total_chars == 0:
            return "en"
        return "hi" if hindi_chars / total_chars > 0.3 else "en"

    def load_voice(self, lang, variant="default"):
        key = f"{lang}_{variant}"
        if key not in self.loaded_voices:
            voice_config = self.voices.get(lang, {}).get(variant)
            if not voice_config:
                voice_config = self.voices.get(lang, {}).get("default")
            if not voice_config:
                raise ValueError(f"Voice not available for language: {lang}")

            model_path = voice_config["model"]
            config_path = voice_config["config"]

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")

            self.loaded_voices[key] = PiperVoice.load(model_path, config_path)
        return self.loaded_voices[key]

    def generate_silence(self, duration_ms):
        num_samples = int(self.sample_rate * duration_ms / 1000)
        samples = [0] * num_samples
        return samples

    def synthesize_segment(self, voice, text, emotion_config):
        syn_config = SynthesisConfig(
            length_scale=emotion_config.get('length_scale', 1.0),
            noise_scale=emotion_config.get('noise_scale', 0.667),
            volume=emotion_config.get('volume', 1.0),
        )

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            voice.synthesize_wav(text, w, syn_config=syn_config)

        buf.seek(0)
        with wave.open(buf, 'rb') as w:
            frames = w.readframes(w.getnframes())
            sample_width = w.getsampwidth()
            channels = w.getnchannels()
            rate = w.getframerate()

        if sample_width == 2:
            fmt = f"<{len(frames) // 2}h"
            samples = list(struct.unpack(fmt, frames))
        else:
            samples = list(struct.unpack(f"<{len(frames)}b", frames))

        return samples, rate, channels, sample_width

    def concatenate_audio(self, all_samples, sample_width=2):
        if not all_samples:
            return b""

        if sample_width == 2:
            fmt = f"<{len(all_samples)}h"
            max_val = 32767
        else:
            fmt = f"<{len(all_samples)}b"
            max_val = 127

        clamped = []
        for s in all_samples:
            s = max(-max_val, min(max_val, s))
            clamped.append(int(s))

        return struct.pack(fmt, *clamped)

    def synthesize(self, text, output_file="output.wav", lang=None):
        if lang is None:
            lang = self.detect_language(text)

        voice = self.load_voice(lang)

        segments = self.preprocessor.process(text)

        if not segments:
            raise ValueError("No text to synthesize")

        all_samples = []
        sample_width = 2
        channels = 1
        rate = self.sample_rate

        for i, seg in enumerate(segments):
            if seg['pause_before_ms'] > 0 and i > 0:
                silence = self.generate_silence(seg['pause_before_ms'])
                all_samples.extend(silence)

            try:
                samples, seg_rate, seg_channels, seg_sw = self.synthesize_segment(
                    voice, seg['text'], seg['config']
                )
                all_samples.extend(samples)
                rate = seg_rate
                channels = seg_channels
                sample_width = seg_sw
            except Exception as e:
                print(f"Warning: Failed to synthesize segment: {e}")

            if seg['pause_after_ms'] > 0:
                silence = self.generate_silence(seg['pause_after_ms'])
                all_samples.extend(silence)

        audio_data = self.concatenate_audio(all_samples, sample_width)

        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(rate)
            wav_file.writeframes(audio_data)

        return output_file, lang

    def get_available_voices(self):
        return list(self.voices.keys())

    def play_audio(self, file_path):
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["aplay", file_path])
        except Exception as e:
            print(f"Could not play audio: {e}")


def main():
    tts = TextToSpeech()

    if len(sys.argv) < 2:
        print("\nText-to-Speech System (Enhanced Piper TTS)")
        print("=" * 50)
        print("\nFeatures:")
        print("  - Natural pauses based on punctuation")
        print("  - Emotional expression (happy, sad, serious, etc.)")
        print("  - Multiple voice options")
        print("\nUsage:")
        print("  python tts.py <text or file.txt> [output_file] [lang] [voice]")
        print("\nLanguages:")
        print("  en - English")
        print("  hi - Hindi")
        print("\nVoices:")
        print("  en: default, amy, libritts")
        print("  hi: default, priyamvada")
        print("\nExamples:")
        print("  python tts.py 'Hello world' output.wav en")
        print("  python tts.py 'Wow! This is amazing!' excited.wav en")
        print("  python tts.py myfile.txt output.wav en amy")
        print("\nInteractive mode:")
        print("  python tts.py --interactive")
        sys.exit(0)

    if sys.argv[1] == "--interactive":
        print("\nText-to-Speech Interactive Mode (Enhanced)")
        print("=" * 50)
        print("Type 'quit' to exit, 'lang' to change language")
        print("Type 'voice' to change voice")
        print("Current languages:", tts.get_available_voices())

        current_lang = "en"
        current_voice = "default"
        counter = 1

        while True:
            try:
                text = input(f"\n[{current_lang}/{current_voice}] Enter text: ").strip()

                if text.lower() == 'quit':
                    break
                elif text.lower() == 'lang':
                    print("Available languages:", tts.get_available_voices())
                    new_lang = input("Enter language code: ").strip()
                    if new_lang in tts.get_available_voices():
                        current_lang = new_lang
                        current_voice = "default"
                        print(f"Language changed to: {current_lang}")
                    else:
                        print("Invalid language code!")
                    continue
                elif text.lower() == 'voice':
                    voices = list(tts.voices.get(current_lang, {}).keys())
                    print(f"Available voices for {current_lang}:", voices)
                    new_voice = input("Enter voice name: ").strip()
                    if new_voice in voices:
                        current_voice = new_voice
                        print(f"Voice changed to: {current_voice}")
                    else:
                        print("Invalid voice name!")
                    continue
                elif not text:
                    continue

                output_file = f"output_{counter}.wav"
                result_file, detected_lang = tts.synthesize(text, output_file, current_lang)
                print(f"Generated: {result_file}")
                tts.play_audio(result_file)
                counter += 1

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    else:
        input_arg = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "output.wav"
        lang = sys.argv[3] if len(sys.argv) > 3 else None
        voice = sys.argv[4] if len(sys.argv) > 4 else "default"

        try:
            if os.path.isfile(input_arg) and input_arg.lower().endswith('.txt'):
                with open(input_arg, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                print(f"Reading from file: {input_arg}")
            else:
                text = input_arg

            if not text:
                print("Error: Empty text")
                sys.exit(1)

            result_file, detected_lang = tts.synthesize(text, output_file, lang)
            print(f"Generated: {result_file} (Language: {detected_lang})")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
