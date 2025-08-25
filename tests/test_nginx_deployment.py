import os
import re

import importlib

import_types = importlib.util.find_spec("yaml")
if import_types is None:
    import pytest
    pytestmark = pytest.mark.skip(reason="PyYAML not installed; skipping manifest validation tests")
else:
    import yaml  # type: ignore

import pytest


# Test configuration note:
# - Testing framework: pytest
# - We validate the Kubernetes Deployment manifest located at tests/fixtures/nginx-deployment.yaml.


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "nginx-deployment.yaml")


def _parse_cpu_to_milli(value: str) -> int:
    """
    Convert Kubernetes CPU quantity string to millicpu.
    Examples:
      "500m" -> 500
      "1" -> 1000
      "0.5" -> 500
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("CPU value must be a non-empty string")
    s = value.strip().lower()
    if s.endswith("m"):
        num = s[:-1]
        try:
            return int(num)
        except Exception as e:
            raise ValueError(f"Invalid millicpu value: {value}") from e
    # Assume cores; allow float
    try:
        cores = float(s)
    except Exception as e:
        raise ValueError(f"Invalid CPU value: {value}") from e
    return int(round(cores * 1000))


MEM_MULTIPLIERS = {
    "e": 10**18,
    "p": 10**15,
    "t": 10**12,
    "g": 10**9,
    "m": 10**6,   # SI "M" (megabytes) — but K8s typically uses Ki/Mi/Gi (binary)
    "k": 10**3,
    "ei": 2**60,
    "pi": 2**50,
    "ti": 2**40,
    "gi": 2**30,
    "mi": 2**20,
    "ki": 2**10,
}


def _parse_mem_to_bytes(value: str) -> int:
    """
    Convert Kubernetes memory quantity string to bytes.
    Supports binary (Ki/Mi/Gi/Ti/Pi/Ei) and SI (K/M/G/T/P/E) suffixes.
    Examples:
      "256Mi" -> 268435456
      "128M"  -> 128_000_000
      "1024"  -> 1024 (bytes)
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Memory value must be a non-empty string")
    s = value.strip()
    # Extract numeric + unit
    m = re.fullmatch(r"(?i)\s*([0-9]*\.?[0-9]+)\s*([kmgtepi]{1,2})?\s*", s)
    if not m:
        # Bare integer bytes?
        if s.isdigit():
            return int(s)
        raise ValueError(f"Invalid memory value: {value}")
    num_str, unit = m.group(1), m.group(2)
    num = float(num_str)
    if not unit:
        return int(round(num))
    unit_l = unit.lower()
    if unit_l not in MEM_MULTIPLIERS:
        raise ValueError(f"Unknown memory unit: {unit}")
    return int(round(num * MEM_MULTIPLIERS[unit_l]))


@pytest.fixture(scope="module")
def manifest():
    assert os.path.exists(FIXTURE_PATH), f"Fixture not found: {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)  # type: ignore[name-defined]
    # Basic validity
    assert isinstance(data, dict), "Manifest should parse into a mapping"
    return data


class TestHelpers:
    def test_parse_cpu_to_milli_happy_paths(self):
        assert _parse_cpu_to_milli("500m") == 500
        assert _parse_cpu_to_milli("1") == 1000
        assert _parse_cpu_to_milli("0.5") == 500
        assert _parse_cpu_to_milli("2") == 2000
        assert _parse_cpu_to_milli("250m") == 250
        assert _parse_cpu_to_milli("1.75") == 1750

    def test_parse_cpu_to_milli_errors(self):
        with pytest.raises(ValueError):
            _parse_cpu_to_milli("")
        with pytest.raises(ValueError):
            _parse_cpu_to_milli("abc")
        with pytest.raises(ValueError):
            _parse_cpu_to_milli("m")
        with pytest.raises(ValueError):
            _parse_cpu_to_milli("10mm")

    def test_parse_mem_to_bytes_happy_paths(self):
        assert _parse_mem_to_bytes("256Mi") == 256 * 2**20
        assert _parse_mem_to_bytes("128Mi") == 128 * 2**20
        assert _parse_mem_to_bytes("1Gi") == 1 * 2**30
        assert _parse_mem_to_bytes("512Ki") == 512 * 2**10
        assert _parse_mem_to_bytes("128M") == 128 * 10**6
        assert _parse_mem_to_bytes("1G") == 1 * 10**9
        assert _parse_mem_to_bytes("1024") == 1024

    def test_parse_mem_to_bytes_errors(self):
        with pytest.raises(ValueError):
            _parse_mem_to_bytes("")
        with pytest.raises(ValueError):
            _parse_mem_to_bytes("foo")
        with pytest.raises(ValueError):
            _parse_mem_to_bytes("10Mii")
        with pytest.raises(ValueError):
            _parse_mem_to_bytes("Mi")  # missing number


class TestK8sDeploymentManifest:
    def test_basic_metadata(self, manifest):
        assert manifest.get("apiVersion") == "apps/v1"
        assert manifest.get("kind") == "Deployment"
        md = manifest.get("metadata") or {}
        assert md.get("name") == "nginx"
        assert md.get("namespace") == "nginx"
        labels = md.get("labels") or {}
        assert labels.get("app") == "nginx"

    def test_spec_replicas_and_selector(self, manifest):
        spec = manifest.get("spec") or {}
        assert spec.get("replicas") == 2
        sel = spec.get("selector") or {}
        match = sel.get("matchLabels") or {}
        assert match.get("app") == "nginx"

        tmpl = spec.get("template") or {}
        tmd = (tmpl.get("metadata") or {})
        tlabels = tmd.get("labels") or {}
        assert tlabels.get("app") == "nginx"

    def test_container_config(self, manifest):
        spec = manifest.get("spec", {})
        pod_spec = ((spec.get("template") or {}).get("spec")) or {}
        containers = pod_spec.get("containers") or []
        assert isinstance(containers, list) and len(containers) == 1
        c0 = containers[0]
        assert c0.get("name") == "nginx"
        image = c0.get("image")
        assert isinstance(image, str) and image.startswith("nginx:")
        # Ensure tag is explicit and not "latest"
        _, tag = image.split(":", 1)
        assert tag and tag.lower() != "latest"
        # Basic semver-like tag check (allowing 1.29.1 etc.)
        assert re.fullmatch(r"\d+(?:\.\d+){0,2}", tag), f"Non-numeric image tag: {tag}"

        ports = c0.get("ports") or []
        assert any(p.get("containerPort") == 80 for p in ports), "Port 80 not exposed"

    def test_resources_exist_and_are_sane(self, manifest):
        c0 = (((manifest.get("spec") or {}).get("template") or {}).get("spec") or {}).get("containers")[0]
        resources = c0.get("resources") or {}
        requests = resources.get("requests") or {}
        limits = resources.get("limits") or {}
        # presence
        for k in ("cpu", "memory"):
            assert k in requests, f"Missing requests.{k}"
            assert k in limits, f"Missing limits.{k}"
        # limits >= requests
        cpu_req_m = _parse_cpu_to_milli(str(requests["cpu"]))
        cpu_lim_m = _parse_cpu_to_milli(str(limits["cpu"]))
        mem_req_b = _parse_mem_to_bytes(str(requests["memory"]))
        mem_lim_b = _parse_mem_to_bytes(str(limits["memory"]))
        assert cpu_lim_m >= cpu_req_m, f"CPU limit {cpu_lim_m}m < request {cpu_req_m}m"
        assert mem_lim_b >= mem_req_b, f"Memory limit {mem_lim_b}B < request {mem_req_b}B"

    def test_labels_consistency_between_selector_and_template(self, manifest):
        spec = manifest.get("spec") or {}
        selector = (spec.get("selector") or {}).get("matchLabels") or {}
        template_labels = ((spec.get("template") or {}).get("metadata") or {}).get("labels") or {}
        # All selector labels must be present in template labels
        for k, v in selector.items():
            assert template_labels.get(k) == v, f"Template label {k} does not match selector"
