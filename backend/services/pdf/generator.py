"""PDF report generator — wraps existing ReportLab logic from src/report/."""
import os
from typing import Dict, List

from backend.services.analysis.models import TableData


class PDFGenerator:
    """Generate PDF reports from TableData using existing ReportLab infrastructure."""

    def generate_table(self, table_data: TableData, output_path: str) -> str:
        """Generate a PDF for a table-type analysis result.

        Delegates to the existing PDFReportGenerator.generate_generic() from
        src/report/direct_generator.py, converting TableData to the expected dict format.

        Returns the output file path.
        """
        from src.report.direct_generator import PDFReportGenerator

        # Convert TableData to the dict format expected by generate_generic
        result = self._table_data_to_dict(table_data)

        generator = PDFReportGenerator()
        return generator.generate_generic(
            result,
            output_path,
            table_title=table_data.title,
            table_id=table_data.tlf_id,
            population=table_data.population,
        )

    def generate_figure(
        self,
        figure_path: str,
        title: str,
        output_path: str,
        population: str = "",
        tlf_id: str = "",
    ) -> str:
        """Embed a matplotlib figure into a PDF page.

        Args:
            figure_path: Path to the existing figure image (PNG).
            title: Title for the figure page.
            output_path: Where to save the PDF.
            population: Analysis population label.
            tlf_id: TLF identifier.

        Returns the output file path.
        """
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(output_path, pagesize=landscape(letter))
        width, height = landscape(letter)

        # Title
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, height - inch, title)

        # TLF ID and population header
        c.setFont("Helvetica", 10)
        header_parts = []
        if tlf_id:
            header_parts.append(f"Table {tlf_id}")
        if population:
            header_parts.append(population)
        if header_parts:
            header_text = "  |  ".join(header_parts)
            c.drawString(inch, height - 1.3 * inch, header_text)

        # Embed image
        if os.path.exists(figure_path):
            img_width = width - 2 * inch
            img_height = height - 2.5 * inch
            c.drawImage(figure_path, inch, inch, width=img_width, height=img_height, preserveAspectRatio=True)

        c.save()
        return output_path

    def _table_data_to_dict(self, td: TableData) -> Dict:
        """Convert TableData back to the dict format the existing PDF generator expects."""
        units = []
        for row in td.rows:
            unit = {
                "unit": f"row_{len(units) + 1}",
                "level": row.level,
                "rowlabel": row.label,
            }
            # Map cells back to col1, col2, col3, col_total
            for i, cell in enumerate(row.cells):
                unit[f"col{i + 1}"] = cell.value
            unit["col_total"] = row.cells[-1].value if len(row.cells) > 0 else ""
            units.append(unit)

        return {
            "big_n": {str(k): v for k, v in td.big_n.groups.items()},
            "total_n": td.big_n.total,
            "units": units,
        }
