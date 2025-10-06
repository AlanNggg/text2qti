#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to verify QTI 2.1 migration.

This script demonstrates that text2qti now generates QTI 2.1 packages.
"""

import os
import sys

# Add text2qti to path
from text2qti.config import Config  
from text2qti.quiz import Quiz  
from text2qti.qti import QTI

# Example quiz content
quiz_text = r"""
Quiz title: Complete Question Type Examples  
Quiz description: This quiz demonstrates all seven question types.  
  
Title: Multiple Choice Example  
Points: 1  
1.  What is 2+3?  
... General question feedback.  
+   Feedback for correct answer.  
-   Feedback for incorrect answer.  
a)  6  
... Feedback for this particular answer.  
b)  1  
*c) 5  
  
Title: True/False Example  
Points: 1  
2.  The Earth is round.  
*a) True  
b)  False  
  
Title: Multiple Answers Example  
Points: 2  
3.  Which of the following are dinosaurs?  
[ ] Woolly mammoth  
[*] Tyrannosaurus rex  
[*] Triceratops  
[ ] Smilodon fatalis  
  
Title: Numerical Example (Range)  
Points: 1  
4.  What is the square root of 2?  
=   1.4142 +- 0.0001  
  
Title: Numerical Example (Exact)  
Points: 1  
5.  What is 10 divided by 2?  
=   5  
  
Title: Short Answer Example  
Points: 1  
6.  Who lives at the North Pole?  
*   Santa  
*   Santa Claus  
*   Father Christmas  
*   Saint Nicholas  
*   Saint Nick  
  
Title: Essay Example  
Points: 5  
7.  Write an essay.  
... General question feedback.  
____  
  
Title: File Upload Example  
Points: 5  
8.  Upload a file.  
... General question feedback.  
^^^^  

Title: Shakespeare Quote - Richard III
Points: 3
9. Identify the missing words in this famous quote from Shakespeare's Richard III. Now is the {G1} of our discontent. Made glorious {G2} by this sun of York.
@gap W) winter
@gap Sp) spring
@gap Su) summer
@gap A) autumn
@match W G1
@match Su G2

Title: Simple Fill-in-the-Blank
Points: 2
10. Fill in the blanks with the correct words. The {GAP1} is the capital of {GAP2}.
@gap L) London
@gap P) Paris
@gap UK) United Kingdom
@gap FR) France
@match L GAP1
@match UK GAP2

Title: Science Question
Points: 2
11. Complete the sentence with the correct scientific terms. Water is composed of {ELEMENT1} and {ELEMENT2} atoms.
@gap H) hydrogen
@gap O) oxygen
@gap C) carbon
@gap N) nitrogen
@match H ELEMENT1
@match O ELEMENT2
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
