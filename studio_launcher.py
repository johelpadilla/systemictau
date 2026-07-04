#!/usr/bin/env python3
"""
Launcher for Systemic Tau Studio (Streamlit) as a native macOS app.

- Starts a local Streamlit server in the background (completely hidden).
- Opens the UI inside a native window using pywebview (WebKit on macOS).
- No external browsers (Chrome/Safari/etc.) are ever launched.
- Shows a loading page immediately, then navigates to the live server when ready.
- Single-instance guard to prevent launch storms.
- Works both in development and when frozen by PyInstaller into .app.
- Fully offline: everything runs locally, no internet required.

Intended to be the entry point for the packaged SystemicTauStudio.app.
"""

import os
import sys
import subprocess
import time
import threading
import socket
import urllib.request
import urllib.error
import atexit
import signal
import traceback
import logging

# Ultra-early raw log write (before any complex logging) so we always have something
# even if the process dies very early in frozen mode.
try:
    _early_log = os.path.expanduser("~/Library/Logs/SystemicTauStudio_early.log")
    with open(_early_log, "a") as _f:
        _f.write(f"EARLY START: frozen={getattr(sys,'frozen',False)} argv0={sys.argv[0] if sys.argv else 'none'}\n")
        _f.flush()
except Exception:
    pass

# --- Robust logging for packaged .app (critical for debugging silent crashes) ---
LOG_DIR = os.path.expanduser("~/Library/Logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "SystemicTauStudio.log")

# Use INFO for the log file by default (keeps user logs clean).
# DEBUG is still available via console when running from Terminal, or we can
# raise it later if needed for troubleshooting.
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,  # override any previous config
)

# Also log to stderr when possible (visible when run from Terminal)
_console_handler = logging.StreamHandler(sys.stderr)
_console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(_console_handler)

# ------------------------------------------------------------------
# SUPER EARLY: silence noisy matplotlib font scanning BEFORE any import.
# This prevents the huge DEBUG spam and INFO "Failed to extract font properties"
# that pollute the log file (especially after cache clear).
# ------------------------------------------------------------------
import logging as _early_log
_early_log.getLogger("matplotlib").setLevel(_early_log.WARNING)
_early_log.getLogger("matplotlib.font_manager").setLevel(_early_log.WARNING)
_early_log.getLogger("matplotlib.backends").setLevel(_early_log.WARNING)

def log(msg: str, level: str = "INFO"):
    getattr(logging, level.lower(), logging.info)(msg)
    # For frozen runs launched from Terminal we want the tag for easy filtering.
    # The StreamHandler will also emit the message (one extra line). Acceptable for debug.
    # If you want zero duplication, redirect or reconfigure the handler.
    if getattr(sys, "frozen", False):
        try:
            # Only print if we are attached to a real terminal (avoid double in some .app launches)
            if sys.stdout.isatty():
                print(f"[SystemicTauStudio] {msg}")
        except Exception:
            pass


log("=== Systemic Tau Studio launcher starting ===")
log(f"Python: {sys.version}")
log(f"sys.frozen={getattr(sys, 'frozen', False)}")

# Configure matplotlib early for frozen bundle (before any studio import triggers it).
# Critical: must use non-GUI backend because Streamlit runs user code in worker threads,
# while the main thread is owned by pywebview/Cocoa.
os.environ.setdefault("MPLBACKEND", "Agg")

_mpl_config_dir = os.path.expanduser("~/Library/Application Support/SystemicTauStudio/matplotlib")
os.makedirs(_mpl_config_dir, exist_ok=True)
os.environ["MPLCONFIGDIR"] = _mpl_config_dir
log(f"Set MPLCONFIGDIR={_mpl_config_dir} for persistent font cache")

# Force Agg backend + clean font (must be done before pyplot is imported anywhere)
try:
    import matplotlib as _mpl
    _mpl.use("Agg", force=True)
    _mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "figure.max_open_warning": 0,
        "backend": "Agg",
    })
    log("Forced matplotlib backend to Agg + DejaVu Sans (thread-safe for Streamlit inside pywebview)")
except Exception as _e:
    log(f"Could not preconfigure matplotlib: {_e}", "WARNING")

# Pre-warm font cache for DejaVu Sans (the one we force) + re-assert log levels.
# Do this after the first import but with levels already set above.
try:
    import matplotlib.font_manager as _fm
    _fm.findfont(_fm.FontProperties(family="DejaVu Sans"))
    log("Matplotlib font cache pre-warmed (will avoid slow first-plot scan)")
except Exception as _e:
    log(f"Matplotlib pre-warm note: {_e}", "WARNING")
if getattr(sys, "frozen", False):
    log(f"_MEIPASS (bundle base): {sys._MEIPASS}")
    log(f"Contents of base: {os.listdir(sys._MEIPASS)[:20] if os.path.isdir(sys._MEIPASS) else 'N/A'}")
    studio_dir = os.path.join(sys._MEIPASS, "systemictau", "studio")
    log(f"studio dir exists? {os.path.isdir(studio_dir)}")
    if os.path.isdir(studio_dir):
        log(f"studio contents sample: {os.listdir(studio_dir)[:10]}")

    # Force the bundled python interpreter to be executable. PyInstaller often ships it without +x bit.
    # This must happen early so the finder (called from the server thread) sees it as runnable.
    for pyname in ("python3__dot__12", "python", "python3", "python3.12"):
        pc = os.path.join(sys._MEIPASS, pyname)
        if os.path.exists(pc):
            try:
                os.chmod(pc, 0o755)
                log(f"chmod +x on bundled python candidate: {pc}")
            except Exception as cherr:
                log(f"chmod attempt on {pc} failed (continuing anyway): {cherr}")

def _find_embedded_python():
    """Return a real Python interpreter inside the bundle for spawning child processes.
    sys.executable in a PyInstaller .app is the bootloader (SystemicTauStudio), not a python -c runner.
    We must use the embedded python3__dot__12 (or similar) that PyInstaller includes.
    """
    if not getattr(sys, "frozen", False):
        return sys.executable
    base = sys._MEIPASS

    # Primary known name from PyInstaller macOS bundles
    candidates = [
        os.path.join(base, "python3__dot__12"),
        os.path.join(base, "python3.12"),
        os.path.join(base, "python"),
        os.path.join(base, "python3"),
    ]

    for c in candidates:
        exists = os.path.exists(c)
        isfile = os.path.isfile(c)
        islink = os.path.islink(c)
        try:
            xok = os.access(c, os.X_OK)
        except Exception:
            xok = False
        log(f"python candidate check: {c} exists={exists} isfile={isfile} islink={islink} X_OK={xok}")
        if exists and (isfile or islink or xok):
            # Relaxed check: PyInstaller mac bundles often report isfile=False for the embedded
            # python3__dot__12 (symlink / special entry) even though X_OK works.
            try:
                os.chmod(c, 0o755)
                if islink:
                    tgt = os.path.realpath(c)
                    if os.path.exists(tgt):
                        os.chmod(tgt, 0o755)
            except Exception:
                pass
            log(f"Using embedded python candidate: {c}")
            return c

    # Broad scan for anything that looks like a python interpreter in the bundle
    try:
        for name in os.listdir(base):
            if name.lower().startswith("python") and not name.endswith((".dylib", ".so", ".pyc", ".py", ".dist-info")):
                full = os.path.join(base, name)
                if os.path.exists(full):
                    log(f"broad scan found potential python: {full}")
                    try:
                        os.chmod(full, 0o755)
                    except Exception:
                        pass
                    return full
    except Exception as e:
        log(f"broad python scan failed: {e}")

    # Last attempt: derive from the bundle layout relative to the main executable
    try:
        contents_dir = os.path.dirname(os.path.dirname(sys.executable))  # .../Contents
        derived = os.path.join(contents_dir, "Frameworks", "python3__dot__12")
        if os.path.exists(derived):
            log(f"derived python from exe layout: {derived}")
            try:
                os.chmod(derived, 0o755)
            except Exception:
                pass
            return derived
    except Exception:
        pass

    log("WARNING: no embedded python found, falling back to sys.executable (child will likely re-enter launcher)", "WARNING")
    return sys.executable


def find_free_port(start=8501, end=8600):
    """Find an available localhost port."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def wait_for_server(url: str, timeout: float = 60.0) -> bool:
    """
    Poll Streamlit's health endpoint until it responds successfully.
    Uses only stdlib (urllib + socket). No extra runtime dependencies.
    """
    health_url = url.rstrip("/") + "/_stcore/health"
    root_url = url.rstrip("/")
    deadline = time.time() + timeout
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": "SystemicTauStudio/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    print(f"Server is ready (after {attempt} attempts).")
                    return True
        except (urllib.error.URLError, urllib.error.HTTPError, socket.error, OSError):
            # Fallback: some Streamlit builds respond on root even if health path varies
            try:
                req2 = urllib.request.Request(root_url, headers={"User-Agent": "SystemicTauStudio/1.0"})
                with urllib.request.urlopen(req2, timeout=1.5) as resp2:
                    if resp2.status == 200:
                        print(f"Server is ready (root fallback, after {attempt} attempts).")
                        return True
            except Exception:
                pass
        time.sleep(0.55)

    print(f"Timed out waiting for server at {url} after {timeout}s.")
    return False


_streamlit_proc = None   # global handle to the child process for clean shutdown
_window_holder = {'window': None}  # share window ref with monitor threads (run_streamlit runs in other thread)


def _cleanup_streamlit():
    """Terminate the Streamlit subprocess (or in-process thread sentinel) cleanly.

    For the in-process (daemon) path we rely on:
      - daemon=True threads (killed on process exit)
      - os._exit(0) after webview returns (bypasses slow/hanging Py_FinalizeEx)
    """
    global _streamlit_proc
    if _streamlit_proc is not None:
        try:
            print("Shutting down internal Streamlit server...")
            if _streamlit_proc == "inprocess":
                # With daemon=True the thread will be terminated when we do os._exit or process death.
                # We can only clear the marker here.
                log("In-process server: relying on daemon thread + aggressive exit for shutdown.")
            else:
                _streamlit_proc.terminate()
                _streamlit_proc.wait(timeout=6)
        except subprocess.TimeoutExpired:
            try:
                if _streamlit_proc not in (None, "inprocess"):
                    _streamlit_proc.kill()
            except Exception:
                pass
        except Exception:
            pass
        finally:
            _streamlit_proc = None


atexit.register(_cleanup_streamlit)


def _run_streamlit_server_code(port: int, script_path: str, base_for_path: str):
    """The actual server bootstrap. Used both for -c (when we have a good python) and the in-process fallback.
    We use streamlit.web.bootstrap.run + direct set_option (before any CLI) to avoid
    the "server.port does not work when global.developmentMode is true" error that the
    click-based st_main path triggers in frozen bundles.
    """
    import sys as _sys
    import os as _os
    import traceback as _traceback
    import logging as _log

    # SUPER EARLY silencing of matplotlib font spam (must be before ANY matplotlib import)
    _log.getLogger("matplotlib").setLevel(_log.WARNING)
    _log.getLogger("matplotlib.font_manager").setLevel(_log.WARNING)
    _log.getLogger("matplotlib.backends").setLevel(_log.WARNING)

    # Force non-GUI matplotlib backend VERY EARLY (before any pyplot import).
    # We run inside a worker thread; macosx backend requires main thread.
    _os.environ.setdefault("MPLBACKEND", "Agg")

    # Force BEFORE any streamlit import.
    _os.environ["STREAMLIT_GLOBAL_DEVELOPMENTMODE"] = "false"
    _os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    _os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")

    # Force Agg explicitly
    try:
        import matplotlib as _mpl
        _mpl.use("Agg", force=True)
    except Exception:
        pass

    # Pre-warm + re-assert levels (in case import triggered something)
    try:
        import matplotlib.font_manager as _fm
        _fm.findfont(_fm.FontProperties(family="DejaVu Sans"))
    except Exception:
        pass

    print("STREAMLIT_CHILD_STARTED", flush=True)
    print("CHILD_PYTHON=" + _sys.executable, flush=True)
    print("CHILD_ARGV=" + repr(_sys.argv), flush=True)
    print("CHILD_BASE_DIR=" + base_for_path, flush=True)

    # Ensure bundle root (with systemictau/ and collected streamlit) is first on path.
    if base_for_path in _sys.path:
        _sys.path.remove(base_for_path)
    _sys.path.insert(0, base_for_path)
    print("CHILD_PATH0=" + (_sys.path[0] if _sys.path else ""), flush=True)

    # Also send these key lines to the launcher log file so they appear in tail -f
    try:
        import logging as _logging
        _logging.info("STREAMLIT_CHILD_STARTED (in-process)")
        _logging.info("CHILD_PYTHON=" + _sys.executable)
    except Exception:
        pass

    # Ensure the directory containing the app.py is also on sys.path (helps its internal imports)
    script_dir = _os.path.dirname(script_path)
    if script_dir and script_dir not in _sys.path:
        _sys.path.insert(0, script_dir)

    try:
        # Set options directly on the config singleton *before* bootstrap triggers any load/check.
        import streamlit.config as _stconfig
        _stconfig.set_option("global.developmentMode", False)
        _stconfig.set_option("server.port", port)
        _stconfig.set_option("server.address", "127.0.0.1")
        _stconfig.set_option("server.headless", True)
        _stconfig.set_option("browser.gatherUsageStats", False)
        _stconfig.set_option("server.runOnSave", False)
        _stconfig.set_option("server.fileWatcherType", "none")
        _stconfig.set_option("server.enableCORS", False)
        _stconfig.set_option("server.enableXsrfProtection", False)

        print("DEV_MODE_FORCED=false via set_option", flush=True)

        from streamlit.web import bootstrap
        # Patch: bootstrap.run tries to do signal.signal(SIGTERM) inside the server thread.
        # That is illegal from non-main threads. Disable it (the main launcher already
        # handles process signals).
        import streamlit.web.bootstrap as _bs
        _bs._set_up_signal_handler = lambda server: None
        print("SIGNAL_HANDLER_PATCHED (non-main thread safe)", flush=True)

        # Correct signature for this Streamlit version:
        # run(main_script_path, is_hello, args, flag_options)
        flag_options = {
            "server.port": port,
            "server.address": "127.0.0.1",
            "server.headless": True,
            "browser.gatherUsageStats": False,
            "server.runOnSave": False,
            "server.fileWatcherType": "none",
            "global.developmentMode": False,
            "server.enableCORS": False,
            "server.enableXsrfProtection": False,
        }
        bootstrap.run(script_path, is_hello=False, args=[], flag_options=flag_options)

    except SystemExit as se:
        print(f"STREAMLIT_CHILD_SYS_EXIT code={se.code}", flush=True)
        raise
    except Exception as e:
        print("STREAMLIT_CHILD_ERROR: " + str(e), flush=True)
        _traceback.print_exc()
        _sys.exit(1)


def run_streamlit(port: int):
    """Run streamlit run (subprocess when possible, or in-process thread fallback in frozen when no separate python exe is usable)."""
    global _streamlit_proc

    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
        script = os.path.join(base, "systemictau", "studio", "app.py")
        env = os.environ.copy()
        env["PYTHONPATH"] = base + os.pathsep + env.get("PYTHONPATH", "")
        env["PYTHONUNBUFFERED"] = "1"
        python = _find_embedded_python()

        # Detect if the finder gave us back the launcher itself (the fatal re-entrancy case)
        is_bad_python = (not python or
                         "SystemicTauStudio" in os.path.basename(python) or
                         python == sys.executable)

        # Extra safety: probe the candidate with a tiny -c. If it doesn't behave like a real python
        # (e.g. python3__dot__12 in the bundle is a wrapper that re-enters the launcher script),
        # fall back to the reliable in-process thread.
        #
        # WHY WE ALMOST ALWAYS HIT IN-PROCESS:
        # The .spec uses COLLECT + BUNDLE with console=False. PyInstaller bundles libpython
        # but does not (by default) ship a standalone executable python interpreter inside
        # the .app that behaves like a normal `python -c`. The candidates often either:
        #   - don't execute -c at all, or
        #   - re-execute the launcher binary (causing recursion).
        # This is why the in-process bootstrap.run path (the one we patched) is the reliable one.
        if not is_bad_python:
            try:
                probe = subprocess.run(
                    [python, "-c", "import sys; print('PROBE_OK')"],
                    capture_output=True, text=True, timeout=3
                )
                out = (probe.stdout or "") + (probe.stderr or "")
                if "PROBE_OK" not in out:
                    log(f"Embedded python probe did not print PROBE_OK (got: {out[:100]!r}). Using in-process fallback.")
                    is_bad_python = True
            except Exception as probe_err:
                log(f"Embedded python probe failed ({probe_err}). Using in-process fallback.")
                is_bad_python = True

        if is_bad_python:
            # FALLBACK — run the server logic in a thread using the already-working Python interpreter.
            # This guarantees the server actually starts even if we can't exec a second python binary.
            log("No usable separate Python interpreter in the bundle — falling back to IN-PROCESS thread (using bootstrap.run + forced config) for Streamlit server.")
            log(f"Will serve: {script}")

            def _inprocess_server():
                try:
                    _run_streamlit_server_code(port, script, base)
                except SystemExit:
                    pass
                except Exception as e:
                    log(f"In-process server crashed: {e}", "ERROR")
                finally:
                    global _streamlit_proc
                    _streamlit_proc = None

            _streamlit_proc = "inprocess"  # sentinel so cleanup knows work is happening
            # daemon=True so Python finalization doesn't hang waiting for this thread on app exit.
            # The in-process bootstrap.run() loop will be killed abruptly on daemon thread death,
            # which is acceptable (and necessary) for .app bundle shutdown.
            t = threading.Thread(target=_inprocess_server, daemon=True)
            t.start()
            # Keep a reference so cleanup / monitors can see it if needed
            globals()['_inprocess_server_thread'] = t

            def _monitor_inprocess(th):
                th.join()
                log("In-process Streamlit server thread finished")
                try:
                    w = _window_holder.get('window')
                    if w is not None:
                        w.load_html("<h1>Server stopped</h1><p>In-process thread ended. See logs.</p>")
                except Exception:
                    pass

            threading.Thread(target=_monitor_inprocess, args=(t,), daemon=True).start()
            return  # skip the Popen path entirely
        else:
            # Good python found → use classic -c with it
            server_code = (
                "import sys, os, traceback, logging\n"
                "logging.getLogger('matplotlib').setLevel(logging.WARNING)\n"
                "logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)\n"
                "logging.getLogger('matplotlib.backends').setLevel(logging.WARNING)\n"
                "os.environ['MPLBACKEND'] = 'Agg'\n"
                "os.environ['STREAMLIT_GLOBAL_DEVELOPMENTMODE'] = 'false'\n"
                "os.environ['STREAMLIT_GLOBAL_DEVELOPMENT_MODE'] = 'false'\n"
                "print('STREAMLIT_CHILD_STARTED', flush=True)\n"
                "print('CHILD_PYTHON=' + sys.executable, flush=True)\n"
                "print('CHILD_ARGV=' + repr(sys.argv), flush=True)\n"
                f"script = {script!r}\n"
                "base_dir = os.path.dirname(os.path.dirname(os.path.dirname(script)))\n"
                "print('CHILD_BASE_DIR=' + base_dir, flush=True)\n"
                "if base_dir in sys.path:\n"
                "    sys.path.remove(base_dir)\n"
                "sys.path.insert(0, base_dir)\n"
                "print('CHILD_PATH0=' + (sys.path[0] if sys.path else ''), flush=True)\n"
                "try:\n"
                "    import streamlit.config as _stconfig\n"
                "    _stconfig.set_option('global.developmentMode', False)\n"
                "    _stconfig.set_option('server.port', " + str(port) + ")\n"
                "    _stconfig.set_option('server.address', '127.0.0.1')\n"
                "    _stconfig.set_option('server.headless', True)\n"
                "    _stconfig.set_option('browser.gatherUsageStats', False)\n"
                "    _stconfig.set_option('server.runOnSave', False)\n"
                "    _stconfig.set_option('server.fileWatcherType', 'none')\n"
                "    _stconfig.set_option('server.enableCORS', False)\n"
                "    _stconfig.set_option('server.enableXsrfProtection', False)\n"
                "    print('DEV_MODE_FORCED=false via set_option', flush=True)\n"
                "    import matplotlib as _mpl\n"
                "    _mpl.use('Agg', force=True)\n"
                "    try:\n"
                "        import matplotlib.font_manager as _fm\n"
                "        _fm.findfont(_fm.FontProperties(family='DejaVu Sans'))\n"
                "    except Exception:\n"
                "        pass\n"
                "    from streamlit.web import bootstrap\n"
                "    import streamlit.web.bootstrap as _bs\n"
                "    _bs._set_up_signal_handler = lambda server: None\n"
                "    print('SIGNAL_HANDLER_PATCHED (non-main thread safe)', flush=True)\n"
                "    flag_options = {\n"
                "        'server.port': " + str(port) + ",\n"
                "        'server.address': '127.0.0.1',\n"
                "        'server.headless': True,\n"
                "        'browser.gatherUsageStats': False,\n"
                "        'server.runOnSave': False,\n"
                "        'server.fileWatcherType': 'none',\n"
                "        'global.developmentMode': False,\n"
                "        'server.enableCORS': False,\n"
                "        'server.enableXsrfProtection': False,\n"
                "    }\n"
                "    bootstrap.run(script, is_hello=False, args=[], flag_options=flag_options)\n"
                "except Exception as e:\n"
                "    print('STREAMLIT_CHILD_ERROR: ' + str(e), flush=True)\n"
                "    traceback.print_exc()\n"
                "    sys.exit(1)\n"
            )
            cmd = [python, "-c", server_code]
    else:
        # dev
        env = os.environ.copy()
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
        env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
        python = sys.executable
        cmd = [
            python, "-m", "streamlit", "run", "src/systemictau/studio/app.py",
            f"--server.port={port}",
            "--server.address=127.0.0.1",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.runOnSave=false",
            "--server.fileWatcherType=none",
        ]

    log(f"Starting internal Systemic Tau Studio server on http://127.0.0.1:{port} ...")
    log(f"Child python chosen: {python}")
    log(f"Child command[0]: {cmd[0] if cmd else 'N/A'}")

    try:
        if os.path.isfile(python):
            os.chmod(python, 0o755)
    except Exception:
        pass

    logf = None
    try:
        logf = open(LOG_FILE, "a", buffering=1)

        _streamlit_proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        def _start_monitor_for_proc(proc, port_for_log):
            try:
                code = proc.wait()
                log(f"Streamlit child exited with code {code}")
                try:
                    w = _window_holder.get('window')
                    error_html = f"<h1>Server stopped</h1><p>Internal server exited with code {code}.</p><p>Port was {port_for_log}. See ~/Library/Logs/SystemicTauStudio.log</p>"
                    if w is not None:
                        w.load_html(error_html)
                except Exception:
                    pass
            except Exception as me:
                log(f"Monitor error: {me}")

        threading.Thread(target=_start_monitor_for_proc, args=(_streamlit_proc, port), daemon=True).start()

        for line in _streamlit_proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            logf.write(line)
            logf.flush()

    except Exception as e:
        log(f"Streamlit subprocess error: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
    finally:
        if logf:
            try:
                logf.close()
            except Exception:
                pass
        _streamlit_proc = None


def _ensure_single_instance():
    """Prevent multiple instances from launching at once (stops the horrible relaunch storm)."""
    import fcntl
    lock_path = os.path.expanduser("~/Library/Application Support/SystemicTauStudio/lock")
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    try:
        lock_fd = open(lock_path, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Store the fd globally so it stays open for the life of the process
        globals()['_single_instance_lock_fd'] = lock_fd
        # Write our PID for extra safety
        lock_fd.write(str(os.getpid()) + '\n')
        lock_fd.flush()
        log("Single instance lock acquired")
        return True
    except BlockingIOError:
        log("Another instance of Systemic Tau Studio is already running. Exiting.", "WARNING")
        return False
    except Exception as e:
        log(f"Could not acquire single instance lock: {e}", "WARNING")
        return True  # allow launch anyway

def _release_single_instance():
    try:
        if '_single_instance_lock_fd' in globals():
            fd = globals().pop('_single_instance_lock_fd', None)
            if fd:
                fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
                fd.close()
    except Exception:
        pass

atexit.register(_release_single_instance)

def main():
    try:
        log("main() entered")

        if not _ensure_single_instance():
            sys.exit(0)

        # Disable macOS persistent UI / window restoration.
        # This prevents the "reopen windows" path that triggers WebKit crashes
        # (NSPersistentUIManager, secure coding exceptions) on subsequent launches
        # after a previous crash. Very common source of SIGABRT loops in pywebview bundles.
        if getattr(sys, 'frozen', False):
            try:
                from AppKit import NSUserDefaults
                defaults = NSUserDefaults.standardUserDefaults()
                defaults.setBool_forKey_(False, "NSQuitAlwaysKeepsWindows")
                defaults.setBool_forKey_(True, "ApplePersistenceIgnoreState")
                defaults.synchronize()
                log("Disabled macOS persistent UI state restoration")
            except Exception as e:
                log(f"Could not disable persistence (non-fatal): {e}")

        port = find_free_port()
        url = f"http://127.0.0.1:{port}"
        log(f"Using port {port}")

        # Handle signals for clean shutdown (important in .app bundles)
        def _signal_handler(signum, frame):
            log(f"Received signal {signum}, shutting down...")
            _cleanup_streamlit()
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, _signal_handler)
            signal.signal(signal.SIGTERM, _signal_handler)
        except Exception:
            pass

        # Launch the Streamlit server in a background thread FIRST (non-blocking)
        # daemon=True to prevent Py_FinalizeEx hang on exit (macOS .app + webview main thread + Streamlit server thread).
        server_thread = threading.Thread(target=run_streamlit, args=(port,), daemon=True)
        server_thread.start()
        log("Server thread started")

        # Small head-start so the server process has a chance to start listening
        time.sleep(0.8)

        # Use a static loading HTML with JS redirect. This way:
        # - Window appears immediately and stays open.
        # - No early network call to the URL (avoids WebKit issues if server not ready yet).
        # - If server is slow, user sees loading then it redirects automatically.
        # - If server never comes, user sees the error page inside the window (no crash, no close).
        loading_html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Systemic Tau Studio</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#111; color:#ddd; margin:0; height:100vh; display:flex; align-items:center; justify-content:center; }}
.container {{ text-align:center; }}
.spinner {{ width:48px; height:48px; border:5px solid #333; border-top-color:#0af; border-radius:50%; animation:spin 1s linear infinite; margin:0 auto 20px; }}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
</style>
</head>
<body>
<div class="container">
  <div class="spinner"></div>
  <h2>Systemic Tau Studio</h2>
  <p>Starting local analysis server...</p>
  <p style="font-size:12px;opacity:0.7;margin-top:12px">Please wait — this can take a few seconds on first launch.</p>
</div>
</body>
</html>'''

        log("Creating native window with loading page (auto-redirect to server)")
        try:
            import webview

            window = webview.create_window(
                title="Systemic Tau Studio",
                html=loading_html,
                width=1366,
                height=900,
                resizable=True,
                min_size=(980, 640),
                text_select=True,
                confirm_close=False,
            )
            _window_holder['window'] = window

            def _on_window_close():
                log("Window close detected")
                _cleanup_streamlit()

            try:
                window.events.closed += _on_window_close
            except Exception:
                pass

            # On macOS .app bundles, sometimes we need to explicitly activate
            # so the window comes to the front instead of staying hidden.
            if getattr(sys, 'frozen', False):
                try:
                    from AppKit import NSApplication
                    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
                    log("Activated NSApplication (macOS .app)")
                except Exception as e:
                    log(f"AppKit activation not available or failed: {e}")

            # Robust readiness watcher: poll health and navigate when ready.
            # This replaces fragile fixed-time JS redirect.
            def _navigate_when_ready(w, url):
                if wait_for_server(url, timeout=45.0):
                    try:
                        w.load_url(url)
                        log(f"Server ready, navigated window to {url}")

                        # Defense-in-depth: prevent any .pdf links from navigating the main
                        # webview document. This avoids the WebKit sandbox error:
                        # "Blocked script execution in '...pdf' because the document's frame is sandboxed..."
                        # When a PDF is loaded, WebKit puts it in a restricted frame and our
                        # injected pywebview scripts get blocked. We stop the navigation at the source.
                        try:
                            w.evaluate_js("""
                                (function installPdfGuard() {
                                    function blockPdf(ev) {
                                        const a = ev.target.closest('a[href]');
                                        if (a && /\\.pdf($|\\?|#)/i.test(a.href)) {
                                            ev.preventDefault();
                                            ev.stopImmediatePropagation();
                                            // The new buttons save directly to ~/Downloads instead.
                                            try {
                                                const msg = 'PDF exports now save directly to your Downloads/SystemicTauStudio folder. Look for the success message and "Reveal in Finder" button in the app.';
                                                if (typeof alert === 'function') alert(msg);
                                            } catch(_) {}
                                        }
                                    }
                                    document.addEventListener('click', blockPdf, true);
                                    document.addEventListener('auxclick', blockPdf, true);
                                    console.log('[SystemicTauStudio] PDF navigation guard installed');
                                })();
                            """)
                        except Exception as jserr:
                            log(f"Could not install PDF guard JS: {jserr}")
                    except Exception as e:
                        log(f"load_url failed: {e}")
                else:
                    try:
                        err = "<h1>Could not start server</h1><p>Timed out waiting for internal server. Check logs.</p>"
                        w.load_html(err)
                    except Exception:
                        pass

            threading.Thread(target=_navigate_when_ready, args=(window, url), daemon=True).start()

            # Note: monitor thread is already started inside run_streamlit right after Popen.
            # This keeps the window open on server death via load_html best-effort.

            log("Calling webview.start() — the window should now be visible")
            webview.start(gui='cocoa', debug=True)
            log("webview.start() returned (window closed)")

            _cleanup_streamlit()

            # Aggressive exit: bypass Python's normal finalization.
            # This prevents the Py_FinalizeEx + wait_for_thread_shutdown hang
            # we saw in the spindump (main thread blocked on non-daemon threads).
            import os
            log("Performing os._exit(0) for clean .app shutdown (avoids finalize hang).")
            os._exit(0)

        except ImportError as ie:
            log(f"pywebview ImportError: {ie}", "ERROR")
            try:
                import webview
                html = f"<h1>Systemic Tau Studio</h1><p>pywebview failed to import.</p><pre>{ie}</pre>"
                webview.create_window("Systemic Tau Studio - Error", html=html)
                webview.start(gui='cocoa')
            except Exception:
                pass
        except Exception as e:
            log(f"Error creating/showing window: {e}", "ERROR")
            log(traceback.format_exc(), "ERROR")
            try:
                import webview
                err_html = f"<h1>Error starting Systemic Tau Studio</h1><pre>{traceback.format_exc()}</pre>"
                webview.create_window("Systemic Tau Studio - Crash", html=err_html, width=800, height=600)
                webview.start(gui='cocoa')
            except Exception as e2:
                log(f"Could not show error window: {e2}", "ERROR")
            finally:
                _release_single_instance()

        # Final cleanup
        _cleanup_streamlit()
        _release_single_instance()

        try:
            if 'server_thread' in locals():
                server_thread.join(timeout=3)
        except Exception:
            pass

        log("Shutting down Systemic Tau Studio...")

        # Last-resort aggressive exit in normal flow too
        import os
        os._exit(0)

    except Exception:
        # Last-resort catch for anything before we even get to window code
        err = traceback.format_exc()
        log("FATAL UNCAUGHT EXCEPTION IN LAUNCHER", "CRITICAL")
        log(err, "CRITICAL")
        # Try to surface the error to the user
        try:
            import webview
            webview.create_window("Systemic Tau Studio - Fatal Error", html=f"<pre>{err}</pre>", width=900, height=700)
            webview.start()
        except Exception:
            # Nothing more we can do - at least the log has it
            pass
        _cleanup_streamlit()


if __name__ == "__main__":
    main()
