import streamlit as st
import importlib
import os

import modules.loader
import modules.load_utils
import modules.overview
import modules.signal_viewer
import modules.frequency
import modules.spectrogram
import modules.topomap

importlib.reload(modules.loader)
importlib.reload(modules.load_utils)
importlib.reload(modules.overview)
importlib.reload(modules.signal_viewer)
importlib.reload(modules.frequency)
importlib.reload(modules.spectrogram)
importlib.reload(modules.topomap)

from modules.loader import EEGLoader
from modules.load_utils import save_uploaded_file

from modules.overview import EEGOverview
from modules.signal_viewer import EEGSignalViewer
from modules.frequency import EEGFrequencyAnalyzer
from modules.spectrogram import EEGSpectrogram
from modules.topomap import EEGTopomap

st.set_page_config(
    page_title="EEG Signal Explorer",
    layout="wide"
)

st.title("🧠 EEG Signal Explorer")

uploaded_file = st.file_uploader(
    "Upload EEG File",
    type=["edf", "fif", "set", "vhdr"]
)

file_path = None
if uploaded_file is not None:
    file_path = save_uploaded_file(uploaded_file)
else:
    query_file = st.query_params.get("file")
    if query_file and os.path.exists(query_file):
        file_path = query_file

if file_path is not None:
    loader = EEGLoader()
    raw = loader.load(file_path)

    page = st.sidebar.radio(
        "Navigation",
        [
            "Overview",
            "Signal Viewer",
            "Frequency Analysis",
            "Spectrogram",
            "Topographic Maps"
        ]
    )


    # OVERVIEW

    if page == "Overview":

        overview = EEGOverview(raw)

        info = overview.get_basic_info()

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Channels",
            info["channels"]
        )

        c2.metric(
            "Sampling Rate",
            info["sampling_rate"]
        )

        c3.metric(
            "Duration (min)",
            round(
                info["duration_min"],
                2
            )
        )

        quality = (
            overview.get_quality_snapshot()
        )

        st.metric(
            "Quality Score",
            f"{quality['quality_score']}%"
        )

        st.plotly_chart(
            overview.create_variance_plot(),
            use_container_width=True
        )

        st.plotly_chart(
            overview.create_amplitude_distribution(),
            use_container_width=True
        )


    # SIGNAL VIEWER

    elif page == "Signal Viewer":

        viewer = EEGSignalViewer(raw)

        channel = st.selectbox(
            "Channel",
            raw.ch_names
        )

        start_sec = st.slider(
            "Start Time",
            0,
            int(raw.times[-1]),
            0
        )

        end_sec = st.slider(
            "End Time",
            start_sec + 1,
            int(raw.times[-1]),
            min(
                start_sec + 10,
                int(raw.times[-1])
            )
        )

        st.plotly_chart(
            viewer.plot_single_channel(
                channel,
                start_sec,
                end_sec
            ),
            use_container_width=True
        )


    # FREQUENCY

    elif page == "Frequency Analysis":

        freq = EEGFrequencyAnalyzer(
            raw
        )

        channel = st.selectbox(
            "Channel",
            raw.ch_names
        )

        st.plotly_chart(
            freq.plot_psd(channel),
            use_container_width=True
        )

        st.plotly_chart(
            freq.plot_band_power(channel),
            use_container_width=True
        )

        st.plotly_chart(
            freq.plot_relative_band_power(
                channel
            ),
            use_container_width=True
        )

        dominant = (
            freq.get_dominant_band(
                channel
            )
        )

        st.success(
            f"Dominant Band: {dominant}"
        )


    # SPECTROGRAM

    elif page == "Spectrogram":

        spec = EEGSpectrogram(
            raw
        )

        channel = st.selectbox(
            "Channel",
            raw.ch_names
        )

        st.plotly_chart(
            spec.plot_spectrogram(
                channel
            ),
            use_container_width=True
        )

        st.plotly_chart(
            spec.plot_band_activity(
                channel
            ),
            use_container_width=True
        )

    elif page == "Topographic Maps":

        topo = EEGTopomap(raw)
        duration_sec = float(raw.times[-1])

        # Columns for controls
        c1, c2, c3, c4 = st.columns([2.5, 3.5, 3.0, 2.0])

        with c1:
            band_selection = st.selectbox(
                "Frequency Band",
                [
                    "Delta (0.5 - 4 Hz)",
                    "Theta (4 - 8 Hz)",
                    "Alpha (8 - 13 Hz)",
                    "Beta (13 - 30 Hz)",
                    "Gamma (30 - 45 Hz)"
                ],
                index=2 
            )
            # Extract clean band name
            band = band_selection.split(" ")[0]

        with c2:
            time_point = st.slider(
                "Time Point",
                min_value=0.0,
                max_value=duration_sec,
                value=0.0,
                step=0.04,
                key="time_point_slider"
            )

        with c3:
            scale_option = st.selectbox(
                "Scale (µV)",
                [5, 10, 20, 50, "Auto"],
                index=1 
            )
            
            max_volt_disp = 10.0 if scale_option == "Auto" else scale_option
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; align-items: center; width: 100%; margin-top: -5px;">
                    <div style="background: linear-gradient(to right, blue, cyan, green, yellow, red); height: 8px; width: 100%; border-radius: 4px;"></div>
                    <div style="display: flex; justify-content: space-between; width: 100%; font-size: 10px; color: #888; margin-top: 2px;">
                        <span>-{max_volt_disp}</span>
                        <span>0</span>
                        <span>{max_volt_disp}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c4:
            view_mode = st.selectbox(
                "View",
                ["Brain", "Sensor"],
                index=0
            )

        if view_mode == "Brain":
            
            # Plotly Brain map
            auto_scale = (scale_option == "Auto")
            max_volt = 10.0 if auto_scale else float(scale_option)
            fig = topo.plot_brain_topomap(
                band_name=band,
                time_point=time_point,
                max_volt=max_volt,
                auto_scale=auto_scale
            )
            st.plotly_chart(
                fig,
                use_container_width=True
            )
        else:

            image_path = topo.save_topomap(band)
            st.image(image_path)

        summary = topo.get_band_summary(band)
        
        col_sum1, col_sum2 = st.columns(2)
        with col_sum1:
            st.info(f"💡 **Highest Activity:** Channel **{summary['highest_channel']}** ({summary['highest_power']:.2e} V²/Hz)")
        with col_sum2:
            st.warning(f"📉 **Lowest Activity:** Channel **{summary['lowest_channel']}** ({summary['lowest_power']:.2e} V²/Hz)")


