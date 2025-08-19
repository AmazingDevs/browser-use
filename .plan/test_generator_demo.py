#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "browser-use",
#     "click",
#     "rich",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import asyncio
from dotenv import load_dotenv
from basic_test_generator import BasicTestGenerator

# Load environment variables from .env file
load_dotenv()

async def main():
    # Example: Generate a test case using a real demo e-commerce site
    generator = BasicTestGenerator()
    test_case = await generator.generate_test_case(
        url="https://www.saucedemo.com",
        scenario="User logs in and completes checkout process"
    )
    print("Generated test case:")
    print(test_case)

if __name__ == "__main__":
    asyncio.run(main())