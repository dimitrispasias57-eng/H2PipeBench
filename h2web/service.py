"""Time-limited isolated workers and process-wide admission control."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from .inputs import validate_request

ROOT=Path(__file__).resolve().parents[1]
_slot=threading.BoundedSemaphore(1)
_last_start=0.
TIMEOUTS={'forward':35.,'comparison':75.,'compressor':90.}
GLOBAL_INTERVAL_S=2.
SESSION_INTERVAL_S=5.

class ServiceError(RuntimeError): pass

def run_request(request):
    global _last_start
    validate_request(request)
    if not _slot.acquire(blocking=False):
        raise ServiceError('The shared simulator is busy. Please wait for the current calculation to finish, then try again.')
    try:
        now=time.monotonic()
        if now-_last_start<GLOBAL_INTERVAL_S:
            raise ServiceError('Please wait a moment before starting another calculation.')
        _last_start=now
        return _run_worker(request,TIMEOUTS[request['operation']])
    finally:
        _slot.release()

def _run_worker(request, timeout):
    env=os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    try:
        proc=subprocess.Popen([sys.executable,str(ROOT/'worker.py')],cwd=ROOT,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            env=env,creationflags=flags)
    except OSError:
        raise ServiceError('The numerical worker could not start. Please try again later; no calculation was performed.') from None
    try:
        output,_=proc.communicate(json.dumps(request,allow_nan=False).encode(),timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill();proc.communicate()
        raise ServiceError('This calculation exceeded the public-service time limit and was stopped. No partial trajectory is used. Try a less demanding case locally.') from None
    finally:
        if proc.poll() is None:
            proc.kill();proc.wait()
    if proc.returncode or len(output)>8_000_000:
        raise ServiceError('The numerical worker ended without a usable result. No result was substituted.')
    try: result=json.loads(output)
    except (ValueError,UnicodeError):
        raise ServiceError('The numerical worker returned an unreadable response.') from None
    if 'error' in result:raise ServiceError(result['error'])
    return result
