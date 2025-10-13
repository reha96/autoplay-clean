# Autoplay: Data Analysis and Research Paper

This repository contains the data cleaning, statistical analysis, and paper writing components for the research project examining the causal effects of autoplay features on video consumption behavior.

## Project Overview

This project analyzes data from a two-day online experiment testing whether autoplay features drive excessive screen time. Participants allocated 20 minutes between transcribing random characters and watching funny animal videos, with autoplay randomly assigned to isolate its causal effect on content consumption. The experimental data collection interface is documented in a separate repository: [labor_leisure_experiment](https://github.com/reha96/labor_leisure_experiment).

**Key Research Question:** Does autoplay in isolation override users' stated preferences for media consumption?

## Repository Structure

```
autoplay-clean/
├── python/
│   ├── 2025-new/           # Current data cleaning scripts
│   │   ├── clean.py        # Main cleaning script: processes raw data → cleaned datasets
│   │   ├── nlp_cleaned.py  # Natural language processing for open-ended responses
│   │   ├── videos.py       # Video content analysis
│   │   └── transition_analysis_summary.txt
│   └── old/                # Legacy scripts from earlier analysis versions
├── stata/
│   ├── 1_analysis.do       # Main analysis: balance tables, summary stats, regressions
│   ├── 2_mpl.do           # Multiple Price List analysis (WTP for autoplay)
│   ├── 3_nlp.do           # Analysis of qualitative responses
│   ├── 4_rd.do            # Regression discontinuity analysis
│   ├── f_*.do             # Figure generation scripts
│   └── figures/           # Output figures (PNG files)
├── writing/
│   ├── main.tex           # Main LaTeX manuscript
│   ├── main.pdf           # Compiled research paper
│   ├── ref.bib            # Bibliography
│   └── *.png              # Figures included in paper
└── README.md
```

**Note:** Raw experimental data (`autoplay.csv`) is not included in this repository.

## Workflow Pipeline

This project follows a three-stage analysis pipeline: **Python → Stata → LaTeX**

### 1. Data Cleaning (Python)

**Location:** `python/2025-new/`

**Main Script:** `clean.py`

**Input:** 
- `autoplay.csv` - Raw data from online experiment (not included in repo)

**Process:**
1. Loads participant-level data and session logs
2. Parses event sequences (task switches, video plays, transcription submissions)
3. Detects mouseout periods (20+ consecutive seconds) for attention validation
4. Creates session-level aggregates (typing/watching periods, videos watched, etc.)
5. Generates both long format (second-by-second) and wide format (participant-level) datasets

**Output:**
- `long_format_data.csv` - Second-by-second timeline for each participant
- `sessions_data.csv` - Individual typing/watching session details
- `clean-data.xlsx` - Main analysis dataset (exported to `stata/`)

**Other Scripts:**
- `nlp_cleaned.py` - Processes open-ended survey responses for qualitative analysis
- `videos.py` - Analyzes video content characteristics

### 2. Statistical Analysis (Stata)

**Location:** `stata/`

**Input:** `clean-data.xlsx` from Python pipeline

**Main Analysis Files:**
1. **`1_analysis.do`** - Core analysis
   - Creates final analysis dataset (`cleaned_autoplay_data.dta`)
   - Balance tables (randomization checks)
   - Summary statistics
   - Main treatment effect regressions
   - Robustness checks

2. **`2_mpl.do`** - Multiple Price List analysis
   - Estimates Willingness To Pay for autoplay
   - Demand for commitment devices

3. **`3_nlp.do`** - Qualitative analysis
   - Word frequency analysis
   - Concept detection (e.g., "break-taking," negative task perceptions)

4. **`4_rd.do`** - Regression discontinuity
   - Tests whether participants monitor their day 1 plans
   - Identifies behavioral changes at plan completion threshold

**Figure Generation Scripts:** `f_*.do` files create publication-ready figures

**Output:** 
- `cleaned_autoplay_data.dta` - Final Stata dataset
- `figures/*.png` - Statistical figures and plots

### 3. Paper Writing (LaTeX)

**Location:** `writing/`

**Main Files:**
- `main.tex` - Complete manuscript including:
  - Introduction and literature review
  - Experimental design
  - Results and analysis
  - Discussion and conclusion
- `ref.bib` - Bibliography (BibTeX format)
- Figure files (`.png`) imported from `stata/figures/` and local figures

**Compilation:**
```bash
cd writing/
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

**Output:** `main.pdf` - Final research paper

## Getting Started

### Prerequisites

- **Python 3.x** with:
  - pandas
  - numpy
  - re (regex)
  
- **Stata** (tested on version 18)
  
- **LaTeX** distribution (TeX Live, MiKTeX, or MacTeX)

### Running the Complete Pipeline

1. **Obtain Raw Data**
   - Collect data using the online experiment: [labor_leisure_experiment](https://github.com/reha96/labor_leisure_experiment)
   - Place `autoplay.csv` in `python/2025-new/` directory

2. **Data Cleaning**
   ```bash
   cd python/2025-new/
   python clean.py
   ```
   This creates:
   - `long_format_data.csv`
   - `sessions_data.csv`
   - Copies `clean-data.xlsx` to `../../stata/`

3. **Statistical Analysis**
   ```stata
   cd stata/
   
   // Run analyses in order:
   do 1_analysis.do    // Main analysis
   do 2_mpl.do         // MPL analysis
   do 3_nlp.do         // Qualitative analysis
   do 4_rd.do          // RD analysis
   
   // Generate figures:
   do f_cdf.do
   do f_hist_time_choice.do
   // ... (other figure scripts)
   ```

4. **Compile Paper**
   ```bash
   cd writing/
   pdflatex main.tex
   bibtex main
   pdflatex main.tex
   pdflatex main.tex
   ```
   Output: `main.pdf`

## Data

### Raw Data Source
Raw experimental data comes from the online experiment platform documented in [labor_leisure_experiment](https://github.com/reha96/labor_leisure_experiment). The experiment includes:
- Two-day design (planning on Day 1, execution on Day 2)
- Random assignment to Autoplay or Control conditions
- 20-minute main session with:
  - Transcription task (typing random characters for 0.15 pence/second)
  - Watching task (80 curated funny animal videos for 0.10 pence/second)
- Participant demographics and survey responses

**Raw data file:** `autoplay.csv` (not included in this repository)

### Cleaned Data Structure

**Wide Format** (`clean-data.xlsx`):
- One row per participant
- Variables include:
  - `id` - Participant identifier
  - `treatment` - Binary indicator (0 = Control, 1 = Autoplay)
  - `timeChoice` - Day 1 planned transcription time
  - `typing_log` - Actual transcription time (Day 2)
  - `videos_watched_total` - Number of videos watched
  - Session-level aggregates (duration, number of sessions, etc.)
  - Demographics (age, gender, employment, income, marital status)

**Long Format** (`long_format_data.csv`):
- One row per participant per second
- Second-by-second tracking of:
  - Current task (typing or watching)
  - Cumulative work time
  - Mouseout periods
  - Video transitions
  - Event counts

## Project Navigation Guide

### For Replication
1. Review experiment design: [labor_leisure_experiment](https://github.com/reha96/labor_leisure_experiment)
2. Examine data cleaning: `python/2025-new/clean.py` (well-commented with section markers)
3. Follow analysis pipeline: Stata do-files numbered 1-4
4. Check results presentation: `writing/main.tex`

### For Understanding Results
1. Read the paper: `writing/main.pdf`
2. Examine main regression tables: Output from `1_analysis.do`
3. Review figures: `stata/figures/` directory
4. Check robustness: Flagged participants analysis in `1_analysis.do`

### For Extending the Analysis
1. **Alternative specifications:** Modify `1_analysis.do` regression models
2. **Additional cleaning:** Update `python/2025-new/clean.py`
3. **New figures:** Add scripts to `stata/` following `f_*.do` pattern
4. **Manuscript edits:** Modify `writing/main.tex`

## Key Findings

From `main.pdf`:

1. **No evidence that autoplay increases video consumption** when content is held constant
2. **Positive WTP for autoplay** (6.72 pence/hour) - participants view it as convenient, not as a self-control problem
3. **Participants transcribed more than planned** - 35% less time on videos than Day 1 plans suggested
4. **Experimenter demand effects** likely confounded treatment, with participants viewing the experiment as a work setting
5. **Participants monitor their plans** but exceed them - 25.5 pp drop in transcribing probability after reaching Day 1 goal

## Citation

If you use this code or data, please cite:

```bibtex
@unpublished{tuncer2025autoplay,
  title={Does Autoplay Drive Excessive Screen Time? Evidence from an Online Experiment},
  author={Tuncer, Reha},
  year={2025},
  note={Working paper}
}
```

## License

[Specify your license]

## Contact

Reha Tuncer  
[Contact information]

## Acknowledgments

This study is supported by the Luxembourg National Research Fund (FNR) PRIDE 19/14302992. See paper acknowledgments for full list of contributors.

---

**Related Repository:** [labor_leisure_experiment](https://github.com/reha96/labor_leisure_experiment) - Online experiment interface and data collection
