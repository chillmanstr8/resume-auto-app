# Resume Optimizer Pro – User Guide (v1.0)

## Table of Contents

1. [What this app does](#1-what-this-app-does)
2. [System requirements](#2-system-requirements)
3. [Installation](#3-installation)
   - [macOS (primary target)](#macos-primary-target)
   - [Windows](#windows)
   - [Linux](#linux)
4. [Launching the app](#4-launching-the-app)
5. [Step-by-step usage](#5-step-by-step-usage)
6. [Understanding the results](#6-understanding-the-results)
7. [OpenAI API key (AI mode)](#7-openai-api-key-ai-mode)
8. [Tips for best results](#8-tips-for-best-results)
9. [Troubleshooting](#9-troubleshooting)
10. [FAQ](#10-faq)

---

## 1. What this app does

Resume Optimizer Pro compares your "master resume" against a specific job description
and produces a new, ATS-optimised Word document (.docx) with:

- **Keywords you were missing** incorporated naturally (AI mode) or
  listed as suggestions (basic mode)
- A **match-score** showing how well your resume aligns with the job before/after
- A clear **change summary** so you know exactly what was modified and why
- The **original file left completely untouched** – the output is always a new file
  named `<your-resume>_optimized_1.docx` (the number increments if a file already exists)

> **Important:** The app will NEVER add skills or experience you don't already have.
> Its job is to surface and emphasise what you *do* have in language that matches
> what hiring managers and ATS systems are looking for.

---

## 2. System requirements

| Item | Requirement |
|---|---|
| Python | 3.9 or later (3.12 recommended) |
| Operating system | macOS (Tahoe / Sequoia / Ventura / Monterey), Windows 10/11, Ubuntu/Debian |
| tkinter | Must be available (bundled with most Python installs) |
| Internet | Required for URL job-posting fetch and AI mode (OpenAI calls) |
| OpenAI API key | *Optional* – only needed for AI rewrite mode |
| Disk space | ~50 MB (Python deps) |

---

## 3. Installation

### macOS (primary target)

#### Option A – Homebrew (recommended)

```bash
# 1. Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python with tkinter support
brew install python-tk

# 3. Clone this repo
git clone https://github.com/chillmanstr8/resume-auto-app.git
cd resume-auto-app

# 4. Run the installer
chmod +x install.sh
./install.sh
```

#### Option B – python.org installer

1. Download Python 3.12 from <https://www.python.org/downloads/macos/>
2. Run the `.pkg` installer (tkinter is included)
3. Open Terminal:

```bash
git clone https://github.com/chillmanstr8/resume-auto-app.git
cd resume-auto-app
chmod +x install.sh
./install.sh
```

### Windows

1. Download Python 3.12 from <https://www.python.org/downloads/windows/>
2. During installation, check **"Add Python to PATH"** and ensure
   **"tcl/tk and IDLE"** is selected (it is by default)
3. Open Command Prompt or PowerShell:

```bat
git clone https://github.com/chillmanstr8/resume-auto-app.git
cd resume-auto-app
install.bat
```

### Linux

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install python3 python3-tk python3-venv python3-pip git

git clone https://github.com/chillmanstr8/resume-auto-app.git
cd resume-auto-app
chmod +x install.sh
./install.sh

# Fedora / RHEL
sudo dnf install python3 python3-tkinter python3-pip git
# Then same clone + install.sh steps above
```

---

## 4. Launching the app

After installation, you can launch the app in two ways:

**macOS / Linux – convenience script:**
```bash
./run.sh
```

**Any platform – manual:**
```bash
source venv/bin/activate      # Windows: venv\Scripts\activate
python main.py
```

**Windows – double-click** `run.bat`

---

## 5. Step-by-step usage

### Step 1 – Upload your master resume

Click **Browse…** and select your resume file.

- **.docx** – recommended; preserves section structure best
- **.pdf** – supported; some complex PDFs may lose minor formatting
- **.txt** – fully supported; plain text

> **What is a "master resume"?**  
> This is your comprehensive resume that lists *everything* you have ever done –
> all roles, responsibilities, projects, and skills. You won't send this document
> to employers directly; it's the source the app draws from.  
> The more complete it is, the better the optimised output will be.

### Step 2 – Provide the job description

Choose one of two input methods using the radio buttons:

**URL** – paste the full link to the job posting page  
`https://www.linkedin.com/jobs/view/12345678`

**Paste Text** – copy the job description from the page and paste it directly
into the text box. This is useful when the URL requires a login.

### Step 3 – Add your OpenAI API key (optional)

- Leave blank to run in **basic mode** (keyword gap report only)
- Enter your key for **AI mode** (GPT-4o rewrites each resume section)

Your key is saved to `~/.resume_optimizer/config.json` on your machine —
it is never sent anywhere except OpenAI's API when performing a rewrite.

Click **Save Key** to persist it between sessions.

### Analyze

Click **🚀 ANALYZE & OPTIMIZE RESUME** and watch the progress bar.

The app will:
1. Parse your resume (5-20%)
2. Fetch/clean the job description (20-40%)
3. Extract keywords and calculate your ATS match score (40-65%)
4. Run AI optimisation if a key is provided (65-75%)
5. Generate the new .docx file (75-100%)

Typical run time: **15-30 seconds** (basic) or **30-60 seconds** (AI mode)

### Review & save

Once analysis is complete:
- Read the **Results & Summary** panel
- Click **💾 Save Optimized Resume** to open/confirm the saved file
  (it was already saved automatically in the same folder as your original)
- Click **🔄 Start Over** to analyse a different job posting

---

## 6. Understanding the results

```
══════════════════════════════════════════════════════════════
   RESUME OPTIMIZATION SUMMARY
══════════════════════════════════════════════════════════════

  ATS Keyword Match Score:  42 %
  [████████░░░░░░░░░░░░]

  🔍  14 keyword(s) NOT found in your resume:
       •  ci/cd
       •  release management
       •  terraform
       …

  ✅  8 keyword(s) already present:
       •  agile
       •  devops
       …

  ✏️   Changes applied:
       Identified 14 ATS keyword(s) missing from your resume.
       → Consider adding: 'ci/cd'
       …

  💾  Saved → /Users/you/Documents/MyResume_optimized_1.docx
```

**ATS Match Score** – percentage of job-description keywords found in your resume.
A score above 70% is generally considered strong for ATS systems.

---

## 7. OpenAI API key (AI mode)

1. Create a free account at <https://platform.openai.com>
2. Navigate to **API Keys** and create a new key
3. Copy the key (starts with `sk-…`)
4. Paste it into the **Step 3** field in the app and click **Save Key**

**Cost:** GPT-4o charges by token. One typical resume optimisation run costs
approximately **$0.02 – $0.08 USD** at current pricing.

---

## 8. Tips for best results

- **Use a complete master resume.** The richer your source document, the more
  material the app has to work with. Include everything.
- **Paste the full job description, not just the title.** The more text, the
  more keywords the app can extract.
- **Review the output.** AI-generated text is excellent but not perfect.
  Always read the new document before sending it to an employer.
- **Run it multiple times.** Apply for several roles? Run the app once per role
  with each job description to get a tailored document each time.
- **Keep the original.** The app never modifies your master resume. All output
  files are new documents.

---

## 9. Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'tkinter'` | Install tkinter – see [Installation](#3-installation) |
| URL fetch fails | The site may block bots; switch to "Paste Text" mode |
| `Invalid API key` | Check for typos; ensure the key has not been revoked |
| PDF text is garbled | Try converting to .docx first (e.g. Word, LibreOffice) |
| Output file is mostly blank | Your original resume may use text boxes or unusual formatting; try saving as .txt first |
| `SSL` / `certificate` errors on macOS | Run `pip install --upgrade certifi` inside the venv |

---

## 10. FAQ

**Q: Will the app make up skills I don't have?**  
A: No. The system prompt explicitly forbids fabrication. The AI only
rephrases and emphasises what is already in your document.

**Q: Is my resume sent to anyone?**  
A: Your resume text is sent to OpenAI's API *only* when you use AI mode
(i.e., you have entered an API key). In basic mode, all processing is
100% local. OpenAI's data usage policy applies when AI mode is used.

**Q: Can I use this for multiple job applications?**  
A: Absolutely – that's the primary use case. Each run produces a new
output file, so you can accumulate a folder of targeted resumes.

**Q: The output is more than 2 pages. What do I do?**  
A: The AI targets 2 pages but cannot enforce exact page-count in every
circumstance. Open the .docx in Word and trim any excess content manually.

**Q: Can I run this without an internet connection?**  
A: Yes – in basic mode (no API key). The only network calls are:
(a) optional URL scraping for job descriptions, and (b) OpenAI API calls
in AI mode. Everything else is local.

---

*Resume Optimizer Pro v1.0 – built for Freddie, targeting Release Manager /
DevOps / Platform Engineering roles. Let's find you that job! 🚀*
