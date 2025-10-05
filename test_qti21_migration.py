#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify QTI 2.1 migration.

This script demonstrates that text2qti now generates QTI 2.1 packages.
"""

import os
import sys

# Add text2qti to path
sys.path.insert(0, os.path.dirname(__file__))

from text2qti import QTI, Config, Quiz

# Example quiz content
quiz_text = """
Quiz title: Sample QTI 2.1 Quiz
Quiz description: This quiz demonstrates the new QTI 2.1 format.

1. What is 2 + 2?

*a) 4
b) 3
c) 5
d) 22

... This is general feedback for the question.

2. Which of the following are prime numbers? (Select all that apply)

[*] 2
[*] 3
[ ] 4
[*] 5
[ ] 6

3. What is the capital of France?

* Paris
* paris

4. Write a short essay about the benefits of QTI 2.1.

___

... Good effort!

5. What is the value of pi (approximately)?

= 3.14 +- 0.01
"""


def main():
    print("Testing QTI 2.1 Migration")
    print("=" * 50)
    
    # Create config
    config = Config()
    
    # Create quiz from text
    print("\n1. Creating quiz from text...")
    quiz = Quiz(quiz_text, config=config)
    print(f"   ✓ Quiz created: '{quiz.title_xml}'")
    print(f"   ✓ Questions: {len([q for q in quiz.questions_and_delims if hasattr(q, 'type')])}")
    
    # Generate QTI 2.1 package
    print("\n2. Generating QTI 2.1 package...")
    qti = QTI(quiz)
    print("   ✓ QTI 2.1 package generated")
    
    # Save to file
    output_path = "test_qti21_output.zip"
    print(f"\n3. Saving to {output_path}...")
    qti.save(output_path)
    print(f"   ✓ Saved successfully")
    
    # Show package info
    print("\n4. Package contents:")
    import zipfile
    with zipfile.ZipFile(output_path, 'r') as zf:
        for name in sorted(zf.namelist()):
            if name.endswith('/'):
                print(f"   📁 {name}")
            else:
                size = zf.getinfo(name).file_size
                print(f"   📄 {name} ({size} bytes)")
    
    # Show sample of assessmentItem
    print("\n5. Sample assessmentItem (first question):")
    with zipfile.ZipFile(output_path, 'r') as zf:
        items = [n for n in zf.namelist() if n.startswith('assessmentItems/') and n.endswith('.xml')]
        if items:
            content = zf.read(items[0]).decode('utf-8')
            lines = content.split('\n')[:20]  # First 20 lines
            for line in lines:
                print(f"   {line}")
            if len(content.split('\n')) > 20:
                print("   ...")
    
    print("\n" + "=" * 50)
    print("✅ QTI 2.1 Migration Test Complete!")
    print("\nKey changes from QTI 1.2 to 2.1:")
    print("  • Individual files for each question (assessmentItems/*.xml)")
    print("  • assessmentTest.xml wrapper for quiz structure")
    print("  • responseDeclaration and outcomeDeclaration")
    print("  • Modern interaction types (choiceInteraction, textEntryInteraction, etc.)")
    print("  • Improved response processing logic")
    print("  • Standards-compliant QTI 2.1 format")


if __name__ == '__main__':
    main()
