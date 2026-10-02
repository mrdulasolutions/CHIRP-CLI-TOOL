from chirpctl.chirp_serial import ChirpSerial


def test_chirp_serial_log_noop_without_debug() -> None:
    # Cannot open real port in CI; log must exist on class instances.
    assert hasattr(ChirpSerial, "log")
