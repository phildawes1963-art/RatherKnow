"""backend/requirements.txt must install outside this pod.

Third defect of one class in a week: hardcoded /app paths, then a missing conftest, now a
pod-only wheel URL. Something true only inside the pod, baked into a thing that has to run
outside it. Both CI jobs died at `pip install` in 18 and 22 seconds, before a single test ran:

  litellm @ https://customer-assets.emergentagent.com/internal-asset/library/...  — 403 outside
  emergentintegrations==0.2.0                                                     — not on PyPI

Neither was imported anywhere in the repository. Both removed; the remaining 126 pins resolve
from the public index. This test is what stops the next one creeping back in.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIREMENTS = os.path.join(ROOT, "backend", "requirements.txt")

# Known to exist only inside the Emergent pod. A public-index check would need the network,
# which CI has and the guard should not depend on, so the names are listed instead.
POD_ONLY_PACKAGES = {"emergentintegrations", "emergent-integrations"}


def _lines():
    with open(REQUIREMENTS, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                yield lineno, stripped


def test_no_requirement_points_at_a_url_or_local_path():
    offenders = [f"{n}: {line}" for n, line in _lines()
                 if "://" in line or line.startswith(("-e ", "file:", "/", "."))]
    assert not offenders, (
        "Requirements resolved from somewhere other than the public index. These install in the "
        "pod and 403 or 404 everywhere else:\n" + "\n".join(offenders)
    )


def test_no_pod_only_package_is_pinned():
    offenders = []
    for n, line in _lines():
        name = re.split(r"[=<>!~\[ @]", line, maxsplit=1)[0].lower()
        if name in POD_ONLY_PACKAGES:
            offenders.append(f"{n}: {line}")
    assert not offenders, (
        "Pod-only packages, absent from PyPI — pip reports 'from versions: none' in CI:\n"
        + "\n".join(offenders)
    )


def test_every_line_is_a_pinned_public_requirement():
    """A bare name or a range would install a different version in CI than in the pod, which is
    the same defect wearing different clothes."""
    unpinned = [f"{n}: {line}" for n, line in _lines() if "==" not in line]
    assert not unpinned, "Unpinned requirements:\n" + "\n".join(unpinned)
