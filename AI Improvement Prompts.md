# AI Improvement Prompts

## Prompt:

Check and verify this code. Validate the functions and calculations and give assumptions where it needs improvement. List all improvements to these code and make suggestions. Format the suggestions in form of a prompt that can be used to instruct AI agents. Identify code and elements that are not necessary.

## Prompt 1: Security Hardening

Analyze and improve the security posture of this Flask application by:

1. Moving all hardcoded API keys to environment variables
2. Implementing proper input validation and sanitization for all user inputs
3. Adding rate limiting and request throttling mechanisms
4. Implementing proper CORS headers and security headers
5. Adding request logging and monitoring capabilities
6. Implementing proper error handling that doesn't expose sensitive information

## Prompt 2: Data Validation and Error Handling

Improve data validation and error handling throughout the application by:

1. Adding comprehensive input validation for all financial data
2. Implementing proper null/None checks in all calculation functions
3. Adding data freshness validation to ensure calculations use recent data
4. Creating consistent error handling patterns across all modules
5. Adding retry logic for failed network requests
6. Implementing proper logging for debugging and monitoring

## ✅ Prompt 3: Financial Calculations Enhancement (Fixed)

Fix and enhance the financial calculations in RuleOneInvestingCalculations.py by:

1. Fixing the ROIC calculation bug (line 212)
2. Implementing the missing slope calculation function
3. Improving edge case handling for negative values in CAGR calculations
4. Adding validation for all input parameters
5. Creating more robust error handling for mathematical edge cases
6. Adding unit tests for all calculation functions

## ✅ Prompt 4: Code Quality and Architecture (Fixed)

Improve code quality and architecture by:

1. Removing all hardcoded values and making them configurable
2. Implementing proper dependency injection for better testability
3. Adding comprehensive type hints throughout the codebase
4. Creating consistent naming conventions
5. Removing commented code and unused imports
6. Implementing proper configuration management

## ✅ Prompt 5: Testing and Documentation (Fixed)

Enhance testing and documentation by:

1. Completing all empty test methods with proper test cases
2. Adding integration tests for the complete data flow
3. Creating comprehensive API documentation
4. Adding performance tests for data fetching operations
5. Implementing proper test data management
6. Adding code coverage reporting

## ✅ Prompt 6: Frontend and UX Improvements (Fixed)

Improve the frontend and user experience by:

1. Adding proper input validation and error messages
2. Implementing responsive design for mobile devices
3. Adding loading states and progress indicators
4. Improving accessibility features
5. Adding data visualization for financial metrics
6. Implementing proper error handling for network failures

## Priority Recommendations

1. Immediate (Critical): Fix security vulnerabilities and ROIC calculation bug
2. Short-term: Implement proper error handling and data validation
3. Medium-term: Complete test coverage and improve code quality
4. Long-term: Enhance frontend UX and add advanced features

