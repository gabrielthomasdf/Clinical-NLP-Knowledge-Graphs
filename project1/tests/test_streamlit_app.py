from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_live_analysis_without_exceptions():
    app = Path(__file__).resolve().parents[2] / "streamlit_app.py"
    page = AppTest.from_file(app, default_timeout=10).run()

    assert not page.exception
    assert page.text_area[0].value.startswith("The fictional patient")
    assert [metric.value for metric in page.metric] == ["6", "8", "7", "8"]

    page.text_area[0].set_value(
        "The fictional patient reported chest pain and fatigue. An MRI was performed."
    )
    page.button[0].click().run()

    assert not page.exception
    assert [metric.value for metric in page.metric[:2]] == ["3", "3"]
