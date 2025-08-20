"""
Sample test data and fixtures for POC testing framework.

This module provides comprehensive test data including:
- Sample test cases and scenarios
- Mock browser page structures
- Test user data and forms
- Error scenarios and edge cases
- Performance test data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

class TestDataGenerator:
    """Generates sample test data for various testing scenarios."""
    
    @staticmethod
    def generate_sample_test_cases() -> List[Dict[str, Any]]:
        """Generate a variety of sample test cases."""
        return [
            {
                "id": "tc_login_001",
                "title": "Valid User Login",
                "description": "Test successful login with valid credentials",
                "priority": "high",
                "type": "functional",
                "tags": ["authentication", "login", "smoke"],
                "estimated_duration": 120,
                "steps": [
                    {
                        "id": "step_001",
                        "description": "Navigate to login page",
                        "action": "navigate",
                        "url": "https://www.saucedemo.com/login",
                        "expected_result": "Login page is displayed with email and password fields",
                        "timeout": 30
                    },
                    {
                        "id": "step_002", 
                        "description": "Enter valid email address",
                        "action": "fill",
                        "selector": "#email",
                        "value": "test.user@example.com",
                        "expected_result": "Email is entered in the email field",
                        "timeout": 10
                    },
                    {
                        "id": "step_003",
                        "description": "Enter valid password",
                        "action": "fill",
                        "selector": "#password",
                        "value": "SecurePassword123!",
                        "expected_result": "Password is entered (masked)",
                        "timeout": 10
                    },
                    {
                        "id": "step_004",
                        "description": "Click login button",
                        "action": "click",
                        "selector": "#login-btn",
                        "expected_result": "User is redirected to dashboard",
                        "timeout": 15
                    },
                    {
                        "id": "step_005",
                        "description": "Verify successful login",
                        "action": "verify",
                        "selector": ".welcome-message",
                        "expected_result": "Welcome message is displayed",
                        "timeout": 10
                    }
                ],
                "expected_result": "User successfully logs in and sees the dashboard",
                "prerequisites": ["User account exists", "Browser is open"],
                "cleanup_steps": ["Logout user", "Clear session data"]
            },
            {
                "id": "tc_form_validation_001",
                "title": "Email Validation Error",
                "description": "Test email validation with invalid email format",
                "priority": "medium",
                "type": "validation",
                "tags": ["validation", "forms", "email"],
                "estimated_duration": 90,
                "steps": [
                    {
                        "id": "step_001",
                        "description": "Navigate to registration form",
                        "action": "navigate",
                        "url": "https://www.saucedemo.com/register",
                        "expected_result": "Registration form is displayed",
                        "timeout": 30
                    },
                    {
                        "id": "step_002",
                        "description": "Enter invalid email format",
                        "action": "fill",
                        "selector": "#email",
                        "value": "invalid-email-format",
                        "expected_result": "Invalid email is entered",
                        "timeout": 10
                    },
                    {
                        "id": "step_003",
                        "description": "Fill other required fields",
                        "action": "fill",
                        "selector": "#name",
                        "value": "Test User",
                        "expected_result": "Name is entered",
                        "timeout": 10
                    },
                    {
                        "id": "step_004",
                        "description": "Submit form",
                        "action": "click",
                        "selector": "#submit-btn",
                        "expected_result": "Form validation is triggered",
                        "timeout": 10
                    },
                    {
                        "id": "step_005",
                        "description": "Verify error message",
                        "action": "verify",
                        "selector": ".email-error",
                        "expected_result": "Email validation error is displayed",
                        "timeout": 5
                    }
                ],
                "expected_result": "Email validation error message is displayed",
                "prerequisites": ["Registration page is accessible"],
                "cleanup_steps": ["Clear form data"]
            },
            {
                "id": "tc_shopping_cart_001",
                "title": "Add Product to Cart",
                "description": "Test adding a product to shopping cart",
                "priority": "high",
                "type": "functional", 
                "tags": ["ecommerce", "cart", "products"],
                "estimated_duration": 180,
                "steps": [
                    {
                        "id": "step_001",
                        "description": "Navigate to product page",
                        "action": "navigate",
                        "url": "https://shop.example.com/products/laptop-123",
                        "expected_result": "Product page is displayed",
                        "timeout": 30
                    },
                    {
                        "id": "step_002",
                        "description": "Select product size",
                        "action": "select",
                        "selector": "#size-select",
                        "value": "Medium",
                        "expected_result": "Size is selected",
                        "timeout": 10
                    },
                    {
                        "id": "step_003",
                        "description": "Select quantity",
                        "action": "fill",
                        "selector": "#quantity",
                        "value": "2",
                        "expected_result": "Quantity is set to 2",
                        "timeout": 10
                    },
                    {
                        "id": "step_004",
                        "description": "Add to cart",
                        "action": "click",
                        "selector": "#add-to-cart-btn",
                        "expected_result": "Product is added to cart",
                        "timeout": 15
                    },
                    {
                        "id": "step_005",
                        "description": "Verify cart badge",
                        "action": "verify",
                        "selector": ".cart-badge",
                        "expected_result": "Cart badge shows 2 items",
                        "timeout": 10
                    }
                ],
                "expected_result": "Product is successfully added to cart with correct quantity",
                "prerequisites": ["Product is in stock", "Cart is empty"],
                "cleanup_steps": ["Empty cart", "Clear session"]
            },
            {
                "id": "tc_search_001",
                "title": "Product Search Functionality",
                "description": "Test product search with various queries",
                "priority": "medium",
                "type": "functional",
                "tags": ["search", "products", "filters"],
                "estimated_duration": 150,
                "steps": [
                    {
                        "id": "step_001",
                        "description": "Navigate to homepage",
                        "action": "navigate",
                        "url": "https://shop.example.com",
                        "expected_result": "Homepage is displayed",
                        "timeout": 30
                    },
                    {
                        "id": "step_002",
                        "description": "Enter search query",
                        "action": "fill",
                        "selector": "#search-box",
                        "value": "wireless headphones",
                        "expected_result": "Search query is entered",
                        "timeout": 10
                    },
                    {
                        "id": "step_003",
                        "description": "Submit search",
                        "action": "click",
                        "selector": "#search-btn",
                        "expected_result": "Search is executed",
                        "timeout": 15
                    },
                    {
                        "id": "step_004",
                        "description": "Verify search results",
                        "action": "verify",
                        "selector": ".search-results",
                        "expected_result": "Search results are displayed",
                        "timeout": 20
                    },
                    {
                        "id": "step_005",
                        "description": "Apply price filter",
                        "action": "click",
                        "selector": "#price-filter-100-200",
                        "expected_result": "Price filter is applied",
                        "timeout": 10
                    }
                ],
                "expected_result": "Search returns relevant products with applied filters",
                "prerequisites": ["Search functionality is available"],
                "cleanup_steps": ["Clear search filters"]
            },
            {
                "id": "tc_performance_001",
                "title": "Page Load Performance",
                "description": "Test page loading performance under normal conditions",
                "priority": "medium",
                "type": "performance",
                "tags": ["performance", "loading", "speed"],
                "estimated_duration": 60,
                "steps": [
                    {
                        "id": "step_001",
                        "description": "Clear browser cache",
                        "action": "clear_cache",
                        "expected_result": "Browser cache is cleared",
                        "timeout": 10
                    },
                    {
                        "id": "step_002",
                        "description": "Navigate to homepage",
                        "action": "navigate",
                        "url": "https://www.saucedemo.com",
                        "expected_result": "Page loads within performance threshold",
                        "timeout": 5,
                        "performance_threshold": 3.0
                    },
                    {
                        "id": "step_003",
                        "description": "Measure loading metrics",
                        "action": "measure_performance",
                        "expected_result": "Performance metrics are captured",
                        "timeout": 5
                    }
                ],
                "expected_result": "Page loads within 3 seconds",
                "prerequisites": ["Stable network connection"],
                "cleanup_steps": [],
                "performance_requirements": {
                    "load_time": 3.0,
                    "first_contentful_paint": 1.5,
                    "largest_contentful_paint": 2.5
                }
            }
        ]
    
    @staticmethod
    def generate_sample_selectors() -> Dict[str, Dict[str, str]]:
        """Generate sample CSS selectors for testing."""
        return {
            "authentication": {
                "email_input": "#email",
                "password_input": "#password",
                "login_button": "#login-btn",
                "logout_button": "#logout-btn",
                "forgot_password_link": "#forgot-password",
                "remember_me_checkbox": "#remember-me",
                "login_error": ".login-error",
                "success_message": ".login-success"
            },
            "navigation": {
                "main_menu": "nav.main-menu",
                "home_link": "a[href='/']",
                "products_link": "a[href='/products']",
                "about_link": "a[href='/about']",
                "contact_link": "a[href='/contact']",
                "user_menu": ".user-menu",
                "search_box": "#search",
                "cart_icon": ".cart-icon"
            },
            "forms": {
                "contact_form": "#contact-form",
                "name_input": "#name",
                "email_input": "#email",
                "phone_input": "#phone",
                "subject_select": "#subject",
                "message_textarea": "#message",
                "submit_button": "button[type='submit']",
                "reset_button": "button[type='reset']",
                "required_field_error": ".required-error",
                "validation_error": ".validation-error"
            },
            "ecommerce": {
                "product_grid": ".product-grid",
                "product_card": ".product-card",
                "product_title": ".product-title",
                "product_price": ".product-price",
                "product_image": ".product-image",
                "add_to_cart": ".add-to-cart",
                "cart_badge": ".cart-badge",
                "cart_total": ".cart-total",
                "checkout_button": ".checkout-btn",
                "quantity_input": ".quantity-input"
            },
            "content": {
                "page_title": "h1",
                "main_content": "#main-content",
                "sidebar": ".sidebar",
                "footer": "footer",
                "breadcrumbs": ".breadcrumbs",
                "pagination": ".pagination",
                "loading_spinner": ".loading",
                "error_message": ".error-message",
                "success_notification": ".success-notification"
            }
        }
    
    @staticmethod
    def generate_test_user_data() -> List[Dict[str, Any]]:
        """Generate sample test user data."""
        return [
            {
                "id": "user_001",
                "type": "valid_user",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": "SecurePassword123!",
                "phone": "+1-555-123-4567",
                "address": {
                    "street": "123 Main Street",
                    "city": "Anytown",
                    "state": "CA",
                    "zip": "12345",
                    "country": "USA"
                },
                "preferences": {
                    "language": "en",
                    "currency": "USD",
                    "notifications": True
                }
            },
            {
                "id": "user_002",
                "type": "admin_user",
                "name": "Admin User",
                "email": "admin@example.com",
                "password": "AdminPass456!",
                "phone": "+1-555-987-6543",
                "role": "administrator",
                "permissions": ["read", "write", "delete", "admin"]
            },
            {
                "id": "user_003",
                "type": "invalid_user",
                "name": "",
                "email": "invalid-email",
                "password": "weak",
                "phone": "invalid-phone",
                "description": "User with invalid data for negative testing"
            },
            {
                "id": "user_004",
                "type": "test_user",
                "name": "Test User",
                "email": "test.user+automation@example.com",
                "password": "TestPassword789!",
                "phone": "+1-555-111-2222",
                "temporary": True,
                "created_for_testing": True
            }
        ]
    
    @staticmethod
    def generate_error_scenarios() -> List[Dict[str, Any]]:
        """Generate error scenarios for testing."""
        return [
            {
                "id": "error_001",
                "type": "timeout_error",
                "description": "Element not found within timeout",
                "scenario": {
                    "action": "click",
                    "selector": "#non-existent-element",
                    "timeout": 5
                },
                "expected_error": "TimeoutError",
                "error_message": "Element with selector '#non-existent-element' not found within 5 seconds"
            },
            {
                "id": "error_002", 
                "type": "network_error",
                "description": "Network connection failure",
                "scenario": {
                    "action": "navigate",
                    "url": "https://non-existent-domain-12345.com"
                },
                "expected_error": "NetworkError",
                "error_message": "Failed to connect to server"
            },
            {
                "id": "error_003",
                "type": "validation_error",
                "description": "Form validation failure",
                "scenario": {
                    "action": "submit_form",
                    "form_data": {
                        "email": "invalid-email-format",
                        "password": ""
                    }
                },
                "expected_error": "ValidationError",
                "error_message": "Invalid email format and password is required"
            },
            {
                "id": "error_004",
                "type": "authentication_error",
                "description": "Invalid login credentials",
                "scenario": {
                    "action": "login",
                    "credentials": {
                        "email": "nonexistent@example.com",
                        "password": "wrongpassword"
                    }
                },
                "expected_error": "AuthenticationError",
                "error_message": "Invalid email or password"
            },
            {
                "id": "error_005",
                "type": "permission_error",
                "description": "Insufficient permissions",
                "scenario": {
                    "action": "access_admin_page",
                    "user_role": "guest"
                },
                "expected_error": "PermissionError", 
                "error_message": "Access denied: insufficient permissions"
            }
        ]
    
    @staticmethod
    def generate_performance_test_data() -> Dict[str, Any]:
        """Generate performance test data and thresholds."""
        return {
            "thresholds": {
                "page_load_time": 3.0,
                "element_find_time": 2.0,
                "form_submit_time": 5.0,
                "search_response_time": 4.0,
                "memory_usage_mb": 512,
                "cpu_usage_percent": 80
            },
            "test_urls": {
                "homepage": "https://www.saucedemo.com",
                "product_page": "https://www.saucedemo.com/products/sample",
                "checkout_page": "https://www.saucedemo.com/checkout",
                "search_page": "https://www.saucedemo.com/search?q=test",
                "large_page": "https://www.saucedemo.com/large-content-page"
            },
            "load_test_scenarios": [
                {
                    "name": "light_load",
                    "concurrent_users": 5,
                    "duration_seconds": 60,
                    "actions_per_user": 10
                },
                {
                    "name": "moderate_load",
                    "concurrent_users": 20,
                    "duration_seconds": 300,
                    "actions_per_user": 25
                },
                {
                    "name": "heavy_load",
                    "concurrent_users": 100,
                    "duration_seconds": 600,
                    "actions_per_user": 50
                }
            ]
        }
    
    @staticmethod
    def generate_mock_page_structures() -> List[Dict[str, Any]]:
        """Generate mock page structures for testing."""
        return [
            {
                "page_type": "login_page",
                "url": "https://www.saucedemo.com/login",
                "title": "Login - Example Site",
                "elements": [
                    {"tag": "form", "id": "login-form", "class": "auth-form"},
                    {"tag": "input", "id": "email", "type": "email", "name": "email", "required": True},
                    {"tag": "input", "id": "password", "type": "password", "name": "password", "required": True},
                    {"tag": "button", "id": "login-btn", "type": "submit", "text": "Login"},
                    {"tag": "a", "id": "forgot-password", "href": "/forgot-password", "text": "Forgot Password?"}
                ],
                "content": {
                    "heading": "Sign In to Your Account",
                    "footer_text": "© 2024 Example Site"
                }
            },
            {
                "page_type": "product_listing",
                "url": "https://www.saucedemo.com/products",
                "title": "Products - Example Store",
                "elements": [
                    {"tag": "div", "class": "product-grid"},
                    {"tag": "div", "class": "product-card", "count": 12},
                    {"tag": "h3", "class": "product-title", "count": 12},
                    {"tag": "span", "class": "product-price", "count": 12},
                    {"tag": "button", "class": "add-to-cart", "count": 12},
                    {"tag": "nav", "class": "pagination"}
                ],
                "content": {
                    "product_count": 12,
                    "categories": ["Electronics", "Clothing", "Home & Garden", "Sports"],
                    "price_range": {"min": 9.99, "max": 999.99}
                }
            },
            {
                "page_type": "contact_form",
                "url": "https://www.saucedemo.com/contact",
                "title": "Contact Us - Example Site",
                "elements": [
                    {"tag": "form", "id": "contact-form"},
                    {"tag": "input", "id": "name", "type": "text", "name": "name", "required": True},
                    {"tag": "input", "id": "email", "type": "email", "name": "email", "required": True},
                    {"tag": "select", "id": "subject", "name": "subject", "options": ["General", "Support", "Sales"]},
                    {"tag": "textarea", "id": "message", "name": "message", "required": True},
                    {"tag": "button", "type": "submit", "text": "Send Message"}
                ],
                "content": {
                    "heading": "Get in Touch",
                    "description": "We'd love to hear from you. Send us a message!"
                }
            },
            {
                "page_type": "dashboard",
                "url": "https://www.saucedemo.com/dashboard",
                "title": "Dashboard - Example App",
                "elements": [
                    {"tag": "nav", "class": "sidebar"},
                    {"tag": "div", "class": "main-content"},
                    {"tag": "div", "class": "widget", "count": 6},
                    {"tag": "table", "class": "data-table"},
                    {"tag": "button", "class": "action-btn", "count": 4},
                    {"tag": "div", "class": "notifications"}
                ],
                "content": {
                    "widgets": ["Sales Chart", "User Stats", "Recent Orders", "Performance Metrics"],
                    "navigation": ["Home", "Analytics", "Settings", "Profile"]
                }
            }
        ]

class TestEnvironmentData:
    """Test environment configuration data."""
    
    @staticmethod
    def get_test_environments() -> Dict[str, Dict[str, Any]]:
        """Get test environment configurations."""
        return {
            "development": {
                "base_url": "https://dev.example.com",
                "api_url": "https://api-dev.example.com",
                "database": "test_db_dev",
                "features": {
                    "new_checkout": True,
                    "beta_features": True,
                    "debug_mode": True
                },
                "credentials": {
                    "test_user": "dev.test@example.com",
                    "admin_user": "dev.admin@example.com"
                }
            },
            "staging": {
                "base_url": "https://staging.example.com",
                "api_url": "https://api-staging.example.com",
                "database": "test_db_staging",
                "features": {
                    "new_checkout": True,
                    "beta_features": False,
                    "debug_mode": False
                },
                "credentials": {
                    "test_user": "staging.test@example.com",
                    "admin_user": "staging.admin@example.com"
                }
            },
            "production": {
                "base_url": "https://www.saucedemo.com",
                "api_url": "https://api.example.com",
                "database": "prod_db_readonly",
                "features": {
                    "new_checkout": False,
                    "beta_features": False,
                    "debug_mode": False
                },
                "credentials": {
                    "test_user": "prod.test@example.com",
                    "admin_user": "prod.admin@example.com"
                },
                "restrictions": {
                    "read_only": True,
                    "no_data_modification": True
                }
            }
        }
    
    @staticmethod
    def get_browser_configurations() -> Dict[str, Dict[str, Any]]:
        """Get browser configuration options."""
        return {
            "chrome": {
                "browser": "chromium",
                "headless": True,
                "viewport": {"width": 1920, "height": 1080},
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions"
                ],
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "firefox": {
                "browser": "firefox",
                "headless": True,
                "viewport": {"width": 1920, "height": 1080},
                "args": ["--width=1920", "--height=1080"],
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
            },
            "mobile": {
                "browser": "chromium",
                "headless": True,
                "viewport": {"width": 375, "height": 667},
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
                "device_scale_factor": 2,
                "touch": True,
                "mobile": True
            }
        }

class TestDataExporter:
    """Utility for exporting test data to various formats."""
    
    @staticmethod
    def export_to_json(data: Any, file_path: str) -> None:
        """Export test data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def export_test_cases_to_csv(test_cases: List[Dict[str, Any]], file_path: str) -> None:
        """Export test cases to CSV format."""
        import csv
        
        # Extract basic test case info for CSV
        fieldnames = ['id', 'title', 'description', 'priority', 'type', 'estimated_duration', 'tags']
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for test_case in test_cases:
                row = {
                    'id': test_case['id'],
                    'title': test_case['title'],
                    'description': test_case['description'],
                    'priority': test_case['priority'],
                    'type': test_case['type'],
                    'estimated_duration': test_case['estimated_duration'],
                    'tags': ', '.join(test_case.get('tags', []))
                }
                writer.writerow(row)

# Pre-generated data instances for easy import
SAMPLE_TEST_CASES = TestDataGenerator.generate_sample_test_cases()
SAMPLE_SELECTORS = TestDataGenerator.generate_sample_selectors()
SAMPLE_USERS = TestDataGenerator.generate_test_user_data()
ERROR_SCENARIOS = TestDataGenerator.generate_error_scenarios()
PERFORMANCE_DATA = TestDataGenerator.generate_performance_test_data()
PAGE_STRUCTURES = TestDataGenerator.generate_mock_page_structures()
TEST_ENVIRONMENTS = TestEnvironmentData.get_test_environments()
BROWSER_CONFIGS = TestEnvironmentData.get_browser_configurations()

# Quick access functions
def get_test_case_by_id(test_case_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific test case by ID."""
    return next((tc for tc in SAMPLE_TEST_CASES if tc['id'] == test_case_id), None)

def get_test_cases_by_type(test_type: str) -> List[Dict[str, Any]]:
    """Get test cases filtered by type."""
    return [tc for tc in SAMPLE_TEST_CASES if tc['type'] == test_type]

def get_test_cases_by_priority(priority: str) -> List[Dict[str, Any]]:
    """Get test cases filtered by priority."""
    return [tc for tc in SAMPLE_TEST_CASES if tc['priority'] == priority]

def get_selectors_for_category(category: str) -> Optional[Dict[str, str]]:
    """Get selectors for a specific category."""
    return SAMPLE_SELECTORS.get(category)

def get_user_by_type(user_type: str) -> Optional[Dict[str, Any]]:
    """Get a user by type."""
    return next((user for user in SAMPLE_USERS if user['type'] == user_type), None)

def get_error_scenario_by_type(error_type: str) -> Optional[Dict[str, Any]]:
    """Get an error scenario by type."""
    return next((error for error in ERROR_SCENARIOS if error['type'] == error_type), None)