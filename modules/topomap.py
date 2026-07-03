# pyrefly: ignore [missing-import]
import tempfile
import numpy as np
import os
import base64
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import mne
import matplotlib.pyplot as plt

from scipy.signal import welch
from scipy.integrate import trapezoid


@st.cache_resource
def get_cached_filtered_data(_raw, raw_id, band_name):
    bands = {
        "Delta": (0.5, 4),
        "Theta": (4, 8),
        "Alpha": (8, 13),
        "Beta": (13, 30),
        "Gamma": (30, 45)
    }
    low, high = bands[band_name]
    raw_copy = _raw.copy()
    if not raw_copy.preload:
        raw_copy.load_data()
    raw_copy.filter(
        l_freq=low,
        h_freq=high,
        fir_design='firwin',
        verbose=False
    )
    return raw_copy



class EEGTopomap:

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

    def compute_band_power_all_channels(
        self,
        band_name
    ):

        low, high = self.BANDS[band_name]

        powers = []

        for ch in self.raw.ch_names:

            signal = self.raw.get_data(
                picks=[ch]
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
                (freqs >= low)
                &
                (freqs <= high)
            )

            band_power = trapezoid(
                psd[mask],
                freqs[mask]
            )

            powers.append(
                band_power
            )

        return np.array(
            powers
        )

    def create_topomap(
        self,
        band_name="Alpha"
    ):

        powers = (
            self.compute_band_power_all_channels(
                band_name
            )
        )

        # Filter channels with valid, unique, non-overlapping coordinates
        valid_picks = []
        seen_locs = set()

        for idx, ch in enumerate(self.raw.info['chs']):
            loc = ch['loc'][:3]
            if np.all(loc == 0) or np.any(np.isnan(loc)):
                continue
            # Round coordinates to 4 decimals to check for overlap
            loc_tuple = (round(loc[0], 4), round(loc[1], 4), round(loc[2], 4))
            if loc_tuple in seen_locs:
                continue
            seen_locs.add(loc_tuple)
            valid_picks.append(idx)

        fig, ax = plt.subplots(
            figsize=(6, 5)
        )

        if not valid_picks:
            ax.text(0.5, 0.5, "No channels with valid, unique\ncoordinates found.",
                    ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
            ax.set_title(f"{band_name} Power Topomap (Error)")
            return fig

        powers_filtered = powers[valid_picks]
        valid_ch_names = [self.raw.ch_names[i] for i in valid_picks]
        raw_temp = self.raw.copy().pick(valid_ch_names)
        info_filtered = raw_temp.info

        mne.viz.plot_topomap(
            powers_filtered,
            info_filtered,
            axes=ax,
            show=False,
            contours=6
        )

        ax.set_title(
            f"{band_name} Power Topomap"
        )

        return fig

    def save_topomap(
        self,
        band_name="Alpha"
    ):

        fig = self.create_topomap(
            band_name
        )

        tmp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        )

        fig.savefig(
            tmp.name,
            dpi=300,
            bbox_inches="tight"
        )

        plt.close(fig)

        return tmp.name

    def get_band_summary(
        self,
        band_name="Alpha"
    ):

        powers = (
            self.compute_band_power_all_channels(
                band_name
            )
        )

        max_idx = np.argmax(
            powers
        )

        min_idx = np.argmin(
            powers
        )

        return {
            "highest_channel":
                self.raw.ch_names[max_idx],

            "highest_power":
                float(
                    powers[max_idx]
                ),

            "lowest_channel":
                self.raw.ch_names[min_idx],

            "lowest_power":
                float(
                    powers[min_idx]
                )
        }

    def plot_brain_topomap(
        self,
        band_name="Alpha",
        time_point=0.0,
        max_volt=10.0,
        auto_scale=False
    ):
        raw_filtered = get_cached_filtered_data(
            self.raw,
            id(self.raw),
            band_name
        )

        sfreq = raw_filtered.info["sfreq"]
        times = raw_filtered.times
        idx = int(np.clip(round(time_point * sfreq), 0, len(times) - 1))

        voltages = raw_filtered.get_data()[:, idx] * 1e6

        valid_picks = []
        seen_locs = set()
        for i, ch in enumerate(raw_filtered.info['chs']):
            loc = ch['loc'][:3]
            if np.all(loc == 0) or np.any(np.isnan(loc)):
                continue
            loc_tuple = (round(loc[0], 4), round(loc[1], 4), round(loc[2], 4))
            if loc_tuple in seen_locs:
                continue
            seen_locs.add(loc_tuple)
            valid_picks.append(i)

        if not valid_picks:
            fig = go.Figure()
            fig.add_annotation(
                text="No channels with valid, unique coordinates found.",
                showarrow=False,
                font=dict(size=14, color="red")
            )
            fig.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False)
            )
            return fig

        valid_voltages = voltages[valid_picks]
        valid_ch_names = [raw_filtered.ch_names[i] for i in valid_picks]

        from mne.channels.layout import _find_topomap_coords
        coords = _find_topomap_coords(raw_filtered.info, valid_picks)

        # Center coordinates
        x_min, y_min = coords.min(axis=0)
        x_max, y_max = coords.max(axis=0)
        x_center = (x_min + x_max) / 2.0
        y_center = (y_min + y_max) / 2.0

        coords[:, 0] -= x_center
        coords[:, 1] -= y_center

        # Scale and offset to fit the head and brain outline in the background image
        coords[:, 0] *= 7.3
        coords[:, 1] *= 7.3
        coords[:, 1] -= 0.08

        df = pd.DataFrame({
            "x": coords[:, 0],
            "y": coords[:, 1],
            "voltage": valid_voltages,
            "Channel": valid_ch_names
        })

        if auto_scale:
            max_volt = float(np.max(np.abs(valid_voltages)))
            if max_volt == 0:
                max_volt = 10.0

        image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "brain_top_down.png"
        )
        image_data_url = ""
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            image_data_url = f"data:image/png;base64,{encoded}"

        fig = go.Figure()

        if image_data_url:
            fig.add_layout_image(
                dict(
                    source=image_data_url,
                    xref="x",
                    yref="y",
                    x=-1.0,
                    y=1.0,
                    sizex=2.0,
                    sizey=2.0,
                    sizing="contain",
                    opacity=0.7,
                    layer="below"
                )
            )

        fig.add_trace(
            go.Scatter(
                x=df["x"],
                y=df["y"],
                mode="markers+text",
                marker=dict(
                    size=26,
                    color=df["voltage"],
                    colorscale="RdBu_r",
                    cmin=-max_volt,
                    cmax=max_volt,
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="µV", side="top"),
                        ticks="outside",
                        thickness=15,
                        len=0.7
                    ),
                    line=dict(width=1, color="rgba(100, 100, 100, 0.5)")
                ),
                text=df["Channel"],
                textposition="middle center",
                textfont=dict(
                    size=8,
                    color="black",
                    family="Arial Black, Gadget, sans-serif"
                ),
                hoverinfo="text",
                hovertext=[
                    f"Channel: {row['Channel']}<br>Voltage: {row['voltage']:.2f} µV"
                    for _, row in df.iterrows()
                ]
            )
        )

        fig.update_layout(
            xaxis=dict(
                range=[-1.05, 1.05],
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True
            ),
            yaxis=dict(
                range=[-1.05, 1.05],
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                fixedrange=True,
                scaleanchor="x",
                scaleratio=1
            ),
            width=650,
            height=600,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        return fig