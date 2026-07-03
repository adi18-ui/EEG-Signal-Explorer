# pyrefly: ignore [missing-import]
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


class EEGOverview:

    def __init__(self, raw):
        self.raw = raw

    def get_basic_info(self):

        duration_sec = (
            self.raw.n_times /
            self.raw.info["sfreq"]
        )

        return {
            "channels": len(self.raw.ch_names),
            "sampling_rate": self.raw.info["sfreq"],
            "duration_sec": duration_sec,
            "duration_min": duration_sec / 60
        }

    def get_channel_table(self):

        df = pd.DataFrame({
            "Channel": self.raw.ch_names,
            "Type": [
                self.raw.get_channel_types()[i]
                for i in range(len(self.raw.ch_names))
            ]
        })

        return df

    def get_bad_channels(self):

        return self.raw.info["bads"]

    def get_channel_statistics(self):

        data = self.raw.get_data()

        stats = []

        for idx, channel in enumerate(self.raw.ch_names):

            signal = data[idx]

            stats.append({
                "Channel": channel,
                "Mean": np.mean(signal),
                "Std": np.std(signal),
                "Min": np.min(signal),
                "Max": np.max(signal)
            })

        return pd.DataFrame(stats)

    def get_global_statistics(self):

        data = self.raw.get_data()

        return {
            "global_mean": np.mean(data),
            "global_std": np.std(data),
            "global_min": np.min(data),
            "global_max": np.max(data)
        }

    def get_channel_type_distribution(self):

        types = self.raw.get_channel_types()

        df = pd.DataFrame({
            "Type": types
        })

        counts = (
            df["Type"]
            .value_counts()
            .reset_index()
        )

        counts.columns = ["Type", "Count"]

        return counts

    def create_channel_distribution_plot(self):

        counts = self.get_channel_type_distribution()

        fig = px.pie(
            counts,
            values="Count",
            names="Type",
            title="Channel Type Distribution"
        )

        return fig

    def create_amplitude_distribution(self):

        data = self.raw.get_data()

        flattened = data.flatten()

        fig = px.histogram(
            flattened,
            nbins=100,
            title="Signal Amplitude Distribution"
        )

        fig.update_layout(
            xaxis_title="Amplitude",
            yaxis_title="Frequency"
        )

        return fig

    def create_variance_plot(self):

        data = self.raw.get_data()

        variances = np.var(
            data,
            axis=1
        )

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=self.raw.ch_names,
                y=variances
            )
        )

        fig.update_layout(
            title="Channel Variance",
            xaxis_title="Channel",
            yaxis_title="Variance"
        )

        return fig

    def get_quality_snapshot(self):

        bad_channels = len(
            self.raw.info["bads"]
        )

        total_channels = len(
            self.raw.ch_names
        )

        quality_score = (
            (total_channels - bad_channels)
            / total_channels
        ) * 100

        return {
            "quality_score": round(
                quality_score,
                2
            ),
            "bad_channels": bad_channels,
            "total_channels": total_channels
        }