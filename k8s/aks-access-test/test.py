#!/usr/bin/env python3
"""
Simple test script to diagnose Jira/Confluence connectivity from Kubernetes
"""
import os
import sys
import ssl
import requests
import urllib3
from http.server import HTTPServer, BaseHTTPRequestHandler

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'AKS Access Test - Check logs for results\n')

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

def test_connection(url, token, service_name):
    """Test connection to Jira/Confluence with different SSL settings"""
    print(f"\n{'='*60}")
    print(f"Testing {service_name}: {url}")
    print(f"{'='*60}")

    import socket

    # Parse hostname and determine protocol
    hostname = url.replace('https://', '').replace('http://', '').split('/')[0].split(':')[0]
    is_https = url.startswith('https://')
    is_http = url.startswith('http://')

    print(f"\n[NETWORK TEST] Basic connectivity to {hostname}")

    # Test DNS resolution
    print(f"  [DNS] Resolving {hostname}...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"  ✓ Resolved to: {ip}")
    except Exception as e:
        print(f"  ✗ DNS resolution failed: {e}")
        return

    # Test TCP connectivity on port 80
    print(f"  [TCP] Testing port 80...")
    try:
        with socket.create_connection((hostname, 80), timeout=5) as sock:
            print(f"  ✓ Port 80 is open")
    except Exception as e:
        print(f"  ✗ Port 80 connection failed: {e}")

    # Test TCP connectivity on port 443
    print(f"  [TCP] Testing port 443...")
    try:
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            print(f"  ✓ Port 443 is open")
    except Exception as e:
        print(f"  ✗ Port 443 connection failed: {e}")

    headers = {"Authorization": f"Bearer {token}"}

    # Test HTTP (port 80) - serverInfo endpoint (no auth needed)
    print(f"\n[HTTP TEST] Testing HTTP on port 80...")
    http_url = f"http://{hostname}/rest/api/2/serverInfo"
    try:
        resp = requests.get(http_url, timeout=30, verify=False)
        print(f"  ✓ HTTP SUCCESS - Status: {resp.status_code}")
        print(f"  Response preview: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"  ✗ HTTP TIMEOUT - Server accepts TCP but HTTP request times out")
        print(f"  This suggests a WAF/firewall is blocking HTTP requests")
    except requests.exceptions.ConnectionError as e:
        print(f"  ✗ HTTP CONNECTION ERROR: {str(e)[:200]}")
    except Exception as e:
        print(f"  ✗ HTTP ERROR: {type(e).__name__}: {str(e)[:200]}")

    # Test HTTPS (port 443) - serverInfo endpoint (no auth needed)
    print(f"\n[HTTPS TEST] Testing HTTPS on port 443...")
    https_url = f"https://{hostname}/rest/api/2/serverInfo"

    # Test with SSL verification
    print(f"  [HTTPS] With SSL verification...")
    try:
        resp = requests.get(https_url, timeout=30, verify=True)
        print(f"  ✓ HTTPS SUCCESS (verified) - Status: {resp.status_code}")
        print(f"  Response preview: {resp.text[:200]}")
    except requests.exceptions.SSLError as e:
        print(f"  ✗ SSL ERROR: {str(e)[:200]}")
    except requests.exceptions.Timeout:
        print(f"  ✗ HTTPS TIMEOUT (verified)")
    except Exception as e:
        print(f"  ✗ HTTPS ERROR (verified): {type(e).__name__}: {str(e)[:200]}")

    # Test without SSL verification
    print(f"  [HTTPS] Without SSL verification...")
    try:
        resp = requests.get(https_url, timeout=30, verify=False)
        print(f"  ✓ HTTPS SUCCESS (unverified) - Status: {resp.status_code}")
        print(f"  Response preview: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"  ✗ HTTPS TIMEOUT (unverified)")
    except Exception as e:
        print(f"  ✗ HTTPS ERROR (unverified): {type(e).__name__}: {str(e)[:200]}")

    # Test authenticated endpoint with the configured URL
    print(f"\n[AUTH TEST] Testing authenticated endpoint: {url}/rest/api/2/myself")
    endpoint = f"{url}/rest/api/2/myself"

    # Determine verify setting based on URL
    verify = not url.startswith('http://')

    try:
        resp = requests.get(endpoint, headers=headers, verify=verify, timeout=30)
        print(f"  ✓ AUTH SUCCESS - Status: {resp.status_code}")
        print(f"  Response preview: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"  ✗ AUTH TIMEOUT")
    except Exception as e:
        print(f"  ✗ AUTH ERROR: {type(e).__name__}: {str(e)[:200]}")

    # SSL/TLS Info
    print(f"\n[SSL INFO] Certificate information for {hostname}:443...")
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"  SSL Version: {ssock.version()}")
                cert = ssock.getpeercert()
                if cert:
                    print(f"  Certificate Subject: {dict(x[0] for x in cert.get('subject', []))}")
                    print(f"  Certificate Issuer: {dict(x[0] for x in cert.get('issuer', []))}")
                else:
                    print(f"  No certificate information available")
    except Exception as e:
        print(f"  ✗ Could not retrieve SSL info: {type(e).__name__}: {str(e)[:150]}")

def main():
    print("\n" + "="*60)
    print("AKS ACCESS TEST - Jira/Confluence Connectivity")
    print("="*60)

    # Get environment variables
    jira_url = os.getenv('JIRA_URL')
    confluence_url = os.getenv('CONFLUENCE_URL')
    jira_token = os.getenv('JIRA_PERSONAL_TOKEN')
    confluence_token = os.getenv('CONFLUENCE_PERSONAL_TOKEN')

    # Validate environment
    print("\n[ENV CHECK] Environment Variables:")
    print(f"  JIRA_URL: {'✓ Set' if jira_url else '✗ Missing'}")
    print(f"  CONFLUENCE_URL: {'✓ Set' if confluence_url else '✗ Missing'}")
    print(f"  JIRA_PERSONAL_TOKEN: {'✓ Set' if jira_token else '✗ Missing'}")
    print(f"  CONFLUENCE_PERSONAL_TOKEN: {'✓ Set' if confluence_token else '✗ Missing'}")

    # Python SSL info
    print(f"\n[PYTHON INFO]")
    print(f"  Python version: {sys.version}")
    print(f"  Requests version: {requests.__version__}")
    print(f"  OpenSSL version: {ssl.OPENSSL_VERSION}")

    # Run tests
    if jira_url and jira_token:
        test_connection(jira_url, jira_token, "JIRA")
    else:
        print("\n⚠ Skipping Jira test - missing URL or token")

    if confluence_url and confluence_token:
        test_connection(confluence_url, confluence_token, "CONFLUENCE")
    else:
        print("\n⚠ Skipping Confluence test - missing URL or token")

    print(f"\n{'='*60}")
    print("Tests complete - starting HTTP server to keep pod alive...")
    print(f"{'='*60}\n")

    # Start HTTP server to keep pod running
    server = HTTPServer(('0.0.0.0', 8080), TestHandler)
    print("HTTP server listening on port 8080...")
    server.serve_forever()

if __name__ == '__main__':
    main()
