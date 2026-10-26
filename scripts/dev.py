"""Start the local API and web server together; Ctrl-C stops both process groups."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
commands=[[sys.executable,'-m','uvicorn','services.api.main:app','--host','127.0.0.1','--port','8000'],['npm','--prefix','apps/web','run','dev']]
processes=[]
try:
    for command in commands:processes.append(subprocess.Popen(command,cwd=ROOT,start_new_session=True))
    print('MatchSense: http://127.0.0.1:3000 · Ctrl-C to stop',flush=True)
    while all(p.poll() is None for p in processes):time.sleep(.5)
except KeyboardInterrupt:pass
finally:
    for p in processes:
        if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
    for p in processes:
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
