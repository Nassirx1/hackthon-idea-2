"""Generate sample CV PDF files for the first-run demo."""
import os

DEMO_DIR = os.path.join(os.path.dirname(__file__), "demo_cvs")

SAMPLE_CVS = {
    "Nasser_AlDataScience_CV.pdf": {
        "name": "Nasser Al-Example",
        "education": "BSc in Data Science | Expected Graduation: 2028",
        "location": "Saudi Arabia",
        "summary": (
            "Data Science student interested in AI systems, analytics, business-facing "
            "problem solving, and real-world automation. Passionate about building "
            "multi-agent systems and deploying ML models to solve business problems."
        ),
        "skills": (
            "Python, SQL, Pandas, Machine Learning, Data Analysis, Streamlit, "
            "Power BI, APIs, Prompt Engineering, Workflow Automation, NLP basics, "
            "Business Analysis, Presentation Skills, Agent Systems, LLM Applications, "
            "Data Preprocessing, Statistics, Experimentation, GitHub, FastAPI"
        ),
        "projects": [
            "Built a multi-agent autonomous analytics system that analyzes datasets and produces strategic business reports.",
            "Created a text-to-SQL agent for natural language database querying using LLMs and LangChain.",
            "Built dashboards and automation workflows for business processes using Streamlit and Python APIs.",
            "Developed a time series forecasting model for retail demand prediction with 92% accuracy.",
        ],
        "experience": [
            "Research Intern — AI Time Series Forecasting Lab (3 months): built forecasting pipelines, data preprocessing scripts, and visualisation dashboards.",
            "AI Automation Intern — Tech Startup (2 months): built internal tools, integrated APIs, automated reporting workflows using Python and Streamlit.",
        ],
    },
    "Sara_Analytics_CV.pdf": {
        "name": "Sara Al-Example",
        "education": "BSc in Information Systems | Expected Graduation: 2027",
        "location": "Saudi Arabia",
        "summary": (
            "Student focused on reporting, business analysis, dashboards, and "
            "communication-oriented analytics work. Experienced in creating executive "
            "dashboards, conducting market research, and supporting product teams "
            "with data-driven insights."
        ),
        "skills": (
            "Excel, SQL, Tableau, Business Analysis, Reporting, Communication, "
            "Market Research, PowerPoint, Stakeholder Management, Data Cleaning, "
            "Presentation Skills, Analytical Thinking, Strategy, Microsoft Office, "
            "Data Storytelling, Problem Solving"
        ),
        "projects": [
            "Created business dashboards for executive reporting using Tableau and Excel.",
            "Conducted customer segmentation analysis to identify high-value customer groups.",
            "Built reporting workflows for operations teams, reducing manual effort by 40%.",
            "Produced a market research report comparing competitors across 5 product dimensions.",
        ],
        "experience": [
            "Business Analyst Intern — Consulting Firm (3 months): supported product and client teams with research, slide decks, and analytical reports.",
            "Reporting and Dashboard Support Trainee — Financial Services (2 months): maintained dashboards, prepared weekly KPI summaries for senior leadership.",
        ],
    },
}


def _create_pdf_fpdf(filepath: str, cv: dict):
    try:
        from fpdf import FPDF

        class CV_PDF(FPDF):
            def header(self):
                self.set_fill_color(30, 60, 120)
                self.rect(0, 0, 210, 18, "F")
                self.set_font("Helvetica", "B", 16)
                self.set_text_color(255, 255, 255)
                self.cell(0, 14, "FURSI - Candidate CV", align="C", ln=True)
                self.set_text_color(0, 0, 0)
                self.ln(4)

        pdf = CV_PDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # Name
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(30, 60, 120)
        pdf.cell(0, 10, cv["name"], ln=True)
        pdf.set_text_color(0, 0, 0)

        # Meta
        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 6, f"{cv['education']}    |    {cv['location']}", ln=True)
        pdf.ln(4)

        def section_title(title: str):
            pdf.set_fill_color(240, 244, 255)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 60, 120)
            pdf.cell(0, 8, title, ln=True, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)

        def body_text(text: str):
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 6, text)
            pdf.ln(2)

        def bullet_list(items: list[str]):
            pdf.set_font("Helvetica", size=10)
            for item in items:
                pdf.cell(6, 6, "-", ln=False)
                pdf.multi_cell(0, 6, item)
            pdf.ln(2)

        # Summary
        section_title("Profile Summary")
        body_text(cv["summary"])

        # Skills
        section_title("Skills")
        body_text(cv["skills"])

        # Projects
        section_title("Projects")
        bullet_list(cv["projects"])

        # Experience
        section_title("Work Experience")
        bullet_list(cv["experience"])

        pdf.output(filepath)
        return True
    except Exception as e:
        print(f"[create_demo_pdfs] fpdf2 failed: {e}")
        return False


def _create_pdf_reportlab(filepath: str, cv: dict):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib.units import mm

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )
        styles = getSampleStyleSheet()

        heading1 = ParagraphStyle(
            "Heading1Custom",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1e3c78"),
            spaceAfter=4,
        )
        heading2 = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#1e3c78"),
            spaceBefore=8,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=4,
        )

        story = []
        story.append(Paragraph(cv["name"], heading1))
        story.append(Paragraph(f"{cv['education']} | {cv['location']}", body_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3c78")))
        story.append(Spacer(1, 8))

        def add_section(title: str, content):
            story.append(Paragraph(title, heading2))
            if isinstance(content, str):
                story.append(Paragraph(content, body_style))
            else:
                for item in content:
                    story.append(Paragraph(f"• {item}", body_style))
            story.append(Spacer(1, 6))

        add_section("Profile Summary", cv["summary"])
        add_section("Skills", cv["skills"])
        add_section("Projects", cv["projects"])
        add_section("Work Experience", cv["experience"])

        doc.build(story)
        return True
    except Exception as e:
        print(f"[create_demo_pdfs] reportlab failed: {e}")
        return False


def _create_pdf_minimal(filepath: str, cv: dict):
    """Last-resort: create a minimal valid PDF manually."""
    lines = [
        cv["name"],
        cv["education"] + "  |  " + cv["location"],
        "",
        "PROFILE SUMMARY",
        cv["summary"],
        "",
        "SKILLS",
        cv["skills"],
        "",
        "PROJECTS",
    ] + ["- " + p for p in cv["projects"]] + [
        "",
        "WORK EXPERIENCE",
    ] + ["- " + e for e in cv["experience"]]

    content = "\n".join(lines)
    # Encode content as a simple PDF text stream
    pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

4 0 obj
<< /Length {len(content) + 200} >>
stream
BT
/F1 10 Tf
40 800 Td
14 TL
"""
    # Each line as a PDF text line
    text_lines = []
    for line in lines[:60]:  # limit pages
        safe = line.replace("\\", "").replace("(", "").replace(")", "").replace("\n", " ")
        text_lines.append(f"({safe}) Tj T*")

    pdf_body = "\n".join(text_lines)
    pdf_end = """
ET
endstream
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

xref
0 6
trailer
<< /Size 6 /Root 1 0 R >>
startxref
0
%%EOF"""
    with open(filepath, "w", encoding="latin-1", errors="replace") as f:
        f.write(pdf_content + pdf_body + pdf_end)
    return True


def create_demo_pdfs() -> list[str]:
    """Create demo CV PDFs if they don't already exist. Returns list of created paths."""
    os.makedirs(DEMO_DIR, exist_ok=True)
    created: list[str] = []

    for filename, cv_data in SAMPLE_CVS.items():
        filepath = os.path.join(DEMO_DIR, filename)
        if os.path.exists(filepath):
            continue

        success = (
            _create_pdf_fpdf(filepath, cv_data)
            or _create_pdf_reportlab(filepath, cv_data)
            or _create_pdf_minimal(filepath, cv_data)
        )
        if success:
            print(f"[create_demo_pdfs] Created: {filepath}")
            created.append(filepath)
        else:
            print(f"[create_demo_pdfs] WARNING: Could not create {filename}")

    return created


def get_demo_pdf_paths() -> dict[str, str]:
    """Return {filename: full_path} for all existing demo CVs."""
    return {
        fname: os.path.join(DEMO_DIR, fname)
        for fname in SAMPLE_CVS
        if os.path.exists(os.path.join(DEMO_DIR, fname))
    }


if __name__ == "__main__":
    paths = create_demo_pdfs()
    print("Created:", paths)
