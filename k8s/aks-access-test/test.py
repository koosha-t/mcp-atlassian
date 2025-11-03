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

    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{url}/rest/api/2/myself"

    # Test 1: With SSL verification
    print(f"\n[TEST 1] Connecting WITH SSL verification...")
    try:
        resp = requests.get(endpoint, headers=headers, verify=True, timeout=10)
        print(f"✓ SUCCESS - Status: {resp.status_code}")
        print(f"  Response preview: {resp.text[:150]}")
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL ERROR: {str(e)[:200]}")
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)[:200]}")

    # Test 2: Without SSL verification
    print(f"\n[TEST 2] Connecting WITHOUT SSL verification...")
    try:
        resp = requests.get(endpoint, headers=headers, verify=False, timeout=10)
        print(f"✓ SUCCESS - Status: {resp.status_code}")
        print(f"  Response preview: {resp.text[:150]}")
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)[:200]}")

    # Test 3: SSL/TLS Info
    print(f"\n[TEST 3] SSL/TLS Information...")
    try:
        import socket
        hostname = url.replace('https://', '').replace('http://', '').split('/')[0]
        context = ssl.create_default_context()

        with socket.create_connection((hostname, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"  SSL Version: {ssock.version()}")
                cert = ssock.getpeercert()
                print(f"  Certificate Subject: {dict(x[0] for x in cert['subject'])}")
                print(f"  Certificate Issuer: {dict(x[0] for x in cert['issuer'])}")
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
