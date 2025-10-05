# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

"""
Generate QTI 3.0 assessmentTest XML.
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
<qti-assessment-test identifier="{identifier}" title="{title}"
    xmlns="http://www.imsglobal.org/xsd/imsqtiasi_v3p0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imsqtiasi_v3p0 https://purl.imsglobal.org/spec/qti/v3p0/schema/xsd/imsqti_asiv3p0_v1p0.xsd">
'''

ASSESSMENT_TEST_END = '''\
</qti-assessment-test>
'''

OUTCOME_DECLARATION = '''\
  <qti-outcome-declaration identifier="SCORE" cardinality="single" base-type="float">
    <qti-default-value>
      <qti-value>0.0</qti-value>
    </qti-default-value>
  </qti-outcome-declaration>
'''

TEST_PART_START = '''\
  <qti-test-part identifier="testPart1" navigation-mode="linear" submission-mode="individual">
    <qti-item-session-control max-attempts="1" show-feedback="true" show-solution="false" allow-comment="false" allow-skipping="true" validate-responses="false"/>
'''

TEST_PART_END = '''\
  </qti-test-part>
'''

ASSESSMENT_SECTION_START = '''\
    <qti-assessment-section identifier="{identifier}" title="{title}" visible="true">
'''

ASSESSMENT_SECTION_END = '''\
    </qti-assessment-section>
'''

ASSESSMENT_SECTION_WITH_SELECTION = '''\
    <qti-assessment-section identifier="{identifier}" title="{title}" visible="true">
      <qti-selection select="{select}"/>
      <qti-ordering shuffle="true"/>
'''

ASSESSMENT_ITEM_REF = '''\
      <qti-assessment-item-ref identifier="{identifier}" href="../assessmentItems/{filename}"/>
'''

TEXT_ITEM_REF = '''\
      <qti-assessment-item-ref identifier="{identifier}" href="../assessmentItems/{filename}"/>
'''


def assessment_test(*, quiz: Quiz, test_identifier: str) -> str:
    '''
    Generate assessmentTest XML from Quiz.
    
    The assessmentTest is the QTI 3.0 wrapper that organizes items into sections
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
    
    # Test part (most QTI 3.0 tests have a single test part)
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
    xml.append('<qti-assessment-item')
    xml.append('\txmlns="http://www.imsglobal.org/xsd/imsqtiasi_v3p0"')
    xml.append('\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    xml.append('\txsi:schemaLocation="http://www.imsglobal.org/xsd/imsqtiasi_v3p0 https://purl.imsglobal.org/spec/qti/v3p0/schema/xsd/imsqti_asiv3p0_v1p0.xsd"')
    xml.append(f'\tidentifier="text2qti_text_{text_region.id}"')
    xml.append(f'\ttitle="{xml_escape(text_region.title_xml)}"')
    xml.append('\tadaptive="false"')
    xml.append('\ttime-dependent="false">')
    
    # No response declaration for text-only items
    
    # Outcome for score (always 0)
    xml.append('<qti-outcome-declaration identifier="SCORE" cardinality="single" base-type="float">')
    xml.append('<qti-default-value><qti-value>0</qti-value></qti-default-value>')
    xml.append('</qti-outcome-declaration>')
    
    # Item body with just text content
    xml.append('<qti-item-body>')
    xml.append(f'<div class="text-region">')
    if text_region.title_xml:
        xml.append(f'<h3>{xml_escape(text_region.title_xml)}</h3>')
    xml.append(text_region.text_html_xml)
    xml.append('</div>')
    xml.append('</qti-item-body>')
    
    # No response processing needed for text-only
    
    xml.append('</qti-assessment-item>')
    return '\n'.join(xml)
