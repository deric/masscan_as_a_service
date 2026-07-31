"""Tests for parsing of masscan output."""

import pytest

from masscan_as_a_service.__main__ import (
    convert_list_of_ports_to_dict,
    process_masscan_results,
)

# masscan emits a trailing ",]" which makes its output invalid JSON
MASSCAN_OUTPUT = """[
{   "ip": "192.0.2.1",   "timestamp": "1645000000", "ports": [ \
{"port": 80, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 58} ] }
,
{   "ip": "192.0.2.1",   "timestamp": "1645000001", "ports": [ \
{"port": 22, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 58} ] }
,
{   "ip": "192.0.2.2",   "timestamp": "1645000002", "ports": [ \
{"port": 443, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 55} ] }
,]
"""


def test_convert_list_of_ports_to_dict():
    ports = [
        {"port": 80, "proto": "tcp", "reason": "syn-ack", "status": "open", "ttl": 58},
        {"port": 22, "proto": "tcp", "reason": "syn-ack", "status": "open", "ttl": 58},
    ]

    assert convert_list_of_ports_to_dict(ports) == {
        "80/tcp": {"reason": "syn-ack", "status": "open"},
        "22/tcp": {"reason": "syn-ack", "status": "open"},
    }


def test_convert_list_of_ports_to_dict_empty():
    assert convert_list_of_ports_to_dict([]) == {}


def test_convert_list_of_ports_to_dict_keeps_proto_apart():
    ports = [
        {"port": 53, "proto": "tcp", "reason": "syn-ack", "status": "open", "ttl": 64},
        {"port": 53, "proto": "udp", "reason": "response", "status": "open", "ttl": 64},
    ]

    assert set(convert_list_of_ports_to_dict(ports)) == {"53/tcp", "53/udp"}


def _write(tmp_path, content):
    path = tmp_path / "output.json"
    path.write_text(content)
    return str(path)


def test_process_masscan_results_groups_by_ip(tmp_path):
    results = process_masscan_results(_write(tmp_path, MASSCAN_OUTPUT))

    assert set(results) == {"192.0.2.1", "192.0.2.2"}
    # both events for the same IP are merged into a single entry
    assert set(results["192.0.2.1"]) == {"80/tcp", "22/tcp"}
    assert results["192.0.2.2"]["443/tcp"] == {"status": "open", "reason": "syn-ack"}


def test_process_masscan_results_empty_scan(tmp_path):
    assert process_masscan_results(_write(tmp_path, "[\n]\n")) == {}


def test_process_masscan_results_survives_broken_json(tmp_path, capsys):
    """A truncated file must not raise - masscan may be killed mid-write."""
    truncated = MASSCAN_OUTPUT[: len(MASSCAN_OUTPUT) // 2]

    assert process_masscan_results(_write(tmp_path, truncated)) == {}
    assert capsys.readouterr().out  # the decode error is reported


def test_process_masscan_results_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_masscan_results(str(tmp_path / "does-not-exist.json"))
