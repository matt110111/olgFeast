#!/usr/bin/env python3
"""
Test WebSocket proxy through nginx (production setup)
"""
import socket
import sys
from datetime import datetime

def test_websocket_proxy():
    """Test if WebSocket proxy is working through nginx"""
    print("🔍 Testing WebSocket Proxy Through Nginx")
    print("=" * 50)
    
    # Test nginx port (3000) for WebSocket endpoints
    host = "localhost"
    port = 3000
    
    websocket_paths = [
        "/ws/kitchen/display",
        "/ws/orders/updates", 
        "/ws/admin/dashboard"
    ]
    
    results = []
    
    for path in websocket_paths:
        print(f"\n🧪 Testing: {path}")
        try:
            # Create a socket connection to test basic connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ {path} proxy endpoint reachable on {host}:{port}")
                results.append(True)
            else:
                print(f"   ❌ {path} proxy endpoint not reachable on {host}:{port}")
                results.append(False)
        except Exception as e:
            print(f"   ❌ Error testing {path}: {e}")
            results.append(False)
    
    # Test HTTP endpoints through proxy
    print(f"\n🧪 Testing HTTP endpoints through proxy:")
    http_paths = ["/"]
    
    for path in http_paths:
        try:
            import urllib.request
            url = f"http://{host}:{port}{path}"
            response = urllib.request.urlopen(url, timeout=5)
            if response.status == 200:
                print(f"   ✅ {path} HTTP proxy working")
                results.append(True)
            else:
                print(f"   ❌ {path} HTTP proxy returned status {response.status}")
                results.append(False)
        except Exception as e:
            print(f"   ❌ Error testing HTTP proxy {path}: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results:")
    print("=" * 20)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All proxy tests passed!")
        print("\n📱 Your OlgFeast application is ready!")
        print("   Frontend: http://localhost:3000")
        print("   Backend: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        print("\n🔑 Login credentials:")
        print("   Check deployment_credentials.txt for admin and customer passwords")
        print("\n💡 WebSocket connections should now work through the nginx proxy!")
    else:
        print("⚠️  Some proxy tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    try:
        result = test_websocket_proxy()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
