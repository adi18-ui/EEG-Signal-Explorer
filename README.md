# EEG Explorer

An interactive web application for loading, visualizing, and analyzing Electroencephalography (EEG) data. Built with Python, Streamlit, and MNE-Python.

## Project Structure

```
├── app.py                  # Main entry point of the Streamlit application
├── requirements.txt        # Python package dependencies
├── modules/
│   ├── loader.py           # EEG file loader (EDF, FIF, etc.)
│   ├── overview.py         # Summary statistics, channel info, and metadata
│   ├── signal_viewer.py    # Time-domain raw EEG signal browser
│   ├── frequency.py        # Spectral analysis (PSD, spectrograms, band power)
│   ├── topomap.py          # Topographical maps for spatial distribution of power
│   └── report.py           # PDF/HTML export and report generation
└── outputs/                # Generated reports, processed files, and downloads
```

## Features

1. **EEG Data Loader**: Support for standard EEG formats like EDF, FIF, BrainVision, etc.
2. **Metadata Overview**: Quick summary of sampling rate, duration, channel types, and bad channels.
3. **Interactive Signal Viewer**: Scroll through EEG channels, adjust scaling, filtering (lowpass, highpass, notch), and flag bad channels.
4. **Spectral Analysis**: Compute and plot Power Spectral Density (PSD) and spectrograms.
5. **Topographical Maps**: View interactive 2D topomaps of specific frequency bands (Delta, Theta, Alpha, Beta, Gamma).

7. **Report Generator**: Compile visualization findings into a downloadable report.

## Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   streamlit run app.py
   ```
