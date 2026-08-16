from app.pdf_loader import infer_quarter


def test_filename_quarter_detection():
    assert infer_quarter("HCLTech_Q3_FY25.pdf", "anything") == "Q3 FY25"


def test_text_quarter_detection():
    assert infer_quarter("report.pdf", "Financial results for the quarter ended June 30, 2024") == "Q1 FY25"
    assert infer_quarter("report.pdf", "Financial results for the quarter ended September 30, 2024") == "Q2 FY25"
    assert infer_quarter("report.pdf", "Financial results for the quarter ended December 31, 2024") == "Q3 FY25"
    assert infer_quarter("report.pdf", "Financial results for the quarter and year ended March 31, 2025") == "Q4 FY25"
