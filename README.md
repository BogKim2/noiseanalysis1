# SEM Image Denoising Application

A professional desktop application for denoising Scanning Electron Microscope (SEM) images with real-time preview, comprehensive noise analysis, and automatic parameter optimization.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

### 7 Denoising Filters
1. **Bilateral Filter** - Edge-preserving smoothing that reduces noise while keeping edges sharp
2. **Non-Local Means (NLM)** - Patch-based denoising utilizing image self-similarity
3. **Wavelet Denoising** - Multi-scale wavelet transform with soft/hard thresholding
4. **Fourier Filter** - Frequency domain filtering (lowpass, highpass, bandpass, bandstop)
5. **Line-wise Correction** - Horizontal/vertical scan line noise removal (SEM-specific)
6. **Notch Filter** - Periodic noise removal in frequency domain
7. **Anisotropic Diffusion** - Edge-enhancing diffusion filtering (Perona-Malik)

### Pipeline Processing
- Combine multiple filters in sequence (3-step pipeline)
- Default optimized for SEM: Line-wise → Notch → NLM
- All parameters synchronized across tabs

### Real-time Preview
- Auto Apply mode for instant parameter feedback
- Side-by-side comparison of original and processed images
- Synchronized zoom and pan between views
- Keyboard shortcuts for navigation (F=Fit, 1=100%, +/- for zoom)

### Comprehensive Noise Analysis
15 noise metrics calculated in real-time:

| Category | Metrics |
|----------|---------|
| **SNR** | SNR (μ/σ), SNR (RMS) |
| **Noise σ** | Standard Deviation, MAD-based, Laplacian-based |
| **Line-wise** | Horizontal σ, Vertical σ, Line Correlation, Abnormal Lines Count |
| **Edge-based** | Edge Noise, Gradient Variance, Edge Sharpness, Edge Coherence |
| **PSD** | Total Spectral Energy, PSD Peaks Count |

### Auto Optimization
- **Hill Climbing** - Fast local search for individual filters
- **Grid Search** - Exhaustive search with coarse-to-fine strategy for pipeline
- Weighted score function with penalty system to prevent metric degradation
- Customizable weights and penalty factors

### Settings Persistence
- All parameters saved to JSON automatically
- Window geometry and last opened file remembered
- Optimization weights configurable via GUI

## Installation

### Prerequisites
- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Quick Start

```bash
# Clone or download the project
cd denoising_python

# Install dependencies with uv
uv sync

# Run the application
uv run python main.py
```

### Alternative: pip installation

```bash
pip install PySide6 opencv-python numpy scikit-image scipy Pillow PyWavelets
python main.py
```

## Code Statistics

**Total Lines of Code: 6,776**

| Module | File | Lines |
|--------|------|------:|
| **Root** | `main.py` | 37 |
| **logic/** | `__init__.py` | 27 |
| | `filter_base.py` | 109 |
| | `bilateral.py` | 72 |
| | `nlm.py` | 86 |
| | `wavelet.py` | 84 |
| | `fourier.py` | 160 |
| | `linewise.py` | 137 |
| | `notch.py` | 205 |
| | `anisotropic.py` | 136 |
| | `pipeline.py` | 127 |
| | `file_io.py` | 178 |
| | `settings.py` | 152 |
| | **Subtotal** | **1,473** |
| **ui/** | `__init__.py` | 21 |
| | `main_window.py` | 338 |
| | `filter_tabs.py` | 1,394 |
| | `compare_view.py` | 484 |
| | `noise_panel.py` | 557 |
| | `optimization_settings.py` | 276 |
| | `styles.py` | 352 |
| | **Subtotal** | **3,422** |
| **calnoise/** | `__init__.py` | 18 |
| | `analyzer.py` | 252 |
| | `snr.py` | 103 |
| | `noise_std.py` | 101 |
| | `linewise.py` | 138 |
| | `edge_noise.py` | 191 |
| | `psd.py` | 175 |
| | **Subtotal** | **978** |
| **optimize/** | `__init__.py` | 21 |
| | `optimizer_base.py` | 169 |
| | `score_function.py` | 244 |
| | `hill_climbing.py` | 169 |
| | `grid_search.py` | 263 |
| | **Subtotal** | **866** |

## Project Structure

```
denoising_python/
├── main.py                 # Application entry point
├── pyproject.toml          # Project dependencies
├── settings.json           # User settings (auto-generated)
│
├── logic/                  # Core processing logic
│   ├── filter_base.py      # Abstract base class for filters
│   ├── bilateral.py        # Bilateral filter implementation
│   ├── nlm.py              # Non-Local Means filter
│   ├── wavelet.py          # Wavelet denoising
│   ├── fourier.py          # Fourier domain filtering
│   ├── linewise.py         # Line-wise correction
│   ├── notch.py            # Notch filter
│   ├── anisotropic.py      # Anisotropic diffusion
│   ├── pipeline.py         # Multi-filter pipeline
│   ├── file_io.py          # Image loading/saving
│   └── settings.py         # Settings management
│
├── ui/                     # User interface components
│   ├── main_window.py      # Main application window
│   ├── filter_tabs.py      # Tab widget for each filter
│   ├── compare_view.py     # Side-by-side image comparison
│   ├── noise_panel.py      # Noise analysis window
│   ├── optimization_settings.py  # Optimization parameter dialog
│   └── styles.py           # Dark theme styling
│
├── calnoise/               # Noise calculation module
│   ├── analyzer.py         # Main analyzer combining all metrics
│   ├── snr.py              # Signal-to-Noise Ratio calculations
│   ├── noise_std.py        # Noise standard deviation methods
│   ├── linewise.py         # Line-wise noise metrics
│   ├── edge_noise.py       # Edge-based noise metrics
│   └── psd.py              # Power Spectral Density analysis
│
├── optimize/               # Optimization algorithms
│   ├── optimizer_base.py   # Base class and parameter bounds
│   ├── score_function.py   # Weighted scoring with penalties
│   ├── hill_climbing.py    # Hill climbing optimizer
│   └── grid_search.py      # Grid search optimizer
│
└── output/                 # Processed images (auto-created)
```

## File Descriptions

### Logic Module (`logic/`)

| File | Description |
|------|-------------|
| `filter_base.py` | Abstract `DenoiseFilter` class defining the interface for all filters |
| `bilateral.py` | OpenCV bilateral filter with diameter, sigma color/space parameters |
| `nlm.py` | Non-Local Means using `cv2.fastNlMeansDenoising` |
| `wavelet.py` | PyWavelets-based denoising with configurable wavelet families |
| `fourier.py` | FFT-based frequency filtering with multiple filter types |
| `linewise.py` | Row/column mean subtraction for scan line artifact removal |
| `notch.py` | Frequency notch filter for periodic noise with auto-detection |
| `anisotropic.py` | Perona-Malik anisotropic diffusion implementation |
| `pipeline.py` | Sequential filter application with parameter management |
| `file_io.py` | Supports PNG, JPG, TIFF, BMP loading; auto-naming for saves |
| `settings.py` | JSON-based settings with dot-notation access (`settings.get("a.b.c")`) |

### UI Module (`ui/`)

| File | Description |
|------|-------------|
| `main_window.py` | Main window with menu bar, drag-drop support, window geometry persistence |
| `filter_tabs.py` | `FilterTabWidget` containing 8 tabs (7 filters + Pipeline) |
| `compare_view.py` | `CompareView` with synchronized `ImagePanel` widgets for zoom/pan |
| `noise_panel.py` | `NoiseAnalysisWindow` with Simple (5 metrics) and Complete (15 metrics) tabs |
| `optimization_settings.py` | `OptimizationSettingsWindow` for weight/penalty configuration |
| `styles.py` | Dark theme color palette and widget styling |

### Noise Calculation Module (`calnoise/`)

| File | Description |
|------|-------------|
| `analyzer.py` | `NoiseAnalyzer` class orchestrating all metric calculations |
| `snr.py` | SNR calculation: mean/std method and RMS-based method |
| `noise_std.py` | Noise σ: simple std, MAD-based (robust), Laplacian-based (edge-aware) |
| `linewise.py` | Line metrics: horizontal/vertical σ, correlation, abnormal line detection |
| `edge_noise.py` | Edge metrics: sharpness, coherence, gradient variance, edge preservation |
| `psd.py` | PSD analysis: 2D/1D PSD, radial profile, peak detection, total energy |

### Optimization Module (`optimize/`)

| File | Description |
|------|-------------|
| `optimizer_base.py` | `OptimizerBase` ABC, `PARAM_BOUNDS` dict, `OptimizationResult` dataclass |
| `score_function.py` | `ScoreFunction` with weighted metrics and negative-change penalties |
| `hill_climbing.py` | `HillClimbingOptimizer` - iterative local search |
| `grid_search.py` | `GridSearchOptimizer` - coarse-to-fine exhaustive search |

## Usage

### Basic Workflow

1. **Open Image**: File → Open Image or drag-and-drop
2. **Select Filter**: Click on filter tab (1-7) or Pipeline (8)
3. **Adjust Parameters**: Use sliders with real-time preview
4. **Analyze Noise**: View metrics in Noise Analysis window
5. **Optimize**: Click "Auto Optimize" for automatic parameter tuning
6. **Save**: Click "Save" button to export processed image

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+O` | Open image |
| `Ctrl+N` | Show Noise Analysis window |
| `Ctrl+Q` | Exit application |
| `F` | Fit image to view |
| `1` | View at 100% zoom |
| `+` / `-` | Zoom in/out |
| `C` | Center view |
| Arrow keys | Pan image |

### Optimization Settings

Access via **View → Optimization Settings**

**Metric Weights** (higher = more important):
- SNR: 2.0 (signal quality)
- Noise σ (MAD): 1.0 (noise level)
- Edge Sharpness: 5.0 (detail preservation - most critical)
- Line σ (H): 1.0 (scan line artifacts)
- Abnormal Lines: 1.0 (severe artifacts)

**Penalty Settings**:
- General Negative Penalty: 5x multiplier for degraded metrics
- Critical Metric Penalty: 20x multiplier for critical metrics
- Per-Negative Penalty: 50 points deducted per degraded metric

## Output

Processed images are saved to `output/` folder with naming convention:
```
{original_name}_{filter_info}_{YYYYMMDD_HHMMSS}.png
```

Example: `image_Linewise_Notch_NLM_20251227_143052.png`

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | ≥6.6.0 | Qt-based GUI framework |
| opencv-python | ≥4.8.0 | Image processing, bilateral, NLM filters |
| numpy | ≥1.24.0 | Array operations, FFT |
| scikit-image | ≥0.22.0 | Wavelet denoising, image metrics |
| scipy | ≥1.11.0 | Signal processing, optimization |
| Pillow | ≥10.0.0 | Image I/O |
| PyWavelets | ≥1.4.0 | Wavelet transforms |

## Configuration

Settings are stored in `settings.json`:

```json
{
  "last_file_path": "path/to/last/image.png",
  "window_geometry": {"width": 1700, "height": 1050, "x": 50, "y": 50},
  "filter_parameters": {
    "Bilateral": {"d": 9, "sigmaColor": 75.0, "sigmaSpace": 75.0},
    "NLM": {"h": 10.0, "templateWindowSize": 7, "searchWindowSize": 21},
    ...
  },
  "pipeline_filters": ["Linewise", "Notch", "NLM"],
  "optimization_weights": {
    "snr": 2.0,
    "edge_sharpness": 5.0,
    "negative_penalty_factor": 5.0,
    ...
  }
}
```

## License

MIT License - Feel free to use, modify, and distribute.

## Acknowledgments

Built with Python and PySide6 for professional SEM image processing workflows.
