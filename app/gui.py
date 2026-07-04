"""
gui.py
Main tkinter GUI for Resume Optimizer Pro.

Layout (top to bottom):
  • Header banner
  • Step 1 – Upload master resume (.docx / .pdf / .txt)
  • Step 2 – Job posting (URL or paste)
  • Step 3 – OpenAI API key (optional; saved to ~/.resume_optimizer/config.json)
  • Analyze button
  • Progress bar + status label
  • Results panel (summary + Save / Reset buttons)
"""

import json
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .analyzer import analyze_resume
from .job_scraper import clean_pasted_text, get_job_description
from .resume_generator import generate_optimized_resume
from .resume_parser import parse_resume


# ---------------------------------------------------------------------------
# Theme colours
# ---------------------------------------------------------------------------

C = {
    "bg":       "#1e1e2e",
    "surface":  "#313244",
    "surface2": "#45475a",
    "primary":  "#cba6f7",   # lavender
    "secondary":"#89dceb",   # teal
    "text":     "#cdd6f4",
    "subtext":  "#a6adc8",
    "green":    "#a6e3a1",
    "red":      "#f38ba8",
    "yellow":   "#f9e2af",
    "blue":     "#89b4fa",
}

_CONFIG_PATH = Path.home() / ".resume_optimizer" / "config.json"

# Best-effort font family (falls back to Helvetica on all platforms)
_FONT: str = "Helvetica"


# ---------------------------------------------------------------------------
# Main application class
# ---------------------------------------------------------------------------

class ResumeOptimizerApp:
    """Root application window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Resume Optimizer Pro")
        self.root.geometry("920x820")
        self.root.minsize(780, 620)
        self.root.configure(bg=C["bg"])

        # State
        self.resume_path  = tk.StringVar()
        self.job_mode     = tk.StringVar(value="url")
        self.job_url      = tk.StringVar()
        self.api_key      = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0.0)
        self.status_var   = tk.StringVar(value="Ready.")

        self.analysis_results: dict | None = None
        self._queue: queue.Queue = queue.Queue()

        self._load_config()
        self._build_ui()
        self._poll_queue()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        if _CONFIG_PATH.exists():
            try:
                cfg = json.loads(_CONFIG_PATH.read_text())
                self.api_key.set(cfg.get("api_key", ""))
            except Exception:
                pass

    def _save_config(self) -> None:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_PATH.write_text(json.dumps({"api_key": self.api_key.get()}))

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Outer canvas + scrollbar so the window is scrollable on small screens
        outer = tk.Frame(self.root, bg=C["bg"])
        outer.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(outer, bg=C["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._content = tk.Frame(canvas, bg=C["bg"])
        _win = canvas.create_window((0, 0), window=self._content, anchor="nw")

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(_win, width=event.width)

        self._content.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", _on_configure)

        # Mouse-wheel scrolling
        def _scroll(event):
            delta = -1 * (event.delta // 120) if sys.platform != "darwin" else -1 * event.delta
            canvas.yview_scroll(int(delta), "units")

        canvas.bind_all("<MouseWheel>", _scroll)

        main = self._content
        pad = {"padx": 24, "pady": 10}

        # Banner
        self._build_banner(main, pad)
        # Steps
        self._build_step1(main, pad)
        self._build_step2(main, pad)
        self._build_step3(main, pad)
        # Analyse button
        self._build_action(main, pad)
        # Progress (hidden until analysis starts)
        self._build_progress(main, pad)
        # Results (hidden until analysis finishes)
        self._build_results(main, pad)

    # ── Individual sections ─────────────────────────────────────────────

    def _build_banner(self, parent, pad) -> None:
        f = tk.Frame(parent, bg=C["bg"])
        f.pack(fill=tk.X, **pad)

        tk.Label(
            f, text="🎯  Resume Optimizer Pro",
            font=(_FONT, 22, "bold"),
            fg=C["primary"], bg=C["bg"],
        ).pack(side=tk.LEFT)

        tk.Label(
            f, text="v1.0",
            font=(_FONT, 11),
            fg=C["subtext"], bg=C["bg"],
        ).pack(side=tk.LEFT, padx=(8, 0), pady=6)

        tk.Label(
            f,
            text="ATS keyword optimisation  •  powered by GPT-4o (optional)",
            font=(_FONT, 10),
            fg=C["subtext"], bg=C["bg"],
        ).pack(side=tk.RIGHT, pady=8)

    def _card(self, parent, title: str, pad: dict):
        """Return a surface-coloured card frame with a header label."""
        card = tk.Frame(parent, bg=C["surface"], relief="flat")
        card.pack(fill=tk.X, padx=pad["padx"], pady=(0, 10))

        hdr = tk.Frame(card, bg=C["surface"])
        hdr.pack(fill=tk.X, padx=14, pady=(12, 0))
        tk.Label(
            hdr, text=title,
            font=(_FONT, 12, "bold"),
            fg=C["primary"], bg=C["surface"],
        ).pack(side=tk.LEFT)

        body = tk.Frame(card, bg=C["surface"])
        body.pack(fill=tk.X, padx=14, pady=(6, 12))
        return body

    def _build_step1(self, parent, pad) -> None:
        body = self._card(parent, "📄  Step 1 – Upload Your Master Resume", pad)

        tk.Label(
            body,
            text="Accepted formats: .docx  •  .pdf  •  .txt",
            font=(_FONT, 10), fg=C["subtext"], bg=C["surface"],
        ).pack(anchor="w", pady=(0, 6))

        row = tk.Frame(body, bg=C["surface"])
        row.pack(fill=tk.X)

        self._file_lbl = tk.Label(
            row, text="No file selected",
            font=(_FONT, 10), fg=C["subtext"], bg=C["bg"],
            anchor="w", padx=8, pady=4,
        )
        self._file_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        _btn(row, "Browse…", C["primary"], self._browse_resume).pack(
            side=tk.RIGHT, padx=(6, 0))

    def _build_step2(self, parent, pad) -> None:
        body = self._card(parent, "🔗  Step 2 – Job Posting", pad)

        # Toggle row
        toggle = tk.Frame(body, bg=C["surface"])
        toggle.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            toggle, text="Input method:",
            font=(_FONT, 10), fg=C["subtext"], bg=C["surface"],
        ).pack(side=tk.LEFT, padx=(0, 8))

        for label, value in (("URL", "url"), ("Paste Text", "paste")):
            tk.Radiobutton(
                toggle, text=label,
                variable=self.job_mode, value=value,
                font=(_FONT, 10),
                fg=C["text"], bg=C["surface"],
                selectcolor=C["bg"],
                activebackground=C["surface"],
                command=self._toggle_job_mode,
            ).pack(side=tk.LEFT, padx=(0, 8))

        # URL frame
        self._url_frame = tk.Frame(body, bg=C["surface"])
        self._url_frame.pack(fill=tk.X)

        tk.Label(
            self._url_frame, text="Job posting URL:",
            font=(_FONT, 10), fg=C["subtext"], bg=C["surface"],
        ).pack(anchor="w", pady=(0, 4))

        self._url_entry = tk.Entry(
            self._url_frame,
            textvariable=self.job_url,
            font=(_FONT, 10),
            fg=C["text"], bg=C["bg"],
            insertbackground=C["text"],
            relief="flat",
        )
        self._url_entry.pack(fill=tk.X, ipady=5)
        self._url_entry.insert(0, "https://")

        # Paste frame (hidden initially)
        self._paste_frame = tk.Frame(body, bg=C["surface"])

        tk.Label(
            self._paste_frame, text="Paste job description:",
            font=(_FONT, 10), fg=C["subtext"], bg=C["surface"],
        ).pack(anchor="w", pady=(0, 4))

        self._job_text = scrolledtext.ScrolledText(
            self._paste_frame,
            font=(_FONT, 10),
            fg=C["text"], bg=C["bg"],
            insertbackground=C["text"],
            relief="flat",
            height=8, wrap=tk.WORD,
        )
        self._job_text.pack(fill=tk.X)

    def _build_step3(self, parent, pad) -> None:
        body = self._card(parent, "⚙️  Step 3 – OpenAI API Key  (Optional – enables AI rewriting)", pad)

        tk.Label(
            body,
            text=(
                "Leave blank to use basic keyword-matching mode.\n"
                "With a key, GPT-4o rewrites your resume sections to sound natural."
            ),
            font=(_FONT, 10), fg=C["subtext"], bg=C["surface"],
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        row = tk.Frame(body, bg=C["surface"])
        row.pack(fill=tk.X)

        self._api_entry = tk.Entry(
            row,
            textvariable=self.api_key,
            font=(_FONT, 10),
            fg=C["text"], bg=C["bg"],
            insertbackground=C["text"],
            relief="flat",
            show="•",
        )
        self._api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

        _btn(row, "Save Key", C["secondary"], self._save_config).pack(
            side=tk.RIGHT, padx=(6, 0))

        tk.Label(
            body,
            text="💡 Get a free key at platform.openai.com",
            font=(_FONT, 9), fg=C["blue"], bg=C["surface"],
        ).pack(anchor="w", pady=(4, 0))

    def _build_action(self, parent, pad) -> None:
        f = tk.Frame(parent, bg=C["bg"])
        f.pack(fill=tk.X, padx=pad["padx"], pady=(4, 12))

        self._analyze_btn = _btn(
            f,
            "🚀   ANALYZE  &  OPTIMIZE  RESUME",
            C["primary"],
            self._start_analysis,
            font_size=13,
            pady=14,
            padx=36,
        )
        self._analyze_btn.pack(expand=True)

    def _build_progress(self, parent, pad) -> None:
        self._progress_card = tk.Frame(parent, bg=C["surface"])

        tk.Label(
            self._progress_card, text="⏳  Analysis in progress…",
            font=(_FONT, 11, "bold"), fg=C["primary"], bg=C["surface"],
        ).pack(anchor="w", padx=14, pady=(12, 4))

        inner = tk.Frame(self._progress_card, bg=C["surface"])
        inner.pack(fill=tk.X, padx=14, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Teal.Horizontal.TProgressbar",
            troughcolor=C["bg"],
            background=C["primary"],
            bordercolor=C["surface"],
        )
        self._pbar = ttk.Progressbar(
            inner,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            style="Teal.Horizontal.TProgressbar",
        )
        self._pbar.pack(fill=tk.X, pady=(0, 6))

        bottom = tk.Frame(inner, bg=C["surface"])
        bottom.pack(fill=tk.X)

        self._status_lbl = tk.Label(
            bottom, textvariable=self.status_var,
            font=(_FONT, 10), fg=C["yellow"], bg=C["surface"],
            anchor="w",
        )
        self._status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._pct_lbl = tk.Label(
            bottom, text="0 %",
            font=(_FONT, 10, "bold"), fg=C["primary"], bg=C["surface"],
        )
        self._pct_lbl.pack(side=tk.RIGHT)

    def _build_results(self, parent, pad) -> None:
        self._results_card = tk.Frame(parent, bg=C["surface"])

        tk.Label(
            self._results_card, text="📋  Results & Summary",
            font=(_FONT, 12, "bold"), fg=C["primary"], bg=C["surface"],
        ).pack(anchor="w", padx=14, pady=(12, 4))

        self._results_text = scrolledtext.ScrolledText(
            self._results_card,
            font=(_FONT, 10),
            fg=C["text"], bg=C["bg"],
            insertbackground=C["text"],
            relief="flat",
            height=14,
            wrap=tk.WORD,
            state="disabled",
        )
        self._results_text.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))

        btn_row = tk.Frame(self._results_card, bg=C["surface"])
        btn_row.pack(fill=tk.X, padx=14, pady=(0, 12))

        self._save_btn = _btn(
            btn_row,
            "💾  Save Optimized Resume (.docx)",
            C["green"],
            self._save_resume,
            state="disabled",
        )
        self._save_btn.pack(side=tk.LEFT)

        _btn(
            btn_row,
            "🔄  Start Over",
            C["surface2"],
            self._reset,
        ).pack(side=tk.LEFT, padx=(8, 0))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _toggle_job_mode(self) -> None:
        if self.job_mode.get() == "url":
            self._paste_frame.pack_forget()
            self._url_frame.pack(fill=tk.X)
        else:
            self._url_frame.pack_forget()
            self._paste_frame.pack(fill=tk.X)

    def _browse_resume(self) -> None:
        path = filedialog.askopenfilename(
            title="Select your master resume",
            filetypes=[
                ("Supported files", "*.docx *.pdf *.txt"),
                ("Word Documents", "*.docx"),
                ("PDF Files", "*.pdf"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            self.resume_path.set(path)
            self._file_lbl.configure(
                text=f"✅  {os.path.basename(path)}", fg=C["green"])

    def _validate(self) -> bool:
        if not self.resume_path.get():
            messagebox.showerror("Missing Input", "Please select your resume file first.")
            return False
        if not os.path.exists(self.resume_path.get()):
            messagebox.showerror(
                "File Not Found",
                f"Resume file not found:\n{self.resume_path.get()}",
            )
            return False

        if self.job_mode.get() == "url":
            url = self.job_url.get().strip()
            if not url or url == "https://":
                messagebox.showerror("Missing Input", "Please enter a job posting URL.")
                return False
            if not url.startswith(("http://", "https://")):
                messagebox.showerror(
                    "Invalid URL", "Please enter a valid URL (http:// or https://).")
                return False
        else:
            if not self._job_text.get("1.0", tk.END).strip():
                messagebox.showerror(
                    "Missing Input", "Please paste the job description text.")
                return False

        return True

    def _start_analysis(self) -> None:
        if not self._validate():
            return

        self._progress_card.pack(
            fill=tk.X, padx=24, pady=(0, 10))
        self._results_card.pack_forget()

        self._analyze_btn.configure(state="disabled", text="⏳  Analyzing…")
        self.progress_var.set(0)
        self._pct_lbl.configure(text="0 %")

        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        """Background thread: parse → fetch → analyze → generate."""
        def progress(pct: float, msg: str) -> None:
            self._queue.put(("progress", pct, msg))

        try:
            progress(5, "📄 Reading resume…")
            resume_data = parse_resume(self.resume_path.get())
            progress(20, "✅ Resume loaded")

            progress(25, "🔗 Fetching job description…")
            if self.job_mode.get() == "url":
                job_text = get_job_description(self.job_url.get().strip())
            else:
                job_text = clean_pasted_text(
                    self._job_text.get("1.0", tk.END).strip())
            progress(40, "✅ Job description ready")

            api_key = self.api_key.get().strip() or None
            results = analyze_resume(
                resume_data, job_text,
                api_key=api_key,
                progress_callback=progress,
            )
            progress(75, "✅ Analysis complete")

            progress(80, "✍️  Generating optimised resume…")
            output = _output_path(self.resume_path.get())
            generate_optimized_resume(
                original_path=self.resume_path.get(),
                results=results,
                output_path=output,
            )
            results["output_path"] = output
            progress(100, "🎉 Done! Your optimised resume is ready.")

            self._queue.put(("done", results))
        except Exception as exc:  # noqa: BLE001
            self._queue.put(("error", str(exc)))

    def _poll_queue(self) -> None:
        """Drain the thread-communication queue every 100 ms."""
        try:
            while True:
                msg = self._queue.get_nowait()
                if msg[0] == "progress":
                    _, pct, text = msg
                    self.progress_var.set(pct)
                    self._pct_lbl.configure(text=f"{int(pct)} %")
                    self.status_var.set(text)
                elif msg[0] == "done":
                    self._on_done(msg[1])
                elif msg[0] == "error":
                    self._on_error(msg[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _on_done(self, results: dict) -> None:
        self.analysis_results = results
        summary = _build_summary(results)

        self._results_text.configure(state="normal")
        self._results_text.delete("1.0", tk.END)
        self._results_text.insert("1.0", summary)
        self._results_text.configure(state="disabled")

        self._results_card.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 12))
        self._save_btn.configure(state="normal")
        self._analyze_btn.configure(
            state="normal", text="🚀   ANALYZE  &  OPTIMIZE  RESUME")

    def _on_error(self, message: str) -> None:
        self._progress_card.pack_forget()
        self._analyze_btn.configure(
            state="normal", text="🚀   ANALYZE  &  OPTIMIZE  RESUME")
        messagebox.showerror(
            "Analysis Error",
            f"Something went wrong:\n\n{message}\n\n"
            "Check your inputs and try again.",
        )

    def _save_resume(self) -> None:
        if not self.analysis_results:
            return
        saved = self.analysis_results.get("output_path", "")
        if saved and os.path.exists(saved):
            if messagebox.askyesno(
                "Resume Saved",
                f"Your optimised resume was saved to:\n{saved}\n\nOpen it now?",
            ):
                _open_file(saved)
        else:
            dst = filedialog.asksaveasfilename(
                title="Save Optimised Resume",
                defaultextension=".docx",
                filetypes=[("Word Document", "*.docx")],
            )
            if dst:
                import shutil
                shutil.copy2(saved, dst)
                messagebox.showinfo("Saved", f"Saved to:\n{dst}")

    def _reset(self) -> None:
        self.resume_path.set("")
        self._file_lbl.configure(text="No file selected", fg=C["subtext"])
        self.job_url.set("https://")
        self._job_text.delete("1.0", tk.END)
        self.progress_var.set(0)
        self.status_var.set("Ready.")
        self.analysis_results = None
        self._progress_card.pack_forget()
        self._results_card.pack_forget()
        self._analyze_btn.configure(
            state="normal", text="🚀   ANALYZE  &  OPTIMIZE  RESUME")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _btn(
    parent,
    text: str,
    color: str,
    command,
    font_size: int = 10,
    pady: int = 8,
    padx: int = 16,
    state: str = "normal",
) -> tk.Button:
    return tk.Button(
        parent, text=text,
        font=(_FONT, font_size, "bold"),
        fg=C["bg"], bg=color,
        relief="flat",
        padx=padx, pady=pady,
        cursor="hand2",
        state=state,
        command=command,
        activebackground=color,
        activeforeground=C["bg"],
    )


def _output_path(original: str) -> str:
    """Derive a non-conflicting output filename in the same directory."""
    p = Path(original)
    parent, stem = p.parent, p.stem
    n = 1
    while True:
        candidate = parent / f"{stem}_optimized_{n}.docx"
        if not candidate.exists():
            return str(candidate)
        n += 1


def _open_file(path: str) -> None:
    import subprocess
    if sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    elif sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", path], check=False)


def _build_summary(results: dict) -> str:
    lines: list[str] = []
    lines += [
        "=" * 62,
        "   RESUME OPTIMIZATION SUMMARY",
        "=" * 62,
        "",
    ]

    score = results.get("match_score", 0)
    bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
    lines += [
        f"  ATS Keyword Match Score:  {score:.0f} %",
        f"  [{bar}]",
        "",
    ]

    missing = results.get("missing_keywords", [])
    present = results.get("present_keywords", [])

    if missing:
        lines.append(f"  🔍  {len(missing)} keyword(s) NOT found in your resume:")
        for kw in missing[:12]:
            lines.append(f"       •  {kw}")
        if len(missing) > 12:
            lines.append(f"       … and {len(missing) - 12} more")
        lines.append("")

    if present:
        lines.append(f"  ✅  {len(present)} keyword(s) already present:")
        for kw in present[:10]:
            lines.append(f"       •  {kw}")
        if len(present) > 10:
            lines.append(f"       … and {len(present) - 10} more")
        lines.append("")

    changes = results.get("changes_summary", [])
    if changes:
        lines.append("  ✏️   Changes applied:")
        for c in changes:
            lines.append(f"       {c}")
        lines.append("")

    if results.get("ai_used"):
        lines.append("  🤖  Full AI-powered rewrite applied via GPT-4o.")
    else:
        lines.append("  📋  Basic keyword-gap report generated.")
        lines.append("       Add an OpenAI key in Step 3 for a full AI rewrite.")

    lines.append("")
    output = results.get("output_path", "")
    if output:
        lines.append(f"  💾  Saved → {output}")
    lines.append("")
    return "\n".join(lines)
