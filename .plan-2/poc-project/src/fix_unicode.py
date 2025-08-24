#!/usr/bin/env python3
"""
Quick fix script to remove Unicode emojis from the exploratory_qa_generator.py file
for Windows compatibility.
"""

import re

# Read the file
with open('exploratory_qa_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace emoji patterns with text equivalents
replacements = {
    '📁': '[INFO]',
    '✅': '[SUCCESS]',
    '⚠️': '[WARNING]', 
    '🔄': '[INFO]',
    '🎯': '[INFO]',
    '⚠': '[WARNING]',
    '🚀': '[INFO]',
    '🏁': '[SUCCESS]',
    '🔍': 'EXPLORATORY QA TESTING:',
}

for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# Write back the file
with open('exploratory_qa_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Unicode emojis fixed successfully!")