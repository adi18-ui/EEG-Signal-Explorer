import numpy as np

from scipy.signal import spectrogram

import plotly.graph_objects as go


class EEGSpectrogram:

    def __init__(self, raw):
        self.raw = raw
        self.sfreq = raw.info["sfreq"]

    def get_channel_signal(
        self,
        channel_name
    ):

        signal = self.raw.get_data(
            picks=[channel_name]
        )[0]

        return signal

    def compute_spectrogram(
        self,
        channel_name,
        fmin=0.5,
        fmax=45,
        nperseg=512,
        noverlap=256
    ):

        signal = self.get_channel_signal(
            channel_name
        )

        freqs, times, power = spectrogram(
            signal,
            fs=self.sfreq,
            nperseg=min(
                nperseg,
                len(signal)
            ),
            noverlap=min(
                noverlap,
                nperseg // 2
            ),
            scaling="density"
        )

        mask = (
            (freqs >= fmin)
            &
            (freqs <= fmax)
        )

        freqs = freqs[mask]
        power = power[mask]

        power_db = (
            10 *
            np.log10(
                power + 1e-12
            )
        )

        return freqs, times, power_db

    def plot_spectrogram(
        self,
        channel_name
    ):

        freqs, times, power = (
            self.compute_spectrogram(
                channel_name
            )
        )

        fig = go.Figure(
            data=go.Heatmap(
                x=times,
                y=freqs,
                z=power
            )
        )

        fig.update_layout(
            title=f"Spectrogram - {channel_name}",
            xaxis_title="Time (s)",
            yaxis_title="Frequency (Hz)"
        )

        return fig

    def get_band_activity_over_time(
        self,
        channel_name
    ):

        freqs, times, power = (
            self.compute_spectrogram(
                channel_name
            )
        )

        bands = {
            "Delta": (0.5, 4),
            "Theta": (4, 8),
            "Alpha": (8, 13),
            "Beta": (13, 30),
            "Gamma": (30, 45)
        }

        results = {}

        for band, (low, high) in bands.items():

            mask = (
                (freqs >= low)
                &
                (freqs < high)
            )

            results[band] = (
                power[mask]
                .mean(axis=0)
            )

        return times, results

    def plot_band_activity(
        self,
        channel_name
    ):

        times, band_data = (
            self.get_band_activity_over_time(
                channel_name
            )
        )

        fig = go.Figure()

        for band in band_data:

            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=band_data[band],
                    mode="lines",
                    name=band
                )
            )

        fig.update_layout(
            title=f"Band Activity Over Time - {channel_name}",
            xaxis_title="Time (s)",
            yaxis_title="Power (dB)"
        )

        return fig