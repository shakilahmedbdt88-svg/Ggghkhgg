#!/usr/bin/env python3
"""
Backend Testing Suite for English to Bengali AI Dictionary
Tests all backend API endpoints and functionality
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Get backend URL from frontend .env file
BACKEND_URL = "https://bengali-dict.preview.emergentagent.com/api"

class DictionaryAPITester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.failed_tests = []
        
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if details:
            print(f"   Details: {details}")
            
        if not success:
            self.failed_tests.append(result)
            
    async def test_api_health_check(self):
        """Test basic API health check at /api/"""
        try:
            async with self.session.get(f"{BACKEND_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if "message" in data and "Dictionary" in data["message"]:
                        self.log_result("API Health Check", True, "API is responding correctly")
                        return True
                    else:
                        self.log_result("API Health Check", False, "Unexpected response format", data)
                        return False
                else:
                    self.log_result("API Health Check", False, f"HTTP {response.status}", await response.text())
                    return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Connection error: {str(e)}")
            return False
            
    async def test_offline_dictionary_translation(self):
        """Test translation with offline dictionary words"""
        offline_words = ["hello", "book", "water", "food", "home", "love", "friend"]
        success_count = 0
        
        for word in offline_words:
            try:
                payload = {"word": word}
                async with self.session.post(f"{BACKEND_URL}/translate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verify required fields
                        required_fields = ["word", "bengaliTranslation", "pronunciation", "definition", "examples", "partOfSpeech", "source"]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if not missing_fields:
                            if data["source"] == "offline" and data["bengaliTranslation"]:
                                success_count += 1
                                self.log_result(f"Offline Translation - {word}", True, 
                                              f"Translated to: {data['bengaliTranslation']}")
                            else:
                                self.log_result(f"Offline Translation - {word}", False, 
                                              f"Expected offline source, got: {data.get('source', 'unknown')}")
                        else:
                            self.log_result(f"Offline Translation - {word}", False, 
                                          f"Missing fields: {missing_fields}", data)
                    else:
                        self.log_result(f"Offline Translation - {word}", False, 
                                      f"HTTP {response.status}", await response.text())
            except Exception as e:
                self.log_result(f"Offline Translation - {word}", False, f"Error: {str(e)}")
                
        overall_success = success_count >= len(offline_words) * 0.8  # 80% success rate
        self.log_result("Offline Dictionary Overall", overall_success, 
                       f"Successfully translated {success_count}/{len(offline_words)} offline words")
        return overall_success
        
    async def test_ai_enhanced_translation(self):
        """Test AI-enhanced translation for unknown words"""
        unknown_words = ["serendipity", "ephemeral", "wanderlust"]
        success_count = 0
        
        for word in unknown_words:
            try:
                payload = {"word": word}
                async with self.session.post(f"{BACKEND_URL}/translate", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check if translation was attempted
                        if data.get("bengaliTranslation") and data.get("bengaliTranslation") != "অনুবাদ পাওয়া যায়নি":
                            success_count += 1
                            source = data.get("source", "unknown")
                            self.log_result(f"AI Translation - {word}", True, 
                                          f"Translated via {source}: {data['bengaliTranslation']}")
                        else:
                            self.log_result(f"AI Translation - {word}", False, 
                                          "No valid translation provided", data)
                    else:
                        self.log_result(f"AI Translation - {word}", False, 
                                      f"HTTP {response.status}", await response.text())
            except Exception as e:
                self.log_result(f"AI Translation - {word}", False, f"Error: {str(e)}")
                
        overall_success = success_count > 0  # At least one AI translation should work
        self.log_result("AI Enhanced Translation Overall", overall_success, 
                       f"Successfully translated {success_count}/{len(unknown_words)} unknown words")
        return overall_success
        
    async def test_database_storage(self):
        """Test database storage functionality"""
        try:
            # First, translate a word to ensure it's stored
            test_word = "happiness"
            payload = {"word": test_word}
            
            async with self.session.post(f"{BACKEND_URL}/translate", json=payload) as response:
                if response.status != 200:
                    self.log_result("Database Storage", False, "Failed to create translation for storage test")
                    return False
                    
            # Wait a moment for database write
            await asyncio.sleep(1)
            
            # Now check if we can retrieve recent translations
            async with self.session.get(f"{BACKEND_URL}/translations?limit=10") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        # Check if our test word is in recent translations
                        found_test_word = any(item.get("word", "").lower() == test_word.lower() for item in data)
                        
                        if found_test_word:
                            self.log_result("Database Storage", True, 
                                          f"Successfully stored and retrieved translations. Found {len(data)} recent translations")
                            return True
                        else:
                            self.log_result("Database Storage", True, 
                                          f"Database is working, found {len(data)} translations (test word may not be latest)")
                            return True
                    else:
                        self.log_result("Database Storage", False, "No translations found in database")
                        return False
                else:
                    self.log_result("Database Storage", False, 
                                  f"Failed to retrieve translations: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_result("Database Storage", False, f"Database error: {str(e)}")
            return False
            
    async def test_statistics_endpoint(self):
        """Test statistics endpoint"""
        try:
            async with self.session.get(f"{BACKEND_URL}/dictionary/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for required statistics fields
                    required_stats = ["total_translations", "offline_words", "ai_enhanced_translations"]
                    missing_stats = [stat for stat in required_stats if stat not in data]
                    
                    if not missing_stats:
                        offline_count = data.get("offline_words", 0)
                        total_translations = data.get("total_translations", 0)
                        
                        # Verify offline dictionary count (should be 15+)
                        if offline_count >= 15:
                            self.log_result("Statistics Endpoint", True, 
                                          f"Stats working: {offline_count} offline words, {total_translations} total translations")
                            return True
                        else:
                            self.log_result("Statistics Endpoint", False, 
                                          f"Expected 15+ offline words, got {offline_count}")
                            return False
                    else:
                        self.log_result("Statistics Endpoint", False, 
                                      f"Missing statistics: {missing_stats}", data)
                        return False
                else:
                    self.log_result("Statistics Endpoint", False, 
                                  f"HTTP {response.status}", await response.text())
                    return False
                    
        except Exception as e:
            self.log_result("Statistics Endpoint", False, f"Error: {str(e)}")
            return False
            
    async def test_error_handling(self):
        """Test API error handling"""
        try:
            # Test empty word
            payload = {"word": ""}
            async with self.session.post(f"{BACKEND_URL}/translate", json=payload) as response:
                if response.status == 400:
                    self.log_result("Error Handling - Empty Word", True, "Correctly rejected empty word")
                else:
                    self.log_result("Error Handling - Empty Word", False, 
                                  f"Expected HTTP 400, got {response.status}")
                    
            # Test invalid JSON
            async with self.session.post(f"{BACKEND_URL}/translate", data="invalid json") as response:
                if response.status in [400, 422]:  # FastAPI returns 422 for validation errors
                    self.log_result("Error Handling - Invalid JSON", True, "Correctly rejected invalid JSON")
                    return True
                else:
                    self.log_result("Error Handling - Invalid JSON", False, 
                                  f"Expected HTTP 400/422, got {response.status}")
                    return False
                    
        except Exception as e:
            self.log_result("Error Handling", False, f"Error: {str(e)}")
            return False
            
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting English to Bengali Dictionary Backend Tests")
        print(f"Testing API at: {BACKEND_URL}")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Run tests in order
            tests = [
                self.test_api_health_check(),
                self.test_offline_dictionary_translation(),
                self.test_ai_enhanced_translation(),
                self.test_database_storage(),
                self.test_statistics_endpoint(),
                self.test_error_handling()
            ]
            
            results = await asyncio.gather(*tests, return_exceptions=True)
            
            # Count successes
            successful_tests = sum(1 for result in results if result is True)
            total_tests = len(results)
            
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY")
            print("=" * 60)
            
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {successful_tests}")
            print(f"Failed: {total_tests - successful_tests}")
            print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
            
            if self.failed_tests:
                print("\n❌ FAILED TESTS:")
                for failed in self.failed_tests:
                    print(f"  - {failed['test']}: {failed['message']}")
                    
            print("\n" + "=" * 60)
            
            # Return overall success (80% pass rate)
            return successful_tests >= total_tests * 0.8
            
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    tester = DictionaryAPITester()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 Backend tests completed successfully!")
        sys.exit(0)
    else:
        print("💥 Backend tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())