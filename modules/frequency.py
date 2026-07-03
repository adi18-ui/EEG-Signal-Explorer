# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd

from scipy.signal import welch
from scipy.integrate import trapezoid

import plotly.graph_objects as go
import plotly.express as px


class EEGFrequencyAnalyzer:

    BANDS = {
        "Delta": (0.5, 4),
        "Theta": (4, 8),
        "Alpha": (8, 13),
        "Beta": (13, 30),
        "Gamma": (30, 45)
    }

    def __init__(self, raw):
        self.raw = raw
        self.sfreq = raw.info["sfreq"]

    def compute_psd(
        self,
        channel_name,
        fmin=0.5,
        fmax=45
    ):

        signal = self.raw.get_data(
            picks=[channel_name]
        )[0]

        freqs, psd = welch(
            signal,
            fs=self.sfreq,
            nperseg=min(
                1024,
                len(signal)
            )
        )

        mask = (
            (freqs >= fmin)
            &
            (freqs <= fmax)
        )

        return freqs[mask], psd[mask]

    def compute_band_power(
        self,
        channel_name
    ):

        freqs, psd = self.compute_psd(
            channel_name
        )

        powers = {}

        for band, (low, high) in self.BANDS.items():

            mask = (
                (freqs >= low)
                &
                (freqs < high)
            )

            power = trapezoid(
                psd[mask],
                freqs[mask]
            )

            powers[band] = power

        return powers

    def compute_relative_band_power(
        self,
        channel_name
    ):

        powers = self.compute_band_power(
            channel_name
        )

        total_power = sum(
            powers.values()
        )

        relative = {}

        for band in powers:

            relative[band] = (
                powers[band]
                /
                total_power
            )

        return relative

    def compute_all_channels_bandpower(
        self
    ):

        rows = []

        for channel in self.raw.ch_names:

            powers = self.compute_band_power(
                channel
            )

            row = {
                "Channel": channel
            }

            row.update(
                powers
            )

            rows.append(row)

        return pd.DataFrame(rows)

    def plot_psd(
        self,
        channel_name
    ):

        freqs, psd = self.compute_psd(
            channel_name
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=freqs,
                y=psd,
                mode="lines",
                name="PSD"
            )
        )

        fig.update_layout(
            title=f"PSD - {channel_name}",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Power"
        )

        return fig

    def plot_band_power(
        self,
        channel_name
    ):

        powers = self.compute_band_power(
            channel_name
        )

        fig = px.bar(
            x=list(powers.keys()),
            y=list(powers.values()),
            labels={
                "x": "Band",
                "y": "Power"
            },
            title=f"Band Power - {channel_name}"
        )

        return fig

    def plot_relative_band_power(
        self,
        channel_name
    ):

        powers = self.compute_relative_band_power(
            channel_name
        )

        fig = px.pie(
            names=list(
                powers.keys()
            ),
            values=list(
                powers.values()
            ),
            title=f"Relative Band Power - {channel_name}"
        )

        return fig

    def get_dominant_band(
        self,
        channel_name
    ):

        powers = self.compute_band_power(
            channel_name
        )

        dominant = max(
            powers,
            key=powers.get
        )

        return dominant