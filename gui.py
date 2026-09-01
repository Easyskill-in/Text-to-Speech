import os
import sys
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading
import subprocess
import wave
import struct

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from piper import PiperVoice
from piper.config import SynthesisConfig


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
    HINDI_EXCITED = {'\u0936\u093E\u0928\u094D\u0926\u093E\u0930', '\u0915\u094D\u092E\u093E\u0932', '\u092c\u0939\u0941\u0924 \u0939\u0948'}
    HINDI_SAD = {'\u0926\u0941\u0903\u0915', '\u092e\u093e\u0924\u092E', '\u0916\u0947\u0926'}
    sample_rate = 22050

    def detect_emotion(self, sentence):
        text_lower = sentence.lower().strip()
        has_exclaim = '!' in text_lower
        has_question = '?' in text_lower
        has_ellipsis = '...' in text_lower
        words = set(text_lower.split())
        hindi_words = set(__import__('re').findall(r'[\u0900-\u097F]+', sentence))

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
            'excited': {'length_scale': 0.88, 'volume': 1.15, 'noise_scale': 0.667, 'pause_ms': 250},
            'energetic': {'length_scale': 0.92, 'volume': 1.1, 'noise_scale': 0.667, 'pause_ms': 300},
            'question': {'length_scale': 0.95, 'volume': 1.0, 'noise_scale': 0.667, 'pause_ms': 350},
            'sad': {'length_scale': 1.12, 'volume': 0.85, 'noise_scale': 0.667, 'pause_ms': 450},
            'serious': {'length_scale': 0.93, 'volume': 1.05, 'noise_scale': 0.667, 'pause_ms': 350},
            'serious_warning': {'length_scale': 0.85, 'volume': 1.2, 'noise_scale': 0.667, 'pause_ms': 400},
            'dramatic_pause': {'length_scale': 1.05, 'volume': 0.95, 'noise_scale': 0.667, 'pause_ms': 700},
            'neutral': {'length_scale': 1.0, 'volume': 1.0, 'noise_scale': 0.667, 'pause_ms': 200},
        }
        return configs.get(emotion, configs['neutral'])

    def split_sentences(self, text):
        import re
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
        self.root.title("AI Voice Generator")
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

        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(self.output_dir, exist_ok=True)

        self.voices = {
            "en": {
                "default (Lessac)": {
                    "model": os.path.join(self.models_dir, "en", "en_US", "lessac", "medium", "en_US-lessac-medium.onnx"),
                    "config": os.path.join(self.models_dir, "en", "en_US", "lessac", "medium", "en_US-lessac-medium.onnx.json"),
                },
                "amy": {
                    "model": os.path.join(self.models_dir, "en", "en_US", "amy", "medium", "en_US-amy-medium.onnx"),
                    "config": os.path.join(self.models_dir, "en", "en_US", "amy", "medium", "en_US-amy-medium.onnx.json"),
                },
                "libritts": {
                    "model": os.path.join(self.models_dir, "en", "en_US", "libritts_r", "medium", "en_US-libritts_r-medium.onnx"),
                    "config": os.path.join(self.models_dir, "en", "en_US", "libritts_r", "medium", "en_US-libritts_r-medium.onnx.json"),
                },
            },
            "hi": {
                "default (Pratham)": {
                    "model": os.path.join(self.models_dir, "hi", "hi_IN", "pratham", "medium", "hi_IN-pratham-medium.onnx"),
                    "config": os.path.join(self.models_dir, "hi", "hi_IN", "pratham", "medium", "hi_IN-pratham-medium.onnx.json"),
                },
                "priyamvada": {
                    "model": os.path.join(self.models_dir, "hi", "hi_IN", "priyamvada", "medium", "hi_IN-priyamvada-medium.onnx"),
                    "config": os.path.join(self.models_dir, "hi", "hi_IN", "priyamvada", "medium", "hi_IN-priyamvada-medium.onnx.json"),
                },
            },
        }

        self.loaded_voices = {}
        self.preprocessor = TextPreprocessor()
        self.sample_rate = 22050

        self.build_ui()

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
        ttk.Label(main, text="Type or paste text, choose language & voice, generate speech", style="Sub.TLabel").pack(anchor="w", pady=(0, 15))

        top_row = ttk.Frame(main, style="Card.TFrame")
        top_row.pack(fill=tk.X, pady=(0, 10))

        lang_frame = ttk.Frame(top_row, style="Card.TFrame", padding=10)
        lang_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(lang_frame, text="Language", style="Card.TLabel").pack(anchor="w")
        self.lang_var = tk.StringVar(value="en")
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var,
                                        values=list(self.voices.keys()), state="readonly", width=15)
        self.lang_combo.pack(fill=tk.X, pady=(5, 0))
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_lang_change)

        voice_frame = ttk.Frame(top_row, style="Card.TFrame", padding=10)
        voice_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(voice_frame, text="Voice", style="Card.TLabel").pack(anchor="w")
        self.voice_var = tk.StringVar(value="default (Lessac)")
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var,
                                         values=list(self.voices["en"].keys()), state="readonly", width=20)
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
        voice_list = list(self.voices[lang].keys())
        self.voice_combo['values'] = voice_list
        self.voice_var.set(voice_list[0])

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

            voice = self.load_voice(lang, voice_name)
            segments = self.preprocessor.process(text)

            if not segments:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "No text to synthesize"))
                return

            all_samples = []
            sample_width = 2
            channels = 1
            rate = self.sample_rate

            for i, seg in enumerate(segments):
                if seg['pause_before_ms'] > 0 and i > 0:
                    silence = [0] * int(self.sample_rate * seg['pause_before_ms'] / 1000)
                    all_samples.extend(silence)

                syn_config = SynthesisConfig(
                    length_scale=seg['config'].get('length_scale', 1.0),
                    noise_scale=seg['config'].get('noise_scale', 0.667),
                    volume=seg['config'].get('volume', 1.0),
                )

                import io as _io
                buf = _io.BytesIO()
                with wave.open(buf, 'wb') as w:
                    voice.synthesize_wav(seg['text'], w, syn_config=syn_config)

                buf.seek(0)
                with wave.open(buf, 'rb') as w:
                    frames = w.readframes(w.getnframes())
                    sw = w.getsampwidth()
                    ch = w.getnchannels()
                    rt = w.getframerate()

                if sw == 2:
                    fmt = f"<{len(frames) // 2}h"
                    samples = list(struct.unpack(fmt, frames))
                else:
                    samples = list(struct.unpack(f"<{len(frames)}b", frames))

                all_samples.extend(samples)
                rate = rt
                channels = ch
                sample_width = sw

                if seg['pause_after_ms'] > 0:
                    silence = [0] * int(self.sample_rate * seg['pause_after_ms'] / 1000)
                    all_samples.extend(silence)

            if sample_width == 2:
                max_val = 32767
                fmt = f"<{len(all_samples)}h"
            else:
                max_val = 127
                fmt = f"<{len(all_samples)}b"

            clamped = [max(-max_val, min(max_val, int(s))) for s in all_samples]
            audio_data = struct.pack(fmt, *clamped)

            with wave.open(output_file, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(rate)
                wav_file.writeframes(audio_data)

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

    def load_voice(self, lang, variant):
        key = f"{lang}_{variant}"
        if key not in self.loaded_voices:
            voice_config = self.voices.get(lang, {}).get(variant)
            if not voice_config:
                raise ValueError(f"Voice not available: {variant}")
            if not os.path.exists(voice_config["model"]):
                raise FileNotFoundError(f"Model not found: {voice_config['model']}")
            self.loaded_voices[key] = PiperVoice.load(voice_config["model"], voice_config["config"])
        return self.loaded_voices[key]

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
