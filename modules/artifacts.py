# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd

from scipy.stats import zscore


class EEGArtifactDetector:

    def __init__(self, raw):

        self.raw = raw
        self.data = raw.get_data()
        self.channels = raw.ch_names
        self.sfreq = raw.info["sfreq"]

    # ----------------------------
    # Flat Channel Detection
    # ----------------------------

    def detect_flat_channels(
        self,
        threshold=1e-8
    ):

        flat_channels = []

        for idx, ch in enumerate(self.channels):

            signal = self.data[idx]

            if np.std(signal) < threshold:

                flat_channels.append(ch)

        return flat_channels

    # ----------------------------
    # Noisy Channel Detection
    # ----------------------------

    def detect_noisy_channels(
        self,
        z_threshold=3
    ):

        variances = np.var(
            self.data,
            axis=1
        )

        zscores = zscore(
            variances
        )

        noisy = []

        for idx, score in enumerate(zscores):

            if score > z_threshold:

                noisy.append(
                    self.channels[idx]
                )

        return noisy

    # ----------------------------
    # Blink Detection
    # ----------------------------

    def detect_blinks(
        self,
        frontal_channels=None,
        threshold_std=4
    ):

        if frontal_channels is None:

            frontal_channels = [
                ch for ch in self.channels
                if ch.startswith("Fp")
            ]

        if len(frontal_channels) == 0:

            return []

        blink_events = []

        for ch in frontal_channels:

            signal = self.raw.get_data(
                picks=[ch]
            )[0]

            threshold = (
                np.mean(signal)
                +
                threshold_std *
                np.std(signal)
            )

            peaks = np.where(
                signal > threshold
            )[0]

            blink_events.extend(
                peaks.tolist()
            )

        blink_events = sorted(
            list(
                set(
                    blink_events
                )
            )
        )

        blink_times = [
            p / self.sfreq
            for p in blink_events
        ]

        return blink_times

    # ----------------------------
    # Signal Statistics
    # ----------------------------

    def channel_statistics(self):

        rows = []

        for idx, ch in enumerate(
            self.channels
        ):

            signal = self.data[idx]

            rows.append({

                "Channel": ch,

                "Mean":
                    np.mean(signal),

                "Std":
                    np.std(signal),

                "Variance":
                    np.var(signal),

                "PeakToPeak":
                    np.ptp(signal)

            })

        return pd.DataFrame(
            rows
        )

    # ----------------------------
    # Quality Score
    # ----------------------------

    def compute_quality_score(self):

        total_channels = len(
            self.channels
        )

        flat_count = len(
            self.detect_flat_channels()
        )

        noisy_count = len(
            self.detect_noisy_channels()
        )

        penalty = (
            flat_count * 10
            +
            noisy_count * 5
        )

        score = max(
            0,
            100 - penalty
        )

        return score

    # ----------------------------
    # Summary Report
    # ----------------------------

    def generate_summary(self):

        flat = (
            self.detect_flat_channels()
        )

        noisy = (
            self.detect_noisy_channels()
        )

        blinks = (
            self.detect_blinks()
        )

        score = (
            self.compute_quality_score()
        )

        return {

            "quality_score":
                score,

            "flat_channels":
                flat,

            "noisy_channels":
                noisy,

            "blink_count":
                len(blinks),

            "blink_times":
                blinks[:20]

        }