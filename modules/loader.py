import os
import tempfile
from pathlib import Path

import mne
import numpy as np


SUPPORTED_FORMATS = {
    ".edf": "EDF",
    ".fif": "FIF",
    ".set": "EEGLAB",
    ".vhdr": "BrainVision"
}


class EEGLoader:
    """
    Loads EEG files and returns an MNE Raw object.
    """

    def __init__(self):
        self.raw = None

    def _validate_file(self, file_path):

        ext = Path(file_path).suffix.lower()

        if ext not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {ext}\n"
                f"Supported formats: {list(SUPPORTED_FORMATS.keys())}"
            )

        return ext

    def _read_file(self, file_path, ext):

        if ext == ".edf":
            raw = mne.io.read_raw_edf(
                file_path,
                preload=True,
                verbose=False
            )

        elif ext == ".fif":
            raw = mne.io.read_raw_fif(
                file_path,
                preload=True,
                verbose=False
            )

        elif ext == ".set":
            raw = mne.io.read_raw_eeglab(
                file_path,
                preload=True,
                verbose=False
            )

        elif ext == ".vhdr":
            raw = mne.io.read_raw_brainvision(
                file_path,
                preload=True,
                verbose=False
            )

        else:
            raise ValueError("Unsupported file")

        return raw

    def _standardize_channel_names(self, raw):

        try:
            montage = mne.channels.make_standard_montage("standard_1005")
            montage_lower = {ch.lower(): ch for ch in montage.ch_names}
        except Exception:
            montage_lower = {}

        rename_dict = {}

        for ch in raw.ch_names:

            clean_name = (
                ch.strip()
                .replace("EEG ", "")
                .replace(".", "")
            )

            standard_name = montage_lower.get(clean_name.lower(), clean_name)
            rename_dict[ch] = standard_name

        raw.rename_channels(rename_dict)

        return raw

    def _set_montage(self, raw):

        try:
            montage = mne.channels.make_standard_montage(
                "standard_1005"
            )

            raw.set_montage(
                montage,
                on_missing="ignore"
            )

        except Exception:
            pass

        return raw

    def _mark_flat_channels(self, raw):

        bads = []

        data = raw.get_data()

        for idx, channel in enumerate(raw.ch_names):

            std = np.std(data[idx])

            if std < 1e-8:
                bads.append(channel)

        raw.info["bads"] = bads

        return raw

    def _basic_cleaning(self, raw):

        raw.pick_types(
            eeg=True,
            exclude=[]
        )

        raw.load_data()

        return raw

    def load(self, file_path):

        ext = self._validate_file(file_path)

        raw = self._read_file(file_path, ext)

        raw = self._standardize_channel_names(raw)

        raw = self._set_montage(raw)

        raw = self._mark_flat_channels(raw)

        raw = self._basic_cleaning(raw)

        self.raw = raw

        return raw