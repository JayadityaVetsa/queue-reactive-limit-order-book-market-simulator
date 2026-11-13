from pathlib import Path
import runpy


def test_source_hashes_ignore_checkout_line_endings_and_use_portable_paths(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts/alpha_experiment.py"
    function = runpy.run_path(str(script))["source_hashes"]
    function.__globals__["ROOT"] = tmp_path
    portable_script = tmp_path / "scripts/alpha_experiment.py"
    portable_script.parent.mkdir()
    portable_script.write_bytes(b"# fixture\n")
    function.__globals__["__file__"] = str(portable_script)
    source = tmp_path / "src/lob_sim/example.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"x = 1\ny = 2\n")
    unix = function()
    source.write_bytes(b"x = 1\r\ny = 2\r\n")
    windows = function()
    assert unix == windows
    assert "src/lob_sim/example.py" in windows
    assert all("\\" not in key for key in windows)
