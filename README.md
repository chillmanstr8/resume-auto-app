# 🎯 Resume Optimizer Pro

> **Give it your master resume + a job posting — get back an ATS-optimised Word document in seconds.**

Resume Optimizer Pro is a standalone Python desktop application that:

1. Reads your master resume (`.docx`, `.pdf`, or `.txt`)
2. Ingests the target job description (URL or pasted text)
3. Extracts ATS keywords from the job description and compares them against your resume
4. *(Optional – with an OpenAI API key)* Uses GPT-4o to rewrite resume sections so the
   missing keywords are incorporated naturally and professionally
5. Writes a brand-new `.docx` file in the **same directory** as your original,
   leaving the original untouched
6. Displays a clear summary of what changed, what was added, and your ATS match score

---

## Quick-start

### macOS / Linux

```bash
git clone https://github.com/chillmanstr8/resume-auto-app.git
cd resume-auto-app
chmod +x install.sh
./install.sh        # creates a venv and installs all deps
./run.sh            # launches the app
```

### Windows

```bat
git clone https://github.com/chillmanstr8/resume-auto-app.git
cd resume-auto-app
install.bat         # creates a venv and installs all deps
run.bat             # launches the app
```

### Manual (any platform)

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

> **Python 3.9+** and **tkinter** are required.  
> See [USER_GUIDE.md](USER_GUIDE.md) for detailed platform-specific instructions.

---

## Features

| Feature | Basic mode | AI mode (OpenAI key) |
|---|---|---|
| Parse .docx / .pdf / .txt | ✅ | ✅ |
| ATS keyword gap analysis | ✅ | ✅ |
| Match-score indicator | ✅ | ✅ |
| Keyword suggestion report | ✅ | ✅ |
| Full GPT-4o resume rewrite | — | ✅ |
| New .docx output (original untouched) | ✅ | ✅ |
| Progress bar | ✅ | ✅ |

---

## Targeting these roles?

The app's keyword library is pre-tuned for:

- Release Manager / Coordinator
- DevOps Engineer / Manager
- Platform Engineer
- Automation Specialist
- Site Reliability Engineer (SRE)
- Technical Program / Project Manager

---

## License

BSD 3-Clause — see [LICENSE](LICENSE)

