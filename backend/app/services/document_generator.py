import io
import csv
import re
from typing import Optional, Dict, Any, List
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from app.models.report import Report
from app.models.project import Project
from app.models.idea import Idea
from app.models.evaluation import Evaluation


class DocumentGenerator:
    """Exports structured reports to PDF, DOCX, Markdown, LaTeX, and CSV."""

    @staticmethod
    def _clean_for_reportlab(text: str) -> str:
        """Converts markdown tags and escapes XML chars for safe ReportLab Paragraph parsing."""
        # 1. Escape XML characters
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # 2. Markdown bold **text** -> <b>text</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # 3. Markdown italic *text* -> <i>text</i>
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        # 4. Markdown code `text` -> <font face="Courier">text</font>
        text = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', text)
        return text

    @staticmethod
    def to_markdown(report: Report) -> str:
        """Returns clean Markdown formatted string with metadata."""
        header = f"# {report.title}\n\n"
        meta = f"**Document Type**: {report.report_type.replace('_', ' ').title()}  \n"
        meta += f"**Generated**: {report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  \n\n---\n\n"
        return header + meta + report.content_markdown

    @staticmethod
    def to_latex(report: Report) -> str:
        """Generates LaTeX document source."""
        clean_title = (
            report.title.replace("_", "\\_")
            .replace("&", "\\&")
            .replace("%", "\\%")
            .replace("#", "")
        )
        body = (
            report.content_markdown.replace("#", "")
            .replace("_", "\\_")
            .replace("&", "\\&")
            .replace("%", "\\%")
        )
        tex = [
            "\\documentclass[11pt,a4paper]{article}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage{geometry}",
            "\\geometry{margin=1in}",
            "\\usepackage{hyperref}",
            "\\usepackage{titlesec}",
            "\\title{" + clean_title + "}",
            "\\author{IdeaLens AI Research Platform}",
            "\\date{\\today}",
            "\\begin{document}",
            "\\maketitle",
            "\\begin{abstract}",
            f"Automated evaluation and publication dossier for {clean_title}.",
            "\\end{abstract}",
            "\\section{Report Overview}",
            f"\\textbf{{Report Type:}} {report.report_type}\\\\",
            "\\section{Content}",
            body,
            "\\end{document}"
        ]
        return "\n".join(tex)

    @staticmethod
    def to_docx_buffer(report: Report) -> io.BytesIO:
        """Builds a formatted Word (.docx) document with tables, headers, and styled lists."""
        doc = Document()

        # Document Title
        title_p = doc.add_heading(report.title, level=0)
        title_p.runs[0].font.color.rgb = RGBColor(20, 71, 216)  # Brand blue

        # Metadata
        meta_p = doc.add_paragraph()
        r1 = meta_p.add_run(f"Report Type: {report.report_type.replace('_', ' ').title()}\n")
        r1.bold = True
        r1.font.color.rgb = RGBColor(15, 23, 42)
        r2 = meta_p.add_run(f"Generated at: {report.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n")
        r2.font.color.rgb = RGBColor(100, 116, 139)

        doc.add_paragraph("―" * 45)

        # Parse markdown lines into headings, paragraphs, and tables
        lines = report.content_markdown.split("\n")
        table_buffer: List[List[str]] = []
        in_table = False

        for line in lines:
            stripped = line.strip()

            # Table row detection
            if stripped.startswith("|") and stripped.endswith("|"):
                # Skip divider lines like | :--- | :---: |
                if "---" in stripped:
                    in_table = True
                    continue
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                table_buffer.append(cells)
                in_table = True
                continue
            else:
                if in_table and table_buffer:
                    # Flush table buffer into docx table
                    num_rows = len(table_buffer)
                    num_cols = max(len(row) for row in table_buffer)
                    if num_cols > 0:
                        tbl = doc.add_table(rows=num_rows, cols=num_cols)
                        tbl.style = 'Table Grid'
                        for r_idx, row_data in enumerate(table_buffer):
                            for c_idx, cell_value in enumerate(row_data):
                                if c_idx < num_cols:
                                    cell = tbl.cell(r_idx, c_idx)
                                    cell.text = cell_value.replace("**", "").replace("*", "")
                                    if r_idx == 0:
                                        # Header row
                                        for p in cell.paragraphs:
                                            for run in p.runs:
                                                run.bold = True
                        doc.add_paragraph()
                    table_buffer = []
                    in_table = False

            if not stripped:
                continue

            if stripped.startswith("### "):
                doc.add_heading(stripped[4:], level=3)
            elif stripped.startswith("## "):
                doc.add_heading(stripped[3:], level=2)
            elif stripped.startswith("# "):
                doc.add_heading(stripped[2:], level=1)
            elif stripped.startswith("- ") or stripped.startswith("* "):
                clean_bullet = stripped[2:].replace("**", "").replace("`", "")
                doc.add_paragraph(clean_bullet, style='List Bullet')
            elif stripped.startswith("> "):
                p_quote = doc.add_paragraph()
                p_quote.add_run(stripped[2:]).italic = True
            else:
                clean_p = stripped.replace("**", "").replace("`", "")
                doc.add_paragraph(clean_p)

        # Flush any remaining table at the end
        if table_buffer:
            num_rows = len(table_buffer)
            num_cols = max(len(row) for row in table_buffer)
            if num_cols > 0:
                tbl = doc.add_table(rows=num_rows, cols=num_cols)
                tbl.style = 'Table Grid'
                for r_idx, row_data in enumerate(table_buffer):
                    for c_idx, cell_value in enumerate(row_data):
                        if c_idx < num_cols:
                            cell = tbl.cell(r_idx, c_idx)
                            cell.text = cell_value.replace("**", "").replace("*", "")
                            if r_idx == 0:
                                for p in cell.paragraphs:
                                    for run in p.runs:
                                        run.bold = True

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def to_pdf_buffer(report: Report) -> io.BytesIO:
        """Builds a styled PDF document using ReportLab with tables and headers."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1447d8'),
            spaceAfter=8
        )

        meta_style = ParagraphStyle(
            'CustomMeta',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=14
        )

        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#0f266e'),
            spaceBefore=12,
            spaceAfter=6
        )

        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=8,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=6
        )

        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#1e293b'),
            leftIndent=12,
            spaceAfter=3
        )

        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor('#0f172a')
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#ffffff')
        )

        story = []
        story.append(Paragraph(report.title, title_style))
        story.append(
            Paragraph(
                f"IdeaLens Innovation Report • {report.report_type.replace('_', ' ').title()} • {report.created_at.strftime('%Y-%m-%d')}",
                meta_style
            )
        )
        story.append(Spacer(1, 8))

        # Parse markdown lines into PDF elements and tables
        lines = report.content_markdown.split("\n")
        table_buffer: List[List[str]] = []
        in_table = False

        for line in lines:
            s = line.strip()

            # Table row parsing
            if s.startswith("|") and s.endswith("|"):
                if "---" in s:
                    in_table = True
                    continue
                cells = [c.strip() for c in s.strip("|").split("|")]
                table_buffer.append(cells)
                in_table = True
                continue
            else:
                if in_table and table_buffer:
                    # Construct ReportLab Table
                    pdf_table_data = []
                    for r_idx, row in enumerate(table_buffer):
                        pdf_row = []
                        for cell_text in row:
                            clean_text = cell_text.replace("**", "").replace("*", "")
                            st = table_header_style if r_idx == 0 else table_cell_style
                            pdf_row.append(Paragraph(clean_text, st))
                        pdf_table_data.append(pdf_row)

                    if pdf_table_data:
                        t = Table(pdf_table_data, colWidths=None)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 6))

                    table_buffer = []
                    in_table = False

            if not s:
                continue

            # Headings & Bullets
            if s.startswith("### "):
                clean = re.sub(r'[*_`#]', '', s[4:])
                story.append(Paragraph(DocumentGenerator._clean_for_reportlab(clean), h3_style))
            elif s.startswith("## "):
                clean = re.sub(r'[*_`#]', '', s[3:])
                story.append(Paragraph(DocumentGenerator._clean_for_reportlab(clean), h2_style))
            elif s.startswith("# "):
                clean = re.sub(r'[*_`#]', '', s[2:])
                story.append(Paragraph(DocumentGenerator._clean_for_reportlab(clean), title_style))
            elif s.startswith("- ") or s.startswith("* "):
                bullet_text = DocumentGenerator._clean_for_reportlab(s[2:].strip())
                story.append(Paragraph(f"&bull; {bullet_text}", bullet_style))
            elif s.startswith("> "):
                clean_quote = s[2:].replace("[!NOTE]", "Note:").replace("[!WARNING]", "Notice:")
                quote_text = DocumentGenerator._clean_for_reportlab(clean_quote)
                story.append(Paragraph(f"<i>{quote_text}</i>", body_style))
            else:
                body_text = DocumentGenerator._clean_for_reportlab(s)
                story.append(Paragraph(body_text, body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def to_evaluation_csv_buffer(
        project: Project,
        ideas: List[Idea],
        evaluations: List[Evaluation]
    ) -> io.BytesIO:
        """
        Builds a structured CSV export containing all idea scores,
        grades, 10 dimension scores, strengths, and risks.
        """
        # Map evaluation by idea_id (latest per idea)
        eval_map: Dict[int, Evaluation] = {}
        for ev in evaluations:
            if ev.idea_id not in eval_map or ev.created_at > eval_map[ev.idea_id].created_at:
                eval_map[ev.idea_id] = ev

        headers = [
            "Project ID",
            "Project Title",
            "Idea ID",
            "Idea Title",
            "Is Selected",
            "Composite Score",
            "Grade",
            "Strategic Recommendation",
            "Problem Significance",
            "Target User Clarity",
            "Technical Feasibility",
            "Implementation Complexity",
            "Estimated Development Cost",
            "Adoption Potential",
            "Competitive Differentiation",
            "Novelty Distance",
            "Security Privacy Risks",
            "Evidence Quality Confidence",
            "Key Strengths",
            "Key Risks",
            "Evaluation Timestamp"
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)

        for idea in ideas:
            ev = eval_map.get(idea.id)
            dim_scores = ev.dimension_scores if ev else {}
            score = ev.overall_score if ev else None
            grade = ("A" if score >= 80 else ("B" if score >= 65 else ("C" if score >= 50 else "D"))) if score is not None else "N/A"
            rec = ("Recommended for Prototyping" if score >= 65 else "Requires Refinement") if score is not None else "Not Evaluated"
            strengths_list = ev.strengths if ev and isinstance(ev.strengths, list) else []
            risks_list = ev.risks if ev and isinstance(ev.risks, list) else []

            row = [
                project.id,
                project.title,
                idea.id,
                idea.title,
                "Yes" if idea.is_selected else "No",
                f"{score:.2f}" if score is not None else "N/A",
                grade,
                rec,
                dim_scores.get("problem_significance", ""),
                dim_scores.get("target_user_clarity", ""),
                dim_scores.get("technical_feasibility", ""),
                dim_scores.get("implementation_complexity", ""),
                dim_scores.get("estimated_development_cost", ""),
                dim_scores.get("adoption_potential", ""),
                dim_scores.get("competitive_differentiation", ""),
                dim_scores.get("novelty_distance", ""),
                dim_scores.get("security_privacy_risks", ""),
                dim_scores.get("evidence_quality", ""),
                "; ".join(strengths_list),
                "; ".join(risks_list),
                ev.created_at.isoformat() if ev else ""
            ]
            writer.writerow(row)

        buffer = io.BytesIO()
        buffer.write(output.getvalue().encode("utf-8-sig"))  # UTF-8 with BOM for Excel compatibility
        buffer.seek(0)
        return buffer
