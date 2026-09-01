import os
import sys
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from tts import TextToSpeech
from video_generator import VideoGenerator


class VideoGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Text to Video AI - YouTube Video Generator")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)

        self.bg_color = "#1e1e2e"
        self.card_color = "#2a2a3e"
        self.accent_color = "#7c3aed"
        self.accent_hover = "#6d28d9"
        self.text_color = "#e2e8f0"
        self.muted_color = "#94a3b8"
        self.success_color = "#22c55e"
        self.border_color = "#3b3b54"
        self.youtube_red = "#cc0000"

        self.root.configure(bg=self.bg_color)

        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(self.output_dir, exist_ok=True)

        self.tts = TextToSpeech()
        self.video_gen = VideoGenerator(tts_engine=self.tts)

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
                "Michael (Male)": ("am_michael", "hinglish"),
                "Adam (Male)": ("am_adam", "hinglish"),
                "Eric (Male)": ("am_eric", "hinglish"),
                "Omega (Male, Hindi)": ("hm_omega", "hinglish"),
            },
        }

        self.build_ui()

    def build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TFrame", background=self.bg_color)
        style.configure("Card.TFrame", background=self.card_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", background=self.bg_color, foreground=self.muted_color, font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=self.card_color, foreground=self.muted_color, font=("Segoe UI", 9))

        style.configure("Accent.TButton", background=self.accent_color, foreground="white",
                        font=("Segoe UI", 11, "bold"), padding=(20, 10))
        style.map("Accent.TButton", background=[("active", self.accent_hover)])

        style.configure("Secondary.TButton", background=self.border_color, foreground=self.text_color,
                        font=("Segoe UI", 9), padding=(10, 6))
        style.map("Secondary.TButton", background=[("active", self.accent_color)])

        style.configure("YouTube.TButton", background=self.youtube_red, foreground="white",
                        font=("Segoe UI", 9, "bold"), padding=(10, 6))
        style.map("YouTube.TButton", background=[("active", "#990000")])

        style.configure("TCombobox", fieldbackground=self.card_color, background=self.card_color,
                        foreground=self.text_color, selectbackground=self.accent_color)

        main = ttk.Frame(self.root, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Text to Video AI", style="Header.TLabel").pack(anchor="w")
        ttk.Label(main, text="Generate YouTube-ready videos with TTS narration", style="Sub.TLabel").pack(anchor="w", pady=(0, 15))

        settings_row = ttk.Frame(main, style="Card.TFrame")
        settings_row.pack(fill=tk.X, pady=(0, 10))

        lang_frame = ttk.Frame(settings_row, style="Card.TFrame", padding=10)
        lang_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(lang_frame, text="Language", style="Card.TLabel").pack(anchor="w")
        self.lang_var = tk.StringVar(value="hinglish")
        ttk.Combobox(lang_frame, textvariable=self.lang_var,
                     values=["en", "hi", "hinglish"], state="readonly", width=12).pack(fill=tk.X, pady=(5, 0))
        self.lang_var.trace_add("write", self._on_lang_change)

        voice_frame = ttk.Frame(settings_row, style="Card.TFrame", padding=10)
        voice_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(voice_frame, text="Voice", style="Card.TLabel").pack(anchor="w")
        self.voice_var = tk.StringVar(value="Michael (Male)")
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var,
                                         values=list(self.voices_map["hinglish"].keys()), state="readonly", width=20)
        self.voice_combo.pack(fill=tk.X, pady=(5, 0))

        theme_frame = ttk.Frame(settings_row, style="Card.TFrame", padding=10)
        theme_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(theme_frame, text="Theme", style="Card.TLabel").pack(anchor="w")
        self.theme_var = tk.StringVar(value="dark")
        ttk.Combobox(theme_frame, textvariable=self.theme_var,
                     values=["dark", "light", "blue", "green", "red"], state="readonly", width=12).pack(fill=tk.X, pady=(5, 0))

        res_frame = ttk.Frame(settings_row, style="Card.TFrame", padding=10)
        res_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Label(res_frame, text="Resolution", style="Card.TLabel").pack(anchor="w")
        self.res_var = tk.StringVar(value="1920x1080")
        ttk.Combobox(res_frame, textvariable=self.res_var,
                     values=["1920x1080", "1280x720", "3840x2160"], state="readonly", width=15).pack(fill=tk.X, pady=(5, 0))

        text_card = ttk.Frame(main, style="Card.TFrame", padding=15)
        text_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        text_header = ttk.Frame(text_card, style="Card.TFrame")
        text_header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(text_header, text="Video Script", style="Card.TLabel",
                  font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        ttk.Button(text_header, text="Load .txt File", style="Secondary.TButton",
                   command=self.load_text_file).pack(side=tk.RIGHT)

        self.text_input = tk.Text(text_card, wrap=tk.WORD, font=("Segoe UI", 11),
                                   bg="#1e1e2e", fg=self.text_color, insertbackground=self.text_color,
                                   selectbackground=self.accent_color, relief=tk.FLAT,
                                   padx=12, pady=10, height=10)
        self.text_input.pack(fill=tk.BOTH, expand=True)
        self.text_input.insert("1.0",
            "Welcome to Python Programming!\n\n"
            "Python is one of the most popular programming languages in the world.\n\n"
            "It is easy to learn and has a huge community support.\n\n"
            "Let us start with variables and data types!"
        )

        options_row = ttk.Frame(main, style="Card.TFrame", padding=10)
        options_row.pack(fill=tk.X, pady=(0, 10))

        font_frame = ttk.Frame(options_row, style="Card.TFrame", padding=5)
        font_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(font_frame, text="Font Size", style="Card.TLabel").pack(anchor="w")
        self.font_var = tk.IntVar(value=48)
        ttk.Spinbox(font_frame, from_=24, to=72, textvariable=self.font_var, width=5).pack(fill=tk.X, pady=(5, 0))

        fps_frame = ttk.Frame(options_row, style="Card.TFrame", padding=5)
        fps_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Label(fps_frame, text="FPS", style="Card.TLabel").pack(anchor="w")
        self.fps_var = tk.IntVar(value=24)
        ttk.Spinbox(fps_frame, from_=15, to=60, textvariable=self.fps_var, width=5).pack(fill=tk.X, pady=(5, 0))

        mode_frame = ttk.Frame(options_row, style="Card.TFrame", padding=5)
        mode_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Label(mode_frame, text="Video Mode", style="Card.TLabel").pack(anchor="w")
        self.mode_var = tk.StringVar(value="scenes")
        ttk.Combobox(mode_frame, textvariable=self.mode_var,
                     values=["scenes", "subtitles"], state="readonly", width=12).pack(fill=tk.X, pady=(5, 0))

        out_frame = ttk.Frame(options_row, style="Card.TFrame", padding=5)
        out_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Label(out_frame, text="Output Folder", style="Card.TLabel").pack(anchor="w")
        out_row = ttk.Frame(out_frame, style="Card.TFrame")
        out_row.pack(fill=tk.X, pady=(5, 0))
        self.out_var = tk.StringVar(value=self.output_dir)
        ttk.Entry(out_row, textvariable=self.out_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_row, text="Browse", style="Secondary.TButton",
                   command=self.browse_output).pack(side=tk.RIGHT, padx=(5, 0))

        btn_row = ttk.Frame(main, style="Card.TFrame")
        btn_row.pack(fill=tk.X, pady=(0, 5))

        self.generate_btn = ttk.Button(btn_row, text="Generate Video", style="Accent.TButton",
                                        command=self.generate_video)
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

    def _on_lang_change(self, *args):
        lang = self.lang_var.get()
        voices = list(self.voices_map[lang].keys())
        self.voice_combo['values'] = voices
        self.voice_var.set(voices[0])

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

    def browse_output(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir)
        if folder:
            self.out_var.set(folder)
            self.output_dir = folder

    def generate_video(self):
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text first!")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=(10, 0))
        self.progress.start()
        self.status_label.config(text="Generating video...")

        thread = threading.Thread(target=self._generate_thread, args=(text,), daemon=True)
        thread.start()

    def _generate_thread(self, text):
        try:
            lang = self.lang_var.get()
            voice_name = self.voice_var.get()
            theme = self.theme_var.get()
            resolution = self.res_var.get()
            font_size = self.font_var.get()
            fps = self.fps_var.get()
            mode = self.mode_var.get()
            output_folder = self.out_var.get()

            os.makedirs(output_folder, exist_ok=True)

            width, height = map(int, resolution.split('x'))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_folder, f"video_{timestamp}.mp4")

            voice_id, pipeline_lang = self.voices_map[lang][voice_name]

            self.root.after(0, lambda: self.status_label.config(text="Generating TTS audio..."))

            if mode == "subtitles":
                result = self.video_gen.generate_video_with_subtitles(
                    text, output_file, theme=theme, font_size=font_size,
                    lang=lang, voice=voice_id, fps=fps, resolution=(width, height)
                )
            else:
                result = self.video_gen.generate_video(
                    text, output_file, theme=theme, font_size=font_size,
                    lang=lang, voice=voice_id, fps=fps, resolution=(width, height)
                )

            self.last_output = result
            filename = os.path.basename(result)
            self.root.after(0, lambda: self._on_complete(filename))

        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_complete(self, filename):
        self.progress.stop()
        self.progress.pack_forget()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Generated: {filename}")
        messagebox.showinfo("Done!", f"Video generated!\n\nFile: {filename}\nFolder: {self.out_var.get()}")

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
                import subprocess
                subprocess.run(["open", self.last_output])
            else:
                import subprocess
                subprocess.run(["xdg-open", self.last_output])
        else:
            messagebox.showinfo("Info", "No video to play yet.\nGenerate a video first!")

    def open_output_folder(self):
        folder = self.out_var.get()
        if os.path.exists(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.run(["open", folder])
            else:
                import subprocess
                subprocess.run(["xdg-open", folder])
        else:
            messagebox.showinfo("Info", "Output folder does not exist yet.")


def main():
    root = tk.Tk()
    app = VideoGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
