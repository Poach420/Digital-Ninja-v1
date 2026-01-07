import requests
import sys
import json
from datetime import datetime

class DigitalNinjaAPITester:
    def __init__(self, base_url="https://ai-app-forge-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_auth_flow(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Flow...")
        
        # Test registration
        test_user = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!"
        }
        
        response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            
            # Test login with same credentials
            login_response = self.run_test(
                "User Login",
                "POST", 
                "auth/login",
                200,
                data={"email": test_user["email"], "password": test_user["password"]}
            )
            
            # Test get current user
            self.run_test(
                "Get Current User",
                "GET",
                "auth/me",
                200
            )
            
            # Test Google OAuth endpoint
            self.run_test(
                "Google OAuth URL",
                "GET",
                "auth/google",
                200
            )
            
            return True
        
        return False

    def test_pages_flow(self):
        """Test page management endpoints"""
        print("\n📄 Testing Page Management...")
        
        # Get pages (should be empty initially)
        self.run_test(
            "Get Pages List",
            "GET",
            "pages",
            200
        )
        
        # Create a new page
        page_data = {
            "name": "Test Page",
            "content_json": {
                "components": [
                    {"id": "1", "type": "heading", "content": "Test Heading"}
                ]
            }
        }
        
        page_response = self.run_test(
            "Create Page",
            "POST",
            "pages",
            200,
            data=page_data
        )
        
        if page_response and 'page_id' in page_response:
            page_id = page_response['page_id']
            
            # Get specific page
            self.run_test(
                "Get Specific Page",
                "GET",
                f"pages/{page_id}",
                200
            )
            
            # Update page
            update_data = {
                "name": "Updated Test Page",
                "published": True
            }
            
            self.run_test(
                "Update Page",
                "PUT",
                f"pages/{page_id}",
                200,
                data=update_data
            )
            
            # Delete page
            self.run_test(
                "Delete Page",
                "DELETE",
                f"pages/{page_id}",
                200
            )

    def test_team_management(self):
        """Test team management endpoints"""
        print("\n👥 Testing Team Management...")
        
        # Get current team
        self.run_test(
            "Get Current Team",
            "GET",
            "teams/current",
            200
        )
        
        # Get team members
        self.run_test(
            "Get Team Members",
            "GET",
            "teams/members",
            200
        )
        
        # Test invite member (mocked)
        invite_data = {
            "email": "newmember@example.com",
            "role": "editor"
        }
        
        self.run_test(
            "Invite Team Member",
            "POST",
            "teams/invite",
            200,
            data=invite_data
        )

    def test_billing_flow(self):
        """Test billing endpoints"""
        print("\n💳 Testing Billing System...")
        
        # Get billing plans
        self.run_test(
            "Get Billing Plans",
            "GET",
            "billing/plans",
            200
        )
        
        # Test subscription (mocked)
        self.run_test(
            "Subscribe to Pro Plan",
            "POST",
            "billing/subscribe?plan_id=pro",
            200
        )

    def test_ai_chat(self):
        """Test AI chat endpoint"""
        print("\n🤖 Testing AI Chat...")
        
        # Test chat message
        chat_data = {
            "message": "Hello, can you help me?",
            "session_id": "test_session_123"
        }
        
        # Note: This is a streaming endpoint, so we test differently
        try:
            url = f"{self.base_url}/api/chat/message"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
            
            response = requests.post(url, json=chat_data, headers=headers, timeout=10, stream=True)
            success = response.status_code == 200
            
            if success:
                # Read a bit of the stream to verify it works
                content = ""
                for i, chunk in enumerate(response.iter_content(chunk_size=1024)):
                    if i > 2:  # Read a few chunks
                        break
                    content += chunk.decode('utf-8', errors='ignore')
                
                success = "data:" in content
            
            self.log_test("AI Chat Message", success, f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("AI Chat Message", False, f"Exception: {str(e)}")

    def test_admin_endpoints(self):
        """Test admin endpoints"""
        print("\n🔧 Testing Admin Endpoints...")
        
        # Test diagnostics
        self.run_test(
            "Get System Diagnostics",
            "GET",
            "admin/diagnostics",
            200
        )
        
        # Test get all users (admin only)
        self.run_test(
            "Get All Users (Admin)",
            "GET",
            "admin/users",
            200
        )

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Digital Ninja App Builder API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Test authentication first
        if not self.test_auth_flow():
            print("❌ Authentication failed - stopping tests")
            return False
        
        # Run other test suites
        self.test_pages_flow()
        self.test_team_management()
        self.test_billing_flow()
        self.test_ai_chat()
        self.test_admin_endpoints()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = DigitalNinjaAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'tests_run': tester.tests_run,
                'tests_passed': tester.tests_passed,
                'success_rate': (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
                'timestamp': datetime.now().isoformat()
            },
            'results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())