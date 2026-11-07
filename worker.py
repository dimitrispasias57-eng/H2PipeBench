"""One bounded JSON request via stdin; no persistent inputs, files or logs."""
import json
import sys

def main():
    from h2web.calculations import execute
    from h2web.inputs import InputError
    try:
        raw=sys.stdin.buffer.read(16385)
        if len(raw)>16384:
            raise InputError('Request exceeds the web-service size limit.')
        result=execute(json.loads(raw))
    except InputError as exc:
        result={'error':str(exc),'kind':'input'}
    except Exception:
        # This boundary deliberately excludes raw property-library messages,
        # environment values, paths and tracebacks from the public response.
        result={'error':'The calculation could not be completed. No result has been substituted. Try the verified example or contact the maintainer through the approved repository.','kind':'internal'}
    sys.stdout.write(json.dumps(result,ensure_ascii=True,allow_nan=False))

if __name__=='__main__':main()
