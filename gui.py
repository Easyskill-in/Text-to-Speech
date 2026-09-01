import os
import sys
import io
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import numpy as np
import soundfile as sf
from kokoro import KPipeline


HINDI_WORDS = {
    'hai', 'ho', 'hum', 'aap', 'tum', 'mein', 'mera', 'teri', 'uska', 'yeh',
    'voh', 'kya', 'kaise', 'kahan', 'kyun', 'kaun', 'ab', 'yahan', 'wahan',
    'se', 'ko', 'ka', 'ki', 'ke', 'ne', 'pe', 'par', 'me', 'mai', 'main',
    'aur', 'ya', 'lekin', 'parantu', 'magar', 'kyunki', 'isliye', 'to',
    'phir', 'bhi', 'hi', 'jo', 'jaise', 'taki', 'tak', 'dusre', 'doosre',
    'ek', 'do', 'teen', 'chaar', 'paanch', 'che', 'saat', 'aath', 'nau', 'dus',
    'bada', 'chota', 'accha', 'bura', 'sundar', 'ghar', 'kaam', 'paani',
    'duniya', 'zindagi', 'shandar', 'kamaal', 'zabardast', 'dhamakedar',
    'maza', 'masti', 'dhamaal', 'dhasu', 'bawaal', 'lajawab',
    'padhai', 'likhai', 'padhna', 'likhna', 'bolna', 'sunna', 'dekhna',
    'janna', 'aana', 'jaana', 'karna', 'hona',
    'dekho', 'suno', 'bolo', 'aao', 'jao', 'karo', 'bano', 'raho',
    'nahi', 'haan', 'bilkul', 'zaroor', 'pakka',
    'shuru', 'khatam', 'aage', 'peeche', 'upar', 'neeche', 'andar',
    'bahar', 'paas', 'door', 'saath', 'alag', 'sab', 'kuch',
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
    r'(?:raho|rahna|rahata|rahiti)',
    r'(?:bano|banna|banta|banti)',
    r'(?:kuch|sab|yahan|wahan|tahan)',
    r'(?:ab|abhi|tab|tabhi|phir)',
    r'(?:bhi|hi|se|pe|ke|ko|ka|ki|ne|me)',
]


class HinglishDetector:
    def __init__(self):
        self.roman_hindi_re = re.compile('|'.join(ROMAN_HINDI_PATTERNS))

    def detect_word(self, word):
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
        return 'en'

    def detect_sentence_language(self, text):
        words = text.split()
        if not words:
            return 'en'
        hi_count = sum(1 for w in words if self.detect_word(w) == 'hi')
        en_count = sum(1 for w in words if self.detect_word(w) == 'en')
        if hi_count > en_count:
            return 'hi'
        return 'en'

    def split_by_language(self, text):
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
        'heartbreaking', 'painful', 'suffer', 'terrible', 'horrible',
        'awful', 'dreadful', 'miserable', 'depressed', 'gloomy',
    }
    SERIOUS_WORDS = {
        'warning', 'caution', 'important', 'critical', 'urgent', 'danger',
        'alert', 'attention', 'mandatory', 'required', 'must', 'necessary',
        'essential', 'vital', 'crucial', 'severe', 'strict', 'immediately',
    }
    SURPRISE_WORDS = {
        'wait', 'really', 'what', 'seriously', 'actually', 'literally',
        'unbelievable', 'impossible', 'insane', 'crazy', 'shocking',
    }
    HINDI_EXCITED = {'शानदार', 'कमाल', 'बहुत अच्छा', 'ज़बरदस्त'}
    HINDI_SAD = {'दुख', 'मातम', 'खेद', 'परेशान'}
    sample_rate = 24000

    def detect_emotion(self, sentence):
        text_lower = sentence.lower().strip()
        has_exclaim = '!' in text_lower
        has_question = '?' in text_lower
        has_ellipsis = '...' in text_lower
        words = set(text_lower.split())
        hindi_words = set(re.findall(r'[\u0900-\u097F]+', sentence))

        excited_score = len(words & self.EXCITED_WORDS) + len(hindi_words & self.HINDI_EXCITED)
        sad_score = len(words & self.SAD_WORDS) + len(hindi_words & self.HINDI_SAD)
        serious_score = len(words & self.SERIOUS_WORDS)

        if has_ellipsis: return 'dramatic_pause'
        if serious_score > 0 and has_exclaim: return 'serious_warning'
        if excited_score > 0 and has_exclaim: return 'excited'
        if has_exclaim: return 'energetic'
        if has_question: return 'question'
        if sad_score > 0: return 'sad'
        if serious_score > 0: return 'serious'
        return 'neutral'

    def get_emotion_config(self, emotion):
        configs = {
            'excited': {'speed': 1.15, 'pause_ms': 250},
            'energetic': {'speed': 1.1, 'pause_ms': 300},
            'question': {'speed': 1.0, 'pause_ms': 350},
            'sad': {'speed': 0.85, 'pause_ms': 450},
            'serious': {'speed': 1.05, 'pause_ms': 350},
            'serious_warning': {'speed': 1.1, 'pause_ms': 400},
            'dramatic_pause': {'speed': 0.95, 'pause_ms': 700},
            'neutral': {'speed': 1.0, 'pause_ms': 200},
        }
        return configs.get(emotion, configs['neutral'])

    def split_sentences(self, text):
        text = text.strip()
        if not text: return []
        paragraphs = re.split(r'\n\s*\n', text)
        parts = []
        for p_idx, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph: continue
            sents = re.split(r'(?<=[.!?])\s+', paragraph)
            for s_idx, sent in enumerate(sents):
                sent = sent.strip()
                if not sent: continue
                parts.append({'text': sent, 'is_first': p_idx == 0 and s_idx == 0, 'is_last': False})
        if parts: parts[-1]['is_last'] = True
        return parts

    def process(self, text):
        sentences = self.split_sentences(text)
        segments = []
        for i, sent_info in enumerate(sentences):
            sent_text = sent_info['text']
            emotion = self.detect_emotion(sent_text)
            config = self.get_emotion_config(emotion)
            pause_after = config['pause_ms']
            if sent_info['is_last']: pause_after = 0
            pause_before = 0 if sent_info['is_first'] else config['pause_ms']
            segments.append({
                'text': sent_text, 'emotion': emotion, 'config': config,
                'pause_before_ms': pause_before, 'pause_after_ms': pause_after,
            })
        return segments


class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Generator - Kokoro TTS")
        self.root.geometry("900x750")
        self.root.minsize(800, 650)

        self.bg_color = "#1e1e2e"
        self.card_color = "#2a2a3e"
        self.accent_color = "#7c3aed"
        self.accent_hover = "#6d28d9"
        self.text_color = "#e2e8f0"
        self.muted_color = "#94a3b8"
        self.success_color = "#22c55e"
        self.border_color = "#3b3b54"

        self.root.configure(bg=self.bg_color)

        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(self.output_dir, exist_ok=True)

        self.voices_map = {
            "en": {
                "Michael (Male)": ("am_michael", "a"),
                "Adam (Male)": ("am_adam", "a"),
                "Eric (Male)": ("am_eric", "a"),
                "Heart (Female)": ("af_heart", "a"),
                "Bella (Female)": ("af_bella", "a"),
                "Nicole (Female)": ("af_nicole", "a"),
            },
            "hi": {
                "Omega (Male)": ("hm_omega", "h"),
            },
            "hinglish": {
                "Michael + Omega": ("am_michael", "hinglish"),
            },
        }

        self.pipelines = {}
        self.preprocessor = TextPreprocessor()
        self.hinglish_detector = HinglishDetector()
        self.sample_rate = 24000

        self.build_ui()

    def _get_pipeline(self, lang_code):
        if lang_code not in self.pipelines:
            self.pipelines[lang_code] = KPipeline(lang_code=lang_code)
        return self.pipelines[lang_code]

    def build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 20, "bold"))
        style.configure("Sub.TLabel", background=self.bg_color, foreground=self.muted_color, font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=self.card_color, foreground=self.muted_color, font=("Segoe UI", 9))
        style.configure("Success.TLabel", background=self.card_color, foreground=self.success_color, font=("Segoe UI", 9, "bold"))

        style.configure("Accent.TButton", background=self.accent_color, foreground="white",
                        font=("Segoe UI", 11, "bold"), padding=(20, 10))
        style.map("Accent.TButton", background=[("active", self.accent_hover)])

        style.configure("Secondary.TButton", background=self.border_color, foreground=self.text_color,
                        font=("Segoe UI", 9), padding=(10, 6))
        style.map("Secondary.TButton", background=[("active", self.accent_color)])

        style.configure("TCombobox", fieldbackground=self.card_color, background=self.card_color,
                        foreground=self.text_color, selectbackground=self.accent_color)
        style.configure("TCombobox", font=("Segoe UI", 10))

        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="AI Voice Generator", style="Header.TLabel").pack(anchor="w")
        ttk.Label(main, text="Powered by Kokoro TTS - English, Hindi & Hinglish support", style="Sub.TLabel").pack(anchor="w", pady=(0, 15))

        top_row = ttk.Frame(main, style="Card.TFrame")
        top_row.pack(fill=tk.X, pady=(0, 10))

        lang_frame = ttk.Frame(top_row, style="Card.TFrame", padding=10)
        lang_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(lang_frame, text="Language", style="Card.TLabel").pack(anchor="w")
        self.lang_var = tk.StringVar(value="en")
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var,
                                        values=["en", "hi", "hinglish"], state="readonly", width=15)
        self.lang_combo.pack(fill=tk.X, pady=(5, 0))
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_lang_change)

        voice_frame = ttk.Frame(top_row, style="Card.TFrame", padding=10)
        voice_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(voice_frame, text="Voice", style="Card.TLabel").pack(anchor="w")
        self.voice_var = tk.StringVar(value="Michael (Male)")
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var,
                                         values=list(self.voices_map["en"].keys()), state="readonly", width=20)
        self.voice_combo.pack(fill=tk.X, pady=(5, 0))

        out_frame = ttk.Frame(top_row, style="Card.TFrame", padding=10)
        out_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Label(out_frame, text="Output Folder", style="Card.TLabel").pack(anchor="w")
        out_row = ttk.Frame(out_frame, style="Card.TFrame")
        out_row.pack(fill=tk.X, pady=(5, 0))
        self.out_var = tk.StringVar(value=self.output_dir)
        self.out_entry = ttk.Entry(out_row, textvariable=self.out_var, font=("Segoe UI", 9))
        self.out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_row, text="Browse", style="Secondary.TButton",
                   command=self.browse_output).pack(side=tk.RIGHT, padx=(5, 0))

        text_card = ttk.Frame(main, style="Card.TFrame", padding=15)
        text_card.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        text_header = ttk.Frame(text_card, style="Card.TFrame")
        text_header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(text_header, text="Enter your text", style="Card.TLabel",
                  font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        ttk.Button(text_header, text="Load .txt File", style="Secondary.TButton",
                   command=self.load_text_file).pack(side=tk.RIGHT)

        self.text_input = tk.Text(text_card, wrap=tk.WORD, font=("Segoe UI", 11),
                                   bg="#1e1e2e", fg=self.text_color, insertbackground=self.text_color,
                                   selectbackground=self.accent_color, relief=tk.FLAT,
                                   padx=12, pady=10, height=12)
        self.text_input.pack(fill=tk.BOTH, expand=True)
        self.text_input.insert("1.0", "Hello, how are you today?\nI hope everything is going well!")

        scrollbar = ttk.Scrollbar(self.text_input, command=self.text_input.yview)
        self.text_input.configure(yscrollcommand=scrollbar.set)

        btn_row = ttk.Frame(main, style="Card.TFrame")
        btn_row.pack(fill=tk.X, pady=(0, 10))

        self.generate_btn = ttk.Button(btn_row, text="Generate Speech", style="Accent.TButton",
                                        command=self.generate_speech)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.play_btn = ttk.Button(btn_row, text="Play Last", style="Secondary.TButton",
                                    command=self.play_last)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.folder_btn = ttk.Button(btn_row, text="Open Output Folder", style="Secondary.TButton",
                                      command=self.open_output_folder)
        self.folder_btn.pack(side=tk.LEFT)

        self.status_label = ttk.Label(btn_row, text="Ready", style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT)

        self.progress = ttk.Progressbar(main, mode='indeterminate')

        self.last_output = None

    def on_lang_change(self, event=None):
        lang = self.lang_var.get()
        voices = list(self.voices_map[lang].keys())
        self.voice_combo['values'] = voices
        self.voice_var.set(voices[0])

    def browse_output(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir)
        if folder:
            self.out_var.set(folder)
            self.output_dir = folder

    def load_text_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", content)
                self.status_label.config(text=f"Loaded: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file: {e}")

    def generate_filename(self):
        now = datetime.now()
        return now.strftime("speech_%Y%m%d_%H%M%S") + ".wav"

    def generate_speech(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text first!")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=(10, 0))
        self.progress.start()
        self.status_label.config(text="Generating speech...")

        thread = threading.Thread(target=self._generate_thread, args=(text,), daemon=True)
        thread.start()

    def _generate_thread(self, text):
        try:
            lang = self.lang_var.get()
            voice_name = self.voice_var.get()
            output_folder = self.out_var.get()

            os.makedirs(output_folder, exist_ok=True)
            output_file = os.path.join(output_folder, self.generate_filename())

            voice_id, pipeline_lang = self.voices_map[lang][voice_name]

            segments = self.preprocessor.process(text)
            if not segments:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "No text to synthesize"))
                return

            all_audio = []

            for i, seg in enumerate(segments):
                if seg['pause_before_ms'] > 0 and i > 0:
                    silence = np.zeros(int(self.sample_rate * seg['pause_before_ms'] / 1000), dtype=np.float32)
                    all_audio.append(silence)

                seg_text = seg['text']
                speed = seg['config'].get('speed', 1.0)

                if pipeline_lang == 'hinglish':
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
                            pipeline = self._get_pipeline(sub_pipeline_lang)
                            for gs, ps, audio in pipeline(sub_text, voice=sub_voice, speed=speed):
                                if len(audio) > 0:
                                    all_audio.append(audio)
                        except Exception as e:
                            print(f"Warning: sub-segment failed: {e}")
                else:
                    try:
                        pipeline = self._get_pipeline(pipeline_lang)
                        for gs, ps, audio in pipeline(seg_text, voice=voice_id, speed=speed):
                            if len(audio) > 0:
                                all_audio.append(audio)
                    except Exception as e:
                        print(f"Warning: segment failed: {e}")

                if seg['pause_after_ms'] > 0:
                    silence = np.zeros(int(self.sample_rate * seg['pause_after_ms'] / 1000), dtype=np.float32)
                    all_audio.append(silence)

            if not all_audio:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "No audio generated"))
                return

            final_audio = np.concatenate(all_audio)
            sf.write(output_file, final_audio, self.sample_rate)

            self.last_output = output_file
            filename = os.path.basename(output_file)
            self.root.after(0, lambda: self._on_complete(filename))

        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_complete(self, filename):
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Generated: {filename}")
        messagebox.showinfo("Done!", f"Speech generated!\n\nFile: {filename}\nFolder: {self.output_dir}")

    def _on_error(self, error):
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Error occurred")
        messagebox.showerror("Error", f"Generation failed:\n{error}")

    def play_last(self):
        if self.last_output and os.path.exists(self.last_output):
            if sys.platform == "win32":
                os.startfile(self.last_output)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.last_output])
            else:
                subprocess.run(["aplay", self.last_output])
        else:
            messagebox.showinfo("Info", "No audio file to play yet.\nGenerate speech first!")

    def open_output_folder(self):
        folder = self.out_var.get()
        if os.path.exists(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        else:
            messagebox.showinfo("Info", "Output folder does not exist yet.")


def main():
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
