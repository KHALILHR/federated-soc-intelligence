"""
Log Ingestion Service
Simulates SIEM log ingestion from various sources into Elasticsearch.
Generates realistic log entries for development and demonstration.
"""

import logging
import random
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

EVENT_TYPES = [
    'authentication_success', 'authentication_failure',
    'firewall_allow', 'firewall_deny',
    'dns_query', 'dns_response',
    'http_request', 'http_response',
    'file_access', 'process_start',
    'network_connection', 'port_scan',
    'malware_detected', 'privilege_escalation',
    'data_transfer', 'vpn_connection',
]

SEVERITY_WEIGHTS = {
    'low': 0.45,
    'medium': 0.30,
    'high': 0.18,
    'critical': 0.07,
}

INTERNAL_SUBNETS = ['10.0.{}.{}', '192.168.{}.{}', '172.16.{}.{}']
EXTERNAL_IPS = [
    '203.0.113.{}', '198.51.100.{}', '185.220.101.{}',
    '91.219.237.{}', '45.33.32.{}',
]


def _random_internal_ip() -> str:
    subnet = random.choice(INTERNAL_SUBNETS)
    return subnet.format(random.randint(1, 254), random.randint(1, 254))


def _random_external_ip() -> str:
    template = random.choice(EXTERNAL_IPS)
    return template.format(random.randint(1, 254))


def _weighted_severity() -> str:
    r = random.random()
    cumulative = 0.0
    for sev, weight in SEVERITY_WEIGHTS.items():
        cumulative += weight
        if r <= cumulative:
            return sev
    return 'low'


def generate_log_entries(count: int = 50,
                         source_name: str = 'sim-source',
                         time_window_hours: int = 24) -> List[Dict[str, Any]]:
    """
    Generate realistic simulated SIEM log entries.

    Returns a list of dicts ready for database insertion or ES indexing.
    """
    entries = []
    now = datetime.now(timezone.utc)

    for _ in range(count):
        event_type = random.choice(EVENT_TYPES)
        severity = _weighted_severity()
        ts = now - timedelta(
            seconds=random.randint(0, time_window_hours * 3600)
        )

        is_outbound = random.random() < 0.4
        src_ip = _random_internal_ip()
        dst_ip = _random_external_ip() if is_outbound else _random_internal_ip()

        raw_line = f"{ts.isoformat()} {src_ip} -> {dst_ip} {event_type} [{severity}]"
        raw_hash = hashlib.sha256(raw_line.encode()).hexdigest()

        entry = {
            'id': str(uuid.uuid4()),
            'timestamp': ts,
            'source_ip': src_ip,
            'destination_ip': dst_ip,
            'event_type': event_type,
            'severity': severity,
            'raw_hash': raw_hash,
            'parsed_fields': {
                'source': source_name,
                'protocol': random.choice(['TCP', 'UDP', 'ICMP']),
                'port': random.choice([22, 53, 80, 443, 3389, 8080, 8443]),
                'bytes_transferred': random.randint(64, 1_048_576),
                'user_agent': random.choice([
                    'Mozilla/5.0', 'curl/7.68.0', 'python-requests/2.28.0',
                    'Wget/1.21', '',
                ]),
            },
        }
        entries.append(entry)

    logger.info("Generated %d simulated log entries from %s", len(entries), source_name)
    return entries
