"""Attempt CHIRP serial detection where supported."""

from __future__ import annotations

import serial
from chirp import chirp_common, directory, errors

from chirpctl.chirp_config import load_chirp_hints
from chirpctl.ports import port_exists


def detect_port(port: str) -> dict[str, object]:
    if not port_exists(port):
        return {
            "ok": False,
            "port": port,
            "detected": None,
            "message": f"Port not found: {port}",
            "hint": None,
        }

    directory.import_drivers()
    hints = load_chirp_hints()
    hint_driver = hints.last_driver if hints.last_port == port else None

    try:
        from chirp import detect as chirp_detect

        md = chirp_detect.detect_icom_radio(port)
        icom_model = getattr(md, "MODEL", None)
        if icom_model:
            return {
                "ok": True,
                "port": port,
                "detected": icom_model,
                "method": "icom_id",
                "hint": None,
            }
    except Exception:
        pass

    for rclass in directory.DRV_TO_RADIO.values():
        if not issubclass(rclass, chirp_common.CloneModeRadio):
            continue
        if not hasattr(rclass, "detect_from_serial"):
            continue
        pipe = None
        try:
            pipe = serial.Serial(port=port, timeout=0.5)
            detected_cls = rclass.detect_from_serial(pipe)
            dname = directory.get_driver(detected_cls)
            return {
                "ok": True,
                "port": port,
                "detected": dname,
                "method": "detect_from_serial",
                "hint": hint_driver,
            }
        except NotImplementedError:
            continue
        except errors.RadioError:
            continue
        except Exception:
            continue
        finally:
            if pipe is not None and pipe.is_open:
                pipe.close()

    msg = "Cannot auto-identify this radio on the serial port."
    if hint_driver:
        msg += f" CHIRP GUI last used {hint_driver} on this port."
    return {
        "ok": True,
        "port": port,
        "detected": hint_driver,
        "method": "chirp_gui_hint" if hint_driver else None,
        "message": msg,
        "hint": hint_driver,
    }
