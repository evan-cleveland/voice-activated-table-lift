
#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from gpiozero import DigitalOutputDevice as DO

#try:
#    import serial
#except ImportError:
#    print("Missing pyserial. Install with: sudo apt install python3-serial", file=sys.stderr)
#    sys.exit(1)


CONFIG_PATH = Path("voice_config.json")

command_codes = {'EXTEND': '01', 'RETRACT': '10', 'STOP': '11', 'NULL': '00'}

def load_config(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    required_top = [
#        "serial_port",
#        "baud_rate",
        "cooldown_seconds",
        "allow_repeat_stop",
        "pocketsphinx_binary",
        "keywords_file",
        "keywords",
    ]
    for key in required_top:
        if key not in cfg:
            raise ValueError(f"Missing config key: {key}")

    if not isinstance(cfg["keywords"], list) or not cfg["keywords"]:
        raise ValueError("Config 'keywords' must be a non-empty list")

    for i, item in enumerate(cfg["keywords"]):
        for key in ("phrase", "threshold", "command"):
            if key not in item:
                raise ValueError(f"Keyword entry {i} missing key: {key}")

    return cfg


def build_keyword_file(cfg):
    kw_path = Path(cfg["keywords_file"])
    lines = []
    phrase_to_command = {}

    for item in cfg["keywords"]:
        phrase = item["phrase"].strip().lower()
        threshold = str(item["threshold"]).strip()
        command = item["command"].strip().upper()

        if not phrase:
            continue

        lines.append(f"{phrase} /{threshold}/")
        phrase_to_command[phrase] = command

    kw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return kw_path, phrase_to_command


#def open_serial(port, baud_rate):
 #   while True:
 #       try:
 #           ser = serial.Serial(port, baud_rate, timeout=1)
 #           print(f"[SERIAL] Connected to {port} @ {baud_rate}")
 #           time.sleep(2.0)  # allow ESP32 reset if using USB serial
 #           return ser
 #       except Exception as e:
 #           print(f"[SERIAL] Failed to open {port}: {e}")
 #           print("[SERIAL] Retrying in 2 seconds...")
 #           time.sleep(2)


def send_command(o1, o0, command):
 #   msg = command.strip().upper() + "\n"
 #   ser.write(msg.encode("utf-8"))
#    ser.flush()
#    print(f"[SEND] {msg.strip()}")
    code = str(command_codes[command])
    if code[0]=='1':
        o1.on()
    else:
        o1.off()

    if code[1]=='1':
        o0.on()
    else:
        o0.off()

def start_pocketsphinx(binary, kw_path, audio_device=None):
    cmd = [binary, "-inmic", "yes", "-kws", str(kw_path)]
    if audio_device:
        cmd.extend(["-adcdev", str(audio_device)])
    print("[PS] Starting:", " ".join(cmd))
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )


def start_arecord_pocketsphinx(cfg, kw_path):
    audio_device = cfg.get("audio_device") or "plughw:0,0"
    rate = str(cfg.get("audio_rate", 16000))
    channels = str(cfg.get("audio_channels", 1))
    fmt = str(cfg.get("audio_format", "S16_LE"))
    buffer_time = str(cfg.get("audio_buffer_time_us", 500000))

    arecord_cmd = [
        "arecord",
        "-D", str(audio_device),
        "-c", channels,
        "-r", rate,
        "-f", fmt,
        "-t", "raw",
        "--buffer-time", buffer_time,
    ]
    ps_cmd = [
        cfg["pocketsphinx_binary"],
        "-infile", "/dev/stdin",
        "-kws", str(kw_path),
        "-samprate", rate,
    ]

    print("[AUDIO] Starting:", " ".join(arecord_cmd))
    print("[PS] Starting:", " ".join(ps_cmd))

    arecord = subprocess.Popen(
        arecord_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    ps = subprocess.Popen(
        ps_cmd,
        stdin=arecord.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    if arecord.stdout is not None:
        arecord.stdout.close()
    return ps, arecord


def main():
    cfg = load_config(CONFIG_PATH)
    kw_path, phrase_to_command = build_keyword_file(cfg)

    S1 = DO(17)
    S0 = DO(27)
    #ser = open_serial(cfg["serial_port"], cfg["baud_rate"])
    arecord = None
    if cfg.get("audio_backend") == "arecord_pipe":
        ps, arecord = start_arecord_pocketsphinx(cfg, kw_path)
    else:
        ps = start_pocketsphinx(cfg["pocketsphinx_binary"], kw_path, cfg.get("audio_device"))

    last_sent_time = {}
    cooldown = float(cfg["cooldown_seconds"])
    allow_repeat_stop = bool(cfg["allow_repeat_stop"])

    try:
        assert ps.stdout is not None

        for raw_line in ps.stdout:
            line = raw_line.strip()
            if not line:
                continue

            print(f"[PS] {line}")

            spoken = line.lower().strip()

            if spoken in phrase_to_command:
                command = phrase_to_command[spoken]
                now = time.time()
                last_time = last_sent_time.get(command, 0)

                if command == "STOP" and allow_repeat_stop:
                    send_command(S1, S0, command)
                    last_sent_time[command] = now
                    continue

                if now - last_time >= cooldown:
                    send_command(S1, S0, command)
                    last_sent_time[command] = now
                else:
                    print(f"[SKIP] Cooldown active for {command}")

    except KeyboardInterrupt:
        print("\n[EXIT] Stopping...")
    finally:
        try:
            send_command(S1, S0, "STOP")
        except Exception:
            pass

        try:
            if ps.poll() is None:
                ps.terminate()
                time.sleep(1)
                if ps.poll() is None:
                    ps.kill()
        except Exception:
            pass

        try:
            if arecord is not None and arecord.poll() is None:
                arecord.terminate()
                time.sleep(1)
                if arecord.poll() is None:
                    arecord.kill()
        except Exception:
            pass

#        try:
#            ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
