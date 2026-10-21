"""Fail early if native offline acceptance cannot enforce its Windows rule."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile


def main():
    if sys.platform != 'win32':
        return
    helper = Path(__file__).with_name('test_firewall.ps1')
    name = 'ArabicAligner-Preflight-' + str(os.getpid())
    # A native system client proves the rule works at an Arabic/spaced path
    # before spending time packaging models. --noproxy prevents proxy routing.
    curl = Path(os.environ['SystemRoot']) / 'System32/curl.exe'
    args = ['--noproxy', '*', '--connect-timeout', '5', '--max-time', '8',
            '-s', '-o', os.devnull, 'http://1.1.1.1/']
    with tempfile.TemporaryDirectory(prefix='arabicaligner-preflight-') as temp:
        target = Path(temp).resolve() / '\u062a\u062c\u0631\u0628\u0629 with spaces' / 'curl.exe'
        target.parent.mkdir()
        shutil.copy2(curl, target)
        subprocess.run([target, *args], check=True)
        try:
            subprocess.run(['powershell', '-NoProfile', '-File', helper, '-Name', name,
                            '-Program', target], check=True)
            blocked = subprocess.run([target, *args], check=False)
            if blocked.returncode not in (7, 28):
                raise RuntimeError('Windows application firewall did not block the test client: ' + str(blocked.returncode))
        finally:
            subprocess.run(['powershell', '-NoProfile', '-Command',
                'Get-NetFirewallRule -DisplayName ' + name + ' -ErrorAction SilentlyContinue | Remove-NetFirewallRule'], check=True)
    print('Native Windows firewall preflight passed, including an Arabic/spaced executable path.')


if __name__ == '__main__':
    main()
