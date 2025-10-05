# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

"""
Generate QTI 2.1 assessmentTest XML.
"""

from .quiz import GroupEnd, GroupStart, Question, Quiz, TextRegion


def xml_escape(s: str) -> str:
    """Basic XML escaping."""
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('"', '&quot;')
             .replace("'", '&apos;'))


ASSESSMENT_TEST_START = '''\
<?xml version="1.0" encoding="UTF-8"?>
<assessmentTest identifier="{identifier}" title="{title}"
    xmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd">
'''

ASSESSMENT_TEST_END = '''\
</assessmentTest>
'''

OUTCOME_DECLARATION = '''\
  <outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">
    <defaultValue>
      <value>0.0</value>
    </defaultValue>
  </outcomeDeclaration>
'''

TEST_PART_START = '''\
  <testPart identifier="testPart1" navigationMode="linear" submissionMode="individual">
    <itemSessionControl maxAttempts="1" showFeedback="true" showSolution="false" allowComment="false" allowSkipping="true" validateResponses="false"/>
'''

TEST_PART_END = '''\
  </testPart>
'''

ASSESSMENT_SECTION_START = '''\
    <assessmentSection identifier="{identifier}" title="{title}" visible="true">
'''

ASSESSMENT_SECTION_END = '''\
    </assessmentSection>
'''

ASSESSMENT_SECTION_WITH_SELECTION = '''\
    <assessmentSection identifier="{identifier}" title="{title}" visible="true">
      <selection select="{select}"/>
      <ordering shuffle="true"/>
'''

ASSESSMENT_ITEM_REF = '''\
      <assessmentItemRef identifier="{identifier}" href="../assessmentItems/{filename}"/>
'''

TEXT_ITEM_REF = '''\
      <assessmentItemRef identifier="{identifier}" href="../assessmentItems/{filename}"/>
'''


def assessment_test(*, quiz: Quiz, test_identifier: str) -> str:
    '''
    Generate assessmentTest XML from Quiz.
    
    The assessmentTest is the QTI 2.1 wrapper that organizes items into sections
    and defines test-level settings.
    '''
    xml = []
    
    # Start
    xml.append(ASSESSMENT_TEST_START.format(
        identifier=test_identifier,
        title=xml_escape(quiz.title_xml)
    ))
    
    # Outcome declarations (test-level score)
    xml.append(OUTCOME_DECLARATION)
    
    # Test part (most QTI 2.1 tests have a single test part)
    xml.append(TEST_PART_START)
    
    # Main assessment section containing all questions
    xml.append(ASSESSMENT_SECTION_START.format(
        identifier='main_section',
        title='Questions'
    ))
    
    # Track if we're inside a group
    in_group = False
    
    # Process each question or delimiter
    for item in quiz.questions_and_delims:
        if isinstance(item, TextRegion):
            # Text regions - create a separate text-only item
            filename = f'text2qti_text_{item.id}.xml'
            xml.append(TEXT_ITEM_REF.format(
                identifier=f'text2qti_text_{item.id}',
                filename=filename
            ))
        
        elif isinstance(item, GroupStart):
            # Start a group (section with selection)
            group = item.group
            xml.append(ASSESSMENT_SECTION_WITH_SELECTION.format(
                identifier=f'text2qti_group_{group.id}',
                title=xml_escape(group.title_xml),
                select=str(group.pick)
            ))
            in_group = True
        
        elif isinstance(item, GroupEnd):
            # End a group
            xml.append(ASSESSMENT_SECTION_END)
            in_group = False
        
        elif isinstance(item, Question):
            # Regular question
            filename = f'text2qti_question_{item.id}.xml'
            xml.append(ASSESSMENT_ITEM_REF.format(
                identifier=f'text2qti_question_{item.id}',
                filename=filename
            ))
    
    # Close main section
    xml.append(ASSESSMENT_SECTION_END)
    
    # Close test part
    xml.append(TEST_PART_END)
    
    # Close assessment test
    xml.append(ASSESSMENT_TEST_END)
    
    return ''.join(xml)


def create_text_region_item(text_region: TextRegion) -> str:
    """
    Create a text-only assessment item for text regions.
    These are non-scored informational sections.
    """
    xml = []
    xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml.append('<assessmentItem')
    xml.append('\txmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"')
    xml.append('\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    xml.append('\txsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"')
    xml.append(f'\tidentifier="text2qti_text_{text_region.id}"')
    xml.append(f'\ttitle="{xml_escape(text_region.title_xml)}"')
    xml.append('\tadaptive="false"')
    xml.append('\ttimeDependent="false">')
    
    # No response declaration for text-only items
    
    # Outcome for score (always 0)
    xml.append('<outcomeDeclaration identifier="SCORE" cardinality="single" baseType="float">')
    xml.append('<defaultValue><value>0</value></defaultValue>')
    xml.append('</outcomeDeclaration>')
    
    # Item body with just text content
    xml.append('<itemBody>')
    xml.append(f'<div class="text-region">')
    if text_region.title_xml:
        xml.append(f'<h3>{xml_escape(text_region.title_xml)}</h3>')
    xml.append(text_region.text_html_xml)
    xml.append('</div>')
    xml.append('</itemBody>')
    
    # No response processing needed for text-only
    
    xml.append('</assessmentItem>')
    return '\n'.join(xml)
