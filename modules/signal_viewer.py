import numpy as np
import pandas as pd
import plotly.graph_objects as go


class EEGSignalViewer:

    def __init__(self, raw):
        self.raw = raw

    def get_time_vector(self):

        sfreq = self.raw.info["sfreq"]

        times = np.arange(
            self.raw.n_times
        ) / sfreq

        return times

    def get_channel_signal(
        self,
        channel_name,
        start_sec=0,
        end_sec=10
    ):

        sfreq = self.raw.info["sfreq"]

        start_idx = int(
            start_sec * sfreq
        )

        end_idx = int(
            end_sec * sfreq
        )

        signal = self.raw.get_data(
            picks=[channel_name]
        )[0]

        signal = signal[
            start_idx:end_idx
        ]

        times = np.arange(
            start_idx,
            end_idx
        ) / sfreq

        return times, signal

    def plot_single_channel(
        self,
        channel_name,
        start_sec=0,
        end_sec=10
    ):

        times, signal = self.get_channel_signal(
            channel_name,
            start_sec,
            end_sec
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=times,
                y=signal,
                mode="lines",
                name=channel_name
            )
        )

        fig.update_layout(
            title=f"{channel_name} Signal",
            xaxis_title="Time (s)",
            yaxis_title="Amplitude"
        )

        return fig

    def plot_multiple_channels(
        self,
        channels,
        start_sec=0,
        end_sec=10
    ):

        fig = go.Figure()

        offset = 0

        for channel in channels:

            times, signal = self.get_channel_signal(
                channel,
                start_sec,
                end_sec
            )

            scaled_signal = signal + offset

            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=scaled_signal,
                    mode="lines",
                    name=channel
                )
            )

            offset += np.std(signal) * 8

        fig.update_layout(
            title="Multi-Channel EEG View",
            xaxis_title="Time (s)",
            yaxis_title="Amplitude"
        )

        return fig

    def get_channel_summary(
        self,
        channel_name
    ):

        signal = self.raw.get_data(
            picks=[channel_name]
        )[0]

        return {
            "mean": np.mean(signal),
            "std": np.std(signal),
            "max": np.max(signal),
            "min": np.min(signal),
            "peak_to_peak":
                np.ptp(signal)
        }

    def create_channel_comparison(
        self,
        channel_1,
        channel_2,
        start_sec=0,
        end_sec=10
    ):

        t1, s1 = self.get_channel_signal(
            channel_1,
            start_sec,
            end_sec
        )

        t2, s2 = self.get_channel_signal(
            channel_2,
            start_sec,
            end_sec
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=t1,
                y=s1,
                mode="lines",
                name=channel_1
            )
        )

        fig.add_trace(
            go.Scatter(
                x=t2,
                y=s2,
                mode="lines",
                name=channel_2
            )
        )

        fig.update_layout(
            title="Channel Comparison",
            xaxis_title="Time (s)",
            yaxis_title="Amplitude"
        )

        return fig