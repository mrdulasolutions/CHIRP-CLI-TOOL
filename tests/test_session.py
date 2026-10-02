from chirpctl.session import _ensure_pipe_log


class _FakePipe:
    pass


def test_ensure_pipe_log_adds_noop() -> None:
    pipe = _FakePipe()
    _ensure_pipe_log(pipe)
    assert callable(pipe.log)
    pipe.log("test")  # must not raise


def test_ensure_pipe_log_preserves_existing() -> None:
    pipe = _FakePipe()
    pipe.log = lambda m: setattr(pipe, "last", m)
    _ensure_pipe_log(pipe)
    pipe.log("keep")
    assert pipe.last == "keep"
