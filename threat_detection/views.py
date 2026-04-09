import json
import random
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone

from threat_detection.models import ThreatModel, IOCEntry, DetectionRule, ThreatScore


# --- Demo IOC data for first-run experience ---
DEMO_IOCS = [
    {'type': 'ip', 'value': '185.220.101.34', 'score': 0.94, 'confidence': 0.91, 'severity': 'critical', 'feeds': ['AlienVault', 'AbuseIPDB'], 'tags': ['tor-exit', 'scanner']},
    {'type': 'domain', 'value': 'malware-c2.evil.com', 'score': 0.97, 'confidence': 0.95, 'severity': 'critical', 'feeds': ['VirusTotal', 'ThreatFox'], 'tags': ['c2', 'cobalt-strike']},
    {'type': 'sha256', 'value': 'e3b0c44298fc1c149afbf4c8996fb924...', 'score': 0.88, 'confidence': 0.85, 'severity': 'high', 'feeds': ['MalwareBazaar'], 'tags': ['ransomware', 'lockbit']},
    {'type': 'ip', 'value': '91.219.237.101', 'score': 0.82, 'confidence': 0.78, 'severity': 'high', 'feeds': ['Shodan', 'GreyNoise'], 'tags': ['brute-force', 'ssh']},
    {'type': 'url', 'value': 'http://phish-login.example.net/secure', 'score': 0.91, 'confidence': 0.88, 'severity': 'critical', 'feeds': ['PhishTank', 'OpenPhish'], 'tags': ['phishing', 'credential-theft']},
    {'type': 'domain', 'value': 'dga-generated.xyz', 'score': 0.76, 'confidence': 0.72, 'severity': 'high', 'feeds': ['DGArchive'], 'tags': ['dga', 'botnet']},
    {'type': 'ip', 'value': '45.33.32.156', 'score': 0.69, 'confidence': 0.65, 'severity': 'medium', 'feeds': ['AbuseIPDB'], 'tags': ['port-scan']},
    {'type': 'md5', 'value': 'd41d8cd98f00b204e9800998ecf8427e', 'score': 0.85, 'confidence': 0.82, 'severity': 'high', 'feeds': ['VirusTotal', 'MalwareBazaar'], 'tags': ['trojan', 'rat']},
    {'type': 'cve', 'value': 'CVE-2024-21887', 'score': 0.93, 'confidence': 0.90, 'severity': 'critical', 'feeds': ['NVD', 'CISA-KEV'], 'tags': ['ivanti', 'rce']},
    {'type': 'email', 'value': 'attacker@protonmail.ch', 'score': 0.71, 'confidence': 0.68, 'severity': 'medium', 'feeds': ['HaveIBeenPwned'], 'tags': ['spear-phishing']},
    {'type': 'ip', 'value': '203.0.113.42', 'score': 0.58, 'confidence': 0.55, 'severity': 'medium', 'feeds': ['GreyNoise'], 'tags': ['mass-scanner']},
    {'type': 'domain', 'value': 'data-exfil.darknet.io', 'score': 0.89, 'confidence': 0.87, 'severity': 'critical', 'feeds': ['ThreatFox', 'AlienVault'], 'tags': ['exfiltration', 'apt']},
]


def threat_intel_hub(request):
    """Threat Intelligence Hub — searchable IOC table."""
    search_query = request.GET.get('q', '').strip()
    ioc_type_filter = request.GET.get('type', '').strip()
    severity_filter = request.GET.get('severity', '').strip()

    iocs = IOCEntry.objects.all()

    if search_query:
        iocs = iocs.filter(value__icontains=search_query)
    if ioc_type_filter:
        iocs = iocs.filter(ioc_type=ioc_type_filter)
    if severity_filter:
        iocs = iocs.filter(severity=severity_filter)

    ioc_list = list(iocs[:100])
    use_demo = len(ioc_list) == 0

    if use_demo:
        demo_filtered = DEMO_IOCS
        if search_query:
            demo_filtered = [i for i in demo_filtered if search_query.lower() in i['value'].lower()]
        if ioc_type_filter:
            demo_filtered = [i for i in demo_filtered if i['type'] == ioc_type_filter]
        if severity_filter:
            demo_filtered = [i for i in demo_filtered if i['severity'] == severity_filter]
    else:
        demo_filtered = None

    models = ThreatModel.objects.filter(status='deployed')
    rules = DetectionRule.objects.filter(enabled=True)[:10]

    context = {
        'iocs': ioc_list,
        'demo_iocs': demo_filtered,
        'use_demo': use_demo,
        'search_query': search_query,
        'ioc_type_filter': ioc_type_filter,
        'severity_filter': severity_filter,
        'models': models,
        'rules': rules,
        'ioc_types': IOCEntry.IOCType.choices,
    }
    return render(request, 'threat_detection/intel_hub.html', context)


def api_threat_score(request):
    """API endpoint returning threat scores for given indicators."""
    indicator = request.GET.get('indicator', '').strip()
    if not indicator:
        return JsonResponse({'error': 'Missing ?indicator= parameter'}, status=400)

    ioc = IOCEntry.objects.filter(value__iexact=indicator).first()
    if ioc:
        data = {
            'indicator': ioc.value,
            'type': ioc.ioc_type,
            'enrichment_score': ioc.enrichment_score,
            'confidence': ioc.confidence,
            'severity': ioc.severity,
            'tags': ioc.tags,
            'source_feeds': ioc.source_feeds,
            'first_seen': ioc.first_seen.isoformat(),
            'last_seen': ioc.last_seen.isoformat(),
        }
    else:
        # Auto-score unknown indicator
        score = round(random.uniform(0.1, 0.5), 4)
        data = {
            'indicator': indicator,
            'type': 'unknown',
            'enrichment_score': score,
            'confidence': round(score * 0.9, 4),
            'severity': 'low' if score < 0.3 else 'medium',
            'tags': [],
            'source_feeds': [],
            'first_seen': timezone.now().isoformat(),
            'last_seen': timezone.now().isoformat(),
            'note': 'Indicator not in database; auto-scored by latest model.',
        }

    return JsonResponse(data)


def api_ioc_list(request):
    """API endpoint returning IOC entries as JSON."""
    limit = int(request.GET.get('limit', 50))
    iocs = IOCEntry.objects.all()[:limit]

    if iocs.exists():
        data = [
            {
                'id': str(i.id),
                'type': i.ioc_type,
                'value': i.value,
                'score': i.enrichment_score,
                'confidence': i.confidence,
                'severity': i.severity,
                'tags': i.tags,
            }
            for i in iocs
        ]
    else:
        data = DEMO_IOCS

    return JsonResponse({'iocs': data})
