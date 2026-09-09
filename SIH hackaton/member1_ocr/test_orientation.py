import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ocr_engine
import preprocessing


def test_quarter_turn_points_map_back_to_source():
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    source_point = np.array([[20, 30]], dtype=np.float32)

    for angle in (0, 90, 180, 270):
        rotated, matrix = preprocessing.rotate_orientation(image, angle)
        source_to_candidate = cv2.invertAffineTransform(matrix)
        candidate_point = cv2.transform(
            source_point.reshape(1, 1, 2),
            source_to_candidate
        )
        round_trip = preprocessing.map_points_to_original(
            candidate_point.reshape(-1, 2),
            {
                "orientation_matrix": matrix,
                "rotation_matrix": None,
                "scale_x": 1.0,
                "scale_y": 1.0
            }
        )

        assert rotated.size > 0
        assert np.allclose(round_trip, source_point, atol=0.01)


def test_quality_score_prefers_readable_horizontal_labeled_output():
    horizontal_page = [
        ([[0, 0], [100, 0], [100, 20], [0, 20]], ("MFG DATE DEC2024", 0.95)),
        ([[0, 30], [100, 30], [100, 50], [0, 50]], ("BATCH NO BAR4L027", 0.95)),
    ]
    vertical_page = [
        ([[0, 0], [20, 0], [20, 100], [0, 100]], ("MFG", 0.55)),
    ]

    assert ocr_engine._ocr_quality_score(horizontal_page) > (
        ocr_engine._ocr_quality_score(vertical_page)
    )


def test_run_ocr_selects_orientation_and_maps_bbox(monkeypatch, tmp_path):
    image_path = tmp_path / "rotated.png"
    cv2.imwrite(str(image_path), np.zeros((100, 200, 3), dtype=np.uint8))

    class FakeOCR:
        def __init__(self):
            self.calls = 0

        def ocr(self, image, cls=True):
            self.calls += 1

            if self.calls == 2:
                page = [
                    (
                        [[20, 30], [80, 30], [80, 45], [20, 45]],
                        ("MFG DATE DEC2024", 0.98)
                    )
                ]
            else:
                page = [
                    (
                        [[20, 30], [35, 30], [35, 90], [20, 90]],
                        ("MFG", 0.55)
                    )
                ]

            return [page]

    fake_ocr = FakeOCR()
    monkeypatch.setattr(ocr_engine, "get_ocr_instance", lambda: fake_ocr)
    monkeypatch.setattr(ocr_engine.config, "USE_ORIENTATION_SEARCH", True)
    monkeypatch.setattr(ocr_engine.config, "ORIENTATION_ANGLES", (0, 90))
    monkeypatch.setattr(ocr_engine.config, "PREPROCESS_STEPS", {})

    result = ocr_engine.run_ocr(str(image_path), use_preprocessed=False)

    assert fake_ocr.calls == 2
    assert result["engine"] == "paddle"
    assert result["image_size"] == {"width": 200, "height": 100}
    assert result["full_text"] == "MFG DATE DEC2024"
    assert result["regions"][0]["bbox"] == {
        "x": 30,
        "y": 19,
        "width": 15,
        "height": 60
    }
