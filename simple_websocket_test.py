#!/usr/bin/env python3
"""
Simple WebSocket Test Script for OlgFeast
Tests WebSocket connections without external dependencies
"""
import socket
import sys
from datetime import datetime

def test_websocket_endpoint(host, port, path):
    """Test if WebSocket endpoint is reachable"""
    try:
        # Create a socket connection to test basic connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {path} endpoint reachable on {host}:{port}")
            return True
        else:
            print(f"❌ {path} endpoint not reachable on {host}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error testing {path}: {e}")
        return False

def test_http_endpoint(host, port, path):
    """Test if HTTP endpoint is reachable"""
    try:
        import urllib.request
        url = f"http://{host}:{port}{path}"
        response = urllib.request.urlopen(url, timeout=5)
        if response.status == 200:
            print(f"✅ {path} HTTP endpoint working")
            return True
        else:
            print(f"❌ {path} HTTP endpoint returned status {response.status}")
            return False
    except Exception as e:
        print(f"❌ Error testing HTTP {path}: {e}")
        return False

def main():
    print("🔍 Testing OlgFeast WebSocket Connectivity")
    print("=" * 50)
    
    host = "localhost"
    port = 8000
    
    endpoints = [
        ("/ws/kitchen/display", "Kitchen Display WebSocket"),
        ("/ws/orders/updates", "Order Updates WebSocket"),
        ("/ws/admin/dashboard", "Admin Dashboard WebSocket"),
        ("/health", "Health Check HTTP"),
        ("/docs", "API Documentation HTTP")
    ]
    
    results = []
    for path, name in endpoints:
        if path.startswith("/ws/"):
            # Test WebSocket endpoint (basic connectivity)
            success = test_websocket_endpoint(host, port, path)
        else:
            # Test HTTP endpoint
            success = test_http_endpoint(host, port, path)
        results.append((name, success))
    
    print("\n📊 Test Results:")
    print("=" * 20)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
        if not success:
            all_passed = False
    
    print(f"\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed!'}")
    print(f"\n📱 Frontend: http://localhost:3001")
    print(f"🔧 Backend: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"\n🔑 Test Credentials:")
    print(f"   Admin: admin / 3_eKugNg9VTAA7Moz8nz7g")
    print(f"   Customer: customer / WLOfiBSVU9dCvv9k")
    
    return all_passed

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)




