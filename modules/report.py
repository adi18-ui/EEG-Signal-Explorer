# pyrefly: ignore [missing-import]
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from reportlab.lib import colors

import os


class EEGReportGenerator:

    def __init__(self, output_path):

        self.output_path = output_path
        self.styles = getSampleStyleSheet()

    def generate_report(
        self,
        basic_info,
        quality_summary,
        band_power_df,
        topomap_paths
    ):

        doc = SimpleDocTemplate(
            self.output_path
        )

        elements = []

        title = Paragraph(
            "EEG Analysis Report",
            self.styles["Title"]
        )

        elements.append(title)

        elements.append(
            Spacer(1, 12)
        )

        # -------------------------
        # Dataset Overview
        # -------------------------

        elements.append(
            Paragraph(
                "Dataset Overview",
                self.styles["Heading1"]
            )
        )

        overview_text = f"""
        <b>Channels:</b> {basic_info['channels']}<br/>
        <b>Sampling Rate:</b> {basic_info['sampling_rate']} Hz<br/>
        <b>Duration:</b> {round(basic_info['duration_min'],2)} min
        """

        elements.append(
            Paragraph(
                overview_text,
                self.styles["BodyText"]
            )
        )

        elements.append(
            Spacer(1, 10)
        )

        # -------------------------
        # Quality Section
        # -------------------------

        elements.append(
            Paragraph(
                "Signal Quality",
                self.styles["Heading1"]
            )
        )

        quality_text = f"""
        <b>Quality Score:</b> {quality_summary['quality_score']}<br/>
        <b>Flat Channels:</b> {', '.join(quality_summary['flat_channels']) if quality_summary['flat_channels'] else 'None'}<br/>
        <b>Noisy Channels:</b> {', '.join(quality_summary['noisy_channels']) if quality_summary['noisy_channels'] else 'None'}<br/>
        <b>Blink Count:</b> {quality_summary['blink_count']}
        """

        elements.append(
            Paragraph(
                quality_text,
                self.styles["BodyText"]
            )
        )

        elements.append(
            Spacer(1, 15)
        )

        # -------------------------
        # Band Powers
        # -------------------------

        elements.append(
            Paragraph(
                "Band Power Summary",
                self.styles["Heading1"]
            )
        )

        top_channels = (
            band_power_df
            .head(10)
            .to_string(index=False)
        )

        elements.append(
            Paragraph(
                top_channels.replace(
                    "\n",
                    "<br/>"
                ),
                self.styles["Code"]
            )
        )

        elements.append(
            PageBreak()
        )

        # -------------------------
        # Topomaps
        # -------------------------

        elements.append(
            Paragraph(
                "Topographic Maps",
                self.styles["Heading1"]
            )
        )

        for band, image_path in topomap_paths.items():

            elements.append(
                Paragraph(
                    f"{band} Band",
                    self.styles["Heading2"]
                )
            )

            if os.path.exists(
                image_path
            ):

                elements.append(
                    Image(
                        image_path,
                        width=350,
                        height=300
                    )
                )

                elements.append(
                    Spacer(1, 10)
                )

        doc.build(
            elements
        )

        return self.output_path