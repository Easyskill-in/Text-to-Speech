import os
import sys
import io
import re
import numpy as np
import soundfile as sf
from datetime import timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from kokoro import KPipeline


class YouTubeExtractor:
    """Extract transcript and chapters from YouTube videos."""

    def __init__(self):
        self.api = None

    def _get_api(self):
        if self.api is None:
            from youtube_transcript_api import YouTubeTranscriptApi
            self.api = YouTubeTranscriptApi()
        return self.api

    def extract_video_id(self, url_or_id):
        """Extract video ID from URL or return if already an ID."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$',
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id.strip())
            if match:
                return match.group(1)
        return None

    def get_transcript(self, url_or_id, languages=None):
        """Get transcript text from YouTube video."""
        video_id = self.extract_video_id(url_or_id)
        if not video_id:
            raise ValueError(f"Could not extract video ID from: {url_or_id}")

        api = self._get_api()

        if languages is None:
            languages = ['hi', 'en', 'hi-Latn']

        try:
            transcript = api.fetch(video_id, languages=languages)
        except Exception:
            try:
                transcript_list = api.list(video_id)
                transcript = transcript_list.find_transcript(['en'])
            except Exception as e:
                raise ValueError(f"No transcript found for video: {video_id}. Error: {e}")

        full_text = ""
        for snippet in transcript:
            full_text += snippet.text + " "

        return full_text.strip()

    def get_transcript_with_timestamps(self, url_or_id, languages=None):
        """Get transcript with timestamps for chapter splitting."""
        video_id = self.extract_video_id(url_or_id)
        if not video_id:
            raise ValueError(f"Could not extract video ID from: {url_or_id}")

        api = self._get_api()

        if languages is None:
            languages = ['hi', 'en', 'hi-Latn']

        try:
            transcript = api.fetch(video_id, languages=languages)
        except Exception:
            try:
                transcript_list = api.list(video_id)
                transcript = transcript_list.find_transcript(['en'])
            except Exception as e:
                raise ValueError(f"No transcript found for video: {video_id}. Error: {e}")

        entries = []
        for snippet in transcript:
            entries.append({
                'start': snippet.start,
                'duration': snippet.duration,
                'text': snippet.text,
            })

        return entries

    def split_into_chapters(self, entries, max_chars=500):
        """Split transcript into chapter-like segments."""
        if not entries:
            return []

        chapters = []
        current_text = ""
        current_start = 0

        for entry in entries:
            if not current_text:
                current_start = entry['start']

            current_text += entry['text'] + " "

            if len(current_text) >= max_chars:
                chapters.append({
                    'text': current_text.strip(),
                    'timestamp': str(timedelta(seconds=int(current_start))),
                    'start_seconds': current_start,
                })
                current_text = ""

        if current_text.strip():
            chapters.append({
                'text': current_text.strip(),
                'timestamp': str(timedelta(seconds=int(current_start))),
                'start_seconds': current_start,
            })

        return chapters


HINDI_WORDS = {
    'hai', 'ho', 'hum', 'aap', 'tum', 'mein', 'mera', 'teri', 'uska', 'yeh',
    'voh', 'kya', 'kaise', 'kahan', 'kyun', 'kaun', 'ab', 'yahan', 'wahan',
    'se', 'ko', 'ka', 'ki', 'ke', 'ne', 'pe', 'par', 'me', 'mai', 'main',
    'aur', 'ya', 'lekin', 'parantu', 'magar', 'kyunki', 'isliye', 'to',
    'phir', 'bhi', 'hi', 'jo', 'jaise', 'taki', 'tak', 'dusre', 'doosre',
    'ek', 'do', 'teen', 'chaar', 'paanch', 'che', 'saat', 'aath', 'nau', 'dus',
    'bada', 'chota', 'accha', 'bura', 'sundar', 'lamba', 'chota', 'motla',
    'ghar', 'kaam', 'paani', 'roti', 'duniya', 'zindagi', 'khoob',
    'shandar', 'kamaal', 'zabardast', 'dhamakedar', 'josh', 'josh mein',
    'maza', 'masti', 'dhamaal', 'dhoom', 'dhasu', 'bawaal', 'lajawab',
    'anokha', 'adbhut', 'vishwas', 'bharosa', 'ummeed', 'ichha', 'ichha',
    'soch', 'samajh', 'padhai', 'likhai', 'padhna', 'likhna', 'bolna',
    'sunna', 'dekhna', 'janna', 'aana', 'jaana', 'karna', 'hona',
    'dekho', 'suno', 'bolo', 'aao', 'jao', 'karo', 'bano', 'raho',
    'nahi', 'haan', 'bilkul', 'zaroor', 'pakka', 'definitely',
    'shuru', 'khatam', 'aage', 'peeche', 'upar', 'neeche', 'andar',
    'bahar', 'paas', 'door', 'saath', 'alag', 'ek', 'sab', 'kuch',
}

TECH_WORDS = {
    'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'ruby',
    'html', 'css', 'react', 'angular', 'vue', 'node', 'npm', 'pip',
    'django', 'flask', 'fastapi', 'spring', 'laravel', 'rails',
    'function', 'variable', 'class', 'object', 'array', 'string', 'integer',
    'boolean', 'loop', 'if', 'else', 'elif', 'return', 'import', 'from',
    'def', 'print', 'list', 'dict', 'tuple', 'set', 'int', 'float', 'str',
    'bool', 'true', 'false', 'none', 'null', 'undefined', 'try', 'except',
    'catch', 'throw', 'error', 'exception', 'async', 'await', 'yield',
    'lambda', 'map', 'filter', 'reduce', 'enumerate', 'zip', 'range',
    'len', 'append', 'extend', 'insert', 'remove', 'pop', 'index',
    'sort', 'reverse', 'copy', 'clear', 'update', 'keys', 'values', 'items',
    'get', 'set', 'has', 'is', 'in', 'not', 'and', 'or', 'for', 'while',
    'break', 'continue', 'pass', 'global', 'nonlocal', 'del', 'assert',
    'with', 'as', 'try', 'finally', 'raise', 'from', 'import',
    'file', 'open', 'read', 'write', 'close', 'seek', 'tell', 'flush',
    'input', 'output', 'stream', 'buffer', 'socket', 'server', 'client',
    'api', 'rest', 'graphql', 'http', 'https', 'url', 'request', 'response',
    'database', 'db', 'sql', 'mysql', 'postgres', 'sqlite', 'mongo', 'redis',
    'array', 'linked', 'tree', 'graph', 'stack', 'queue', 'hash', 'map',
    'algorithm', 'recursion', 'iteration', 'binary', 'search', 'sort',
    'merge', 'quick', 'heap', 'bubble', 'selection', 'insertion',
    'stack', 'heap', 'memory', 'cpu', 'gpu', 'thread', 'process',
    'compile', 'interpret', 'runtime', 'debug', 'test', 'deploy',
    'git', 'github', 'gitlab', 'bitbucket', 'docker', 'kubernetes', 'k8s',
    'aws', 'azure', 'gcp', 'cloud', 'serverless', 'lambda',
    'machine', 'learning', 'ai', 'ml', 'dl', 'neural', 'network',
    'model', 'train', 'predict', 'data', 'dataset', 'batch', 'epoch',
    'loss', 'accuracy', 'precision', 'recall', 'f1', 'score',
    'tensor', 'numpy', 'pandas', 'scipy', 'sklearn', 'pytorch', 'tensorflow',
    'keras', 'opencv', 'nlp', 'cv', 'computer', 'vision',
    'web', 'frontend', 'backend', 'fullstack', 'devops', 'ci', 'cd',
    'agile', 'scrum', 'sprint', 'backlog', 'ticket', 'story',
    'code', 'coding', 'programming', 'developer', 'engineer', 'software',
    'bug', 'fix', 'issue', 'feature', 'release', 'version', 'update',
    'package', 'library', 'framework', 'module', 'plugin', 'extension',
    'ide', 'vscode', 'vim', 'emacs', 'terminal', 'console', 'shell',
    'bash', 'powershell', 'cmd', 'command', 'script', 'automation',
    'api', 'json', 'xml', 'yaml', 'toml', 'csv', 'excel',
    'index', 'key', 'value', 'pair', 'entry', 'record', 'field',
    'type', 'interface', 'struct', 'enum', 'const', 'let', 'var',
    'scope', 'closure', 'callback', 'event', 'listener', 'handler',
    'promise', 'observable', 'stream', 'pipe', 'filter', 'map',
    'reduce', 'iterate', 'loop', 'recurse', 'stack', 'queue',
}

ROMAN_HINDI_PREFIXES = {'b', 'ch', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'y', 'z'}

ROMAN_HINDI_PATTERNS = [
    r'(?:main|mai)\s+(?:aap|tum|hum)',
    r'(?:kya|kaise|kahan|kyun|kaun)',
    r'(?:hai|ho|hoon|hain)',
    r'(?:nahi|na)',
    r'(?:aur|ya|lekin)',
    r'(?:yeh|voh|woh)',
    r'(?:ko|ka|ki|ke|se|ne|pe|me)',
    r'(?:karo|karna|karta|karti|kiye|kiya)',
    r'(?:bolo|bolna|bolta|boli)',
    r'(?:aao|aana|aata|aati)',
    r'(?:jao|jana|jata|jati)',
    r'(?:dekho|dekhna|dekhta|dekhti)',
    r'(?:padho|padhna|padhta|padhti)',
    r'(?:likho|likhna|likhta|likhti)',
    r'(?:suno|sunna|sunta|sunti)',
    r'(?:jao|jana|jata|jati)',
    r'(?:raho|rahna|rahata|rahiti)',
    r'(?:bano|banna|banta|banti)',
    r'(?:kuch|sab|yahan|wahan|tahan)',
    r'(?:ab|abhi|tab|tabhi|phir)',
    r'(?:bhi|hi|se|pe|ke|ko|ka|ki|ne|me)',
]


class HinglishDetector:
    """Word-level language detection for Hinglish text."""

    def __init__(self):
        self.roman_hindi_re = re.compile('|'.join(ROMAN_HINDI_PATTERNS))

    def detect_word(self, word):
        """Detect if a word is English or Hindi."""
        word_lower = word.lower().strip('.,!?;:"')

        if not word_lower:
            return 'en'

        if any('\u0900' <= c <= '\u097F' for c in word_lower):
            return 'hi'

        if word_lower in TECH_WORDS:
            return 'en'

        if word_lower in HINDI_WORDS:
            return 'hi'

        if self.roman_hindi_re.match(word_lower):
            return 'hi'

        if len(word_lower) <= 2:
            return 'en'

        return 'en'

    def detect_sentence_language(self, text):
        """Detect overall sentence language."""
        words = text.split()
        if not words:
            return 'en'

        hi_count = sum(1 for w in words if self.detect_word(w) == 'hi')
        en_count = sum(1 for w in words if self.detect_word(w) == 'en')

        if hi_count > en_count:
            return 'hi'
        return 'en'

    def split_by_language(self, text):
        """Split text into segments by language for Hinglish."""
        words = text.split()
        if not words:
            return [{'text': text, 'lang': 'en'}]

        segments = []
        current_segment = []
        current_lang = None

        for word in words:
            word_lang = self.detect_word(word)

            if current_lang is None:
                current_lang = word_lang
                current_segment.append(word)
            elif word_lang == current_lang:
                current_segment.append(word)
            else:
                if current_segment:
                    segments.append({
                        'text': ' '.join(current_segment),
                        'lang': current_lang,
                    })
                current_segment = [word]
                current_lang = word_lang

        if current_segment:
            segments.append({
                'text': ' '.join(current_segment),
                'lang': current_lang,
            })

        merged = []
        for seg in segments:
            if merged and merged[-1]['lang'] == seg['lang']:
                merged[-1]['text'] += ' ' + seg['text']
            else:
                merged.append(seg.copy())

        return merged


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
        'शानदार', 'कमाल', 'बहुत अच्छा', 'अड़ड',
        'ज़बरदस्त',
    }

    HINDI_SAD = {
        'दुख', 'मातम',
        'खेद', 'परेशान',
    }

    def __init__(self):
        self.sample_rate = 24000

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
            'excited': {'speed': 1.15, 'pause_ms': 250},
            'energetic': {'speed': 1.1, 'pause_ms': 300},
            'question': {'speed': 1.0, 'pause_ms': 350},
            'sad': {'speed': 0.85, 'pause_ms': 450},
            'serious': {'speed': 1.05, 'pause_ms': 350},
            'serious_warning': {'speed': 1.1, 'pause_ms': 400},
            'surprise': {'speed': 1.1, 'pause_ms': 500},
            'dramatic_pause': {'speed': 0.95, 'pause_ms': 700},
            'neutral': {'speed': 1.0, 'pause_ms': 200},
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
    VOICES = {
        'en': {
            'am_michael': 'a',
            'am_adam': 'a',
            'am_eric': 'a',
            'af_heart': 'a',
            'af_bella': 'a',
            'af_nicole': 'a',
        },
        'hi': {
            'hm_omega': 'h',
        },
        'hinglish': {
            'am_michael': 'a',
            'am_adam': 'a',
            'am_eric': 'a',
            'hm_omega': 'h',
        },
    }

    def __init__(self):
        self.pipelines = {}
        self.preprocessor = TextPreprocessor()
        self.hinglish_detector = HinglishDetector()
        self.youtube = YouTubeExtractor()
        self.sample_rate = 24000

    def _get_pipeline(self, lang_code):
        if lang_code not in self.pipelines:
            self.pipelines[lang_code] = KPipeline(lang_code=lang_code)
        return self.pipelines[lang_code]

    def generate_silence(self, duration_ms):
        num_samples = int(self.sample_rate * duration_ms / 1000)
        return np.zeros(num_samples, dtype=np.float32)

    def synthesize_segment(self, text, voice, lang_code, speed=1.0):
        pipeline = self._get_pipeline(lang_code)

        all_audio = []
        for gs, ps, audio in pipeline(text, voice=voice, speed=speed):
            all_audio.append(audio)

        if not all_audio:
            return np.array([], dtype=np.float32)

        return np.concatenate(all_audio)

    def synthesize(self, text, output_file="output.wav", lang=None, voice=None):
        if lang is None:
            lang = self.hinglish_detector.detect_sentence_language(text)

        if voice is None:
            if lang == 'hi':
                voice = 'hm_omega'
            else:
                voice = 'am_michael'

        segments = self.preprocessor.process(text)

        if not segments:
            raise ValueError("No text to synthesize")

        all_audio = []

        for i, seg in enumerate(segments):
            if seg['pause_before_ms'] > 0 and i > 0:
                silence = self.generate_silence(seg['pause_before_ms'])
                all_audio.append(silence)

            seg_text = seg['text']
            speed = seg['config'].get('speed', 1.0)

            if lang == 'hinglish':
                lang_segments = self.hinglish_detector.split_by_language(seg_text)
                for sub_seg in lang_segments:
                    sub_text = sub_seg['text']
                    sub_lang = sub_seg['lang']

                    if sub_lang == 'hi':
                        sub_voice = 'hm_omega'
                        sub_pipeline_lang = 'h'
                    else:
                        sub_voice = 'am_michael'
                        sub_pipeline_lang = 'a'

                    try:
                        audio = self.synthesize_segment(
                            sub_text, sub_voice, sub_pipeline_lang, speed
                        )
                        if len(audio) > 0:
                            all_audio.append(audio)
                    except Exception as e:
                        print(f"Warning: Failed to synthesize sub-segment: {e}")
            else:
                if lang == 'hi':
                    pipeline_lang = 'h'
                else:
                    pipeline_lang = 'a'

                try:
                    audio = self.synthesize_segment(
                        seg_text, voice, pipeline_lang, speed
                    )
                    if len(audio) > 0:
                        all_audio.append(audio)
                except Exception as e:
                    print(f"Warning: Failed to synthesize segment: {e}")

            if seg['pause_after_ms'] > 0:
                silence = self.generate_silence(seg['pause_after_ms'])
                all_audio.append(silence)

        if not all_audio:
            raise ValueError("No audio generated")

        final_audio = np.concatenate(all_audio)

        sf.write(output_file, final_audio, self.sample_rate)

        return output_file, lang

    def get_available_voices(self):
        return {
            'en': list(self.VOICES['en'].keys()),
            'hi': list(self.VOICES['hi'].keys()),
            'hinglish': list(self.VOICES['hinglish'].keys()),
        }

    def play_audio(self, file_path):
        import subprocess
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
        print("\nText-to-Speech System (Kokoro TTS)")
        print("=" * 50)
        print("\nFeatures:")
        print("  - Natural pauses based on punctuation")
        print("  - Emotional expression (happy, sad, serious, etc.)")
        print("  - Hinglish support (mixed Hindi-English)")
        print("  - YouTube transcript extraction")
        print("  - Chapter-wise script splitting")
        print("  - Multiple voice options")
        print("\nUsage:")
        print("  python tts.py <text or file.txt or YouTube URL> [output_file] [lang] [voice]")
        print("\nYouTube Commands:")
        print("  python tts.py --youtube <URL> [output_folder] [lang] [voice]")
        print("  python tts.py --youtube-chapters <URL> [output_folder] [lang] [voice]")
        print("\nLanguages:")
        print("  en - English")
        print("  hi - Hindi")
        print("  hinglish - Mixed Hindi-English")
        print("\nVoices:")
        print("  en: am_michael, am_adam, am_eric, af_heart, af_bella, af_nicole")
        print("  hi: hm_omega")
        print("  hinglish: am_michael, am_adam, am_eric, hm_omega")
        print("\nExamples:")
        print("  python tts.py 'Hello world' output.wav en")
        print("  python tts.py --youtube https://youtu.be/xyz output.wav hinglish")
        print("  python tts.py --youtube-chapters https://youtu.be/xyz output/ hinglish")
        print("  python tts.py myfile.txt output.wav hinglish am_michael")
        print("\nInteractive mode:")
        print("  python tts.py --interactive")
        sys.exit(0)

    if sys.argv[1] == "--youtube":
        url = sys.argv[2] if len(sys.argv) > 2 else None
        output_file = sys.argv[3] if len(sys.argv) > 3 else "youtube_output.wav"
        lang = sys.argv[4] if len(sys.argv) > 4 else None
        voice = sys.argv[5] if len(sys.argv) > 5 else None

        if not url:
            print("Error: YouTube URL required")
            sys.exit(1)

        try:
            print(f"Extracting transcript from: {url}")
            text = tts.youtube.get_transcript(url)
            print(f"Transcript extracted ({len(text)} chars)")

            if not text:
                print("Error: Empty transcript")
                sys.exit(1)

            result_file, detected_lang = tts.synthesize(text, output_file, lang, voice)
            print(f"Generated: {result_file} (Language: {detected_lang})")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif sys.argv[1] == "--youtube-chapters":
        url = sys.argv[2] if len(sys.argv) > 2 else None
        output_dir = sys.argv[3] if len(sys.argv) > 3 else "output"
        lang = sys.argv[4] if len(sys.argv) > 4 else None
        voice = sys.argv[5] if len(sys.argv) > 5 else None

        if not url:
            print("Error: YouTube URL required")
            sys.exit(1)

        try:
            os.makedirs(output_dir, exist_ok=True)

            print(f"Extracting transcript from: {url}")
            entries = tts.youtube.get_transcript_with_timestamps(url)
            chapters = tts.youtube.split_into_chapters(entries)
            print(f"Split into {len(chapters)} chapters")

            for i, chapter in enumerate(chapters):
                chapter_file = os.path.join(output_dir, f"chapter_{i+1:02d}.wav")
                print(f"Generating chapter {i+1}/{len(chapters)} [{chapter['timestamp']}]...")
                result_file, detected_lang = tts.synthesize(chapter['text'], chapter_file, lang, voice)
                print(f"  Generated: {os.path.basename(result_file)}")

            print(f"\nAll {len(chapters)} chapters generated in: {output_dir}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif sys.argv[1] == "--interactive":
        print("\nText-to-Speech Interactive Mode (Kokoro)")
        print("=" * 50)
        print("Type 'quit' to exit, 'lang' to change language")
        print("Type 'voice' to change voice")
        available = tts.get_available_voices()
        print("Languages:", list(available.keys()))

        current_lang = "en"
        current_voice = "am_michael"
        counter = 1

        while True:
            try:
                text = input(f"\n[{current_lang}/{current_voice}] Enter text: ").strip()

                if text.lower() == 'quit':
                    break
                elif text.lower() == 'lang':
                    print("Available languages:", list(available.keys()))
                    new_lang = input("Enter language code: ").strip()
                    if new_lang in available:
                        current_lang = new_lang
                        current_voice = available[current_lang][0]
                        print(f"Language changed to: {current_lang}, Voice: {current_voice}")
                    else:
                        print("Invalid language code!")
                    continue
                elif text.lower() == 'voice':
                    voices = available.get(current_lang, [])
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
                result_file, detected_lang = tts.synthesize(text, output_file, current_lang, current_voice)
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
        voice = sys.argv[4] if len(sys.argv) > 4 else None

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

            result_file, detected_lang = tts.synthesize(text, output_file, lang, voice)
            print(f"Generated: {result_file} (Language: {detected_lang})")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
