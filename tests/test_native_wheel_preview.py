"""Display-retry fixtures for the example recipe; live CAD proof is separate."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'examples/process-interfaces/printed-replacement-part/native-wheel-operation.py'


def capture_fixture(frames):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    function = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == 'capture_native_preview')
    events = []
    current = {'shade': 255}

    def save_image(path, *args):
        current['shade'] = frames.pop(0)
        Path(path).write_bytes(bytes([current['shade']]))
        events.append('capture')

    view = SimpleNamespace(viewAxonometric=lambda: None, fitAll=lambda: None, redraw=lambda: events.append('redraw'), saveImage=save_image)

    def get_document(name):
        assert name == 'exact-owned-document'
        events.append(name)
        return SimpleNamespace(activeView=lambda: view)

    def color(*args):
        return SimpleNamespace(red=lambda: current['shade'], green=lambda: current['shade'], blue=lambda: current['shade'])

    image = SimpleNamespace(isNull=lambda: False, width=lambda: 1200, height=lambda: 900, pixelColor=color)
    namespace = {
        'Gui': SimpleNamespace(getDocument=get_document, updateGui=lambda: events.append('update')),
        'QtWidgets': SimpleNamespace(QApplication=SimpleNamespace(processEvents=lambda: events.append('events'))),
        'QtGui': SimpleNamespace(QImage=lambda path: image),
        'QtCore': SimpleNamespace(QEventLoop=lambda: SimpleNamespace(quit=lambda: None, exec_=lambda: events.append('yield')), QTimer=SimpleNamespace(singleShot=lambda ms, callback: callback())),
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace['capture_native_preview'], SimpleNamespace(Name='exact-owned-document'), events


def test_blank_candidate_is_retained_and_only_display_is_retried(tmp_path):
    capture, doc, events = capture_fixture([255, 150])
    target = tmp_path / 'native-design.png'
    receipt = capture(doc, target)
    assert target.read_bytes() == bytes([150])
    assert (tmp_path / 'native-design-attempt-1.png').read_bytes() == bytes([255])
    assert not (tmp_path / 'native-design-attempt-2.png').exists()
    assert len(receipt['attempts']) == 2
    assert events[0] == doc.Name
    assert events.count('capture') == 2
    assert events.index('yield') < events.index('capture')
    assert 'Nonblank capture only' in receipt['scope']


def test_persistent_blank_is_a_specific_failure_with_no_final_preview(tmp_path):
    capture, doc, events = capture_fixture([255, 255, 255])
    target = tmp_path / 'native-design.png'
    with pytest.raises(RuntimeError, match='remained blank after three'):
        capture(doc, target)
    assert not target.exists()
    assert len(list(tmp_path.glob('*attempt-*.png'))) == 3
    assert events.count('capture') == 3


@pytest.mark.parametrize('filename', ['native-design.png', 'native-design-attempt-1.png'])
def test_capture_never_overwrites_prior_output_or_diagnostic(tmp_path, filename):
    existing = tmp_path / filename
    existing.write_bytes(b'old-evidence')
    capture, doc, events = capture_fixture([150])
    with pytest.raises(AssertionError, match='Preserve'):
        capture(doc, tmp_path / 'native-design.png')
    assert existing.read_bytes() == b'old-evidence'
    assert 'capture' not in events
