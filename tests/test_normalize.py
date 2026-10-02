from chirpctl.csv_normalize import CHIRP_HEADERS, normalize_csv_text


def test_crossmode_default_and_headers() -> None:
    text = "Location,Name,Frequency,Duplex,Offset,Tone,rToneFreq,cToneFreq,DtcsCode,DtcsPolarity,RxDtcsCode,Mode,TStep,Skip,Power,Comment\n1,A,146.400000,,0,Tone,88.5,88.5,023,NN,023,FM,5,,5.0W,\n"
    out, notes = normalize_csv_text(text)
    assert "CrossMode" in out
    assert "Tone->Tone" in out
    assert CHIRP_HEADERS.index("CrossMode") < CHIRP_HEADERS.index("Mode")
