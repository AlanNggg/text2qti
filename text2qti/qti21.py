# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

"""
QTI 2.1 classes for generating assessment items.
Based on IMS QTI 2.1 specification.
"""

from typing import List, Optional, Union


def xml_escape(s: str) -> str:
    """Basic XML escaping for attributes and text content."""
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('"', '&quot;')
             .replace("'", '&apos;'))


class AssessmentItem:
    """QTI 2.1 assessmentItem - represents a single question/item."""
    
    def __init__(self, identifier: str, title: str, adaptive: bool = False, 
                 time_dependent: bool = False, language: Optional[str] = None):
        self.identifier = identifier
        self.title = title
        self.adaptive = adaptive
        self.time_dependent = time_dependent
        self.language = language
        self.response_declarations: List[ResponseDeclaration] = []
        self.outcome_declarations: List[OutcomeDeclaration] = []
        self.item_body: Optional[ItemBody] = None
        self.response_processing: Optional[ResponseProcessing] = None
        self.modal_feedbacks: List[ModalFeedback] = []
    
    def add_response_declaration(self, identifier: str, cardinality: str, 
                                base_type: str) -> 'ResponseDeclaration':
        """Add a response declaration (declares what type of response is expected)."""
        decl = ResponseDeclaration(identifier, cardinality, base_type)
        self.response_declarations.append(decl)
        return decl
    
    def add_outcome_declaration(self, identifier: str, cardinality: str, 
                               base_type: str, default_value: Optional[str] = None) -> 'OutcomeDeclaration':
        """Add an outcome declaration (declares outcome variables like SCORE)."""
        decl = OutcomeDeclaration(identifier, cardinality, base_type, default_value)
        self.outcome_declarations.append(decl)
        return decl
    
    def set_item_body(self, item_body: 'ItemBody'):
        """Set the item body (contains the question content and interactions)."""
        self.item_body = item_body
    
    def set_response_processing(self, response_processing: 'ResponseProcessing'):
        """Set response processing (scoring logic)."""
        self.response_processing = response_processing
    
    def add_modal_feedback(self, feedback: 'ModalFeedback'):
        """Add modal feedback (feedback shown to student)."""
        self.modal_feedbacks.append(feedback)
    
    def to_xml(self) -> str:
        """Generate QTI 2.1 XML for this assessment item."""
        xml = []
        xml.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml.append('<assessmentItem')
        xml.append('\txmlns="http://www.imsglobal.org/xsd/imsqti_v2p1"')
        xml.append('\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
        xml.append('\txsi:schemaLocation="http://www.imsglobal.org/xsd/imsqti_v2p1 http://www.imsglobal.org/xsd/imsqti_v2p1.xsd"')
        xml.append(f'\tidentifier="{xml_escape(self.identifier)}"')
        xml.append(f'\ttitle="{xml_escape(self.title)}"')
        xml.append(f'\tadaptive="{"true" if self.adaptive else "false"}"')
        xml.append(f'\ttimeDependent="{"true" if self.time_dependent else "false"}"')
        if self.language:
            xml.append(f'\txml:lang="{xml_escape(self.language)}"')
        xml.append('>')
        
        # Response declarations
        for decl in self.response_declarations:
            xml.append(decl.to_xml())
        
        # Outcome declarations
        for decl in self.outcome_declarations:
            xml.append(decl.to_xml())
        
        # Item body
        if self.item_body:
            xml.append(self.item_body.to_xml())
        
        # Response processing
        if self.response_processing:
            xml.append(self.response_processing.to_xml())
        
        # Modal feedback
        for feedback in self.modal_feedbacks:
            xml.append(feedback.to_xml())
        
        xml.append('</assessmentItem>')
        return '\n'.join(xml)


class ResponseDeclaration:
    """Declares a response variable (what the student answers)."""
    
    def __init__(self, identifier: str, cardinality: str, base_type: str):
        self.identifier = identifier
        self.cardinality = cardinality  # 'single', 'multiple', 'ordered'
        self.base_type = base_type      # 'identifier', 'string', 'float', 'integer', etc.
        self.correct_response: Optional[List[str]] = None
    
    def set_correct_response(self, values: List[str]):
        """Set the correct response value(s)."""
        self.correct_response = values
    
    def to_xml(self) -> str:
        xml = [f'<responseDeclaration identifier="{xml_escape(self.identifier)}" cardinality="{self.cardinality}" baseType="{self.base_type}"']
        if self.correct_response:
            xml.append('>')
            xml.append('<correctResponse>')
            for value in self.correct_response:
                xml.append(f'<value>{xml_escape(value)}</value>')
            xml.append('</correctResponse>')
            xml.append('</responseDeclaration>')
        else:
            xml.append('/>')
        return '\n'.join(xml)


class OutcomeDeclaration:
    """Declares an outcome variable (like SCORE, FEEDBACK)."""
    
    def __init__(self, identifier: str, cardinality: str, base_type: str, 
                 default_value: Optional[str] = None):
        self.identifier = identifier
        self.cardinality = cardinality
        self.base_type = base_type
        self.default_value = default_value
        self.interpretation: Optional[str] = None
        self.normal_maximum: Optional[float] = None
    
    def to_xml(self) -> str:
        xml = [f'<outcomeDeclaration identifier="{xml_escape(self.identifier)}" cardinality="{self.cardinality}" baseType="{self.base_type}"']
        if self.interpretation:
            xml.append(f' interpretation="{xml_escape(self.interpretation)}"')
        if self.normal_maximum is not None:
            xml.append(f' normalMaximum="{self.normal_maximum}"')
        
        if self.default_value:
            xml.append('>')
            xml.append('<defaultValue>')
            xml.append(f'<value>{xml_escape(self.default_value)}</value>')
            xml.append('</defaultValue>')
            xml.append('</outcomeDeclaration>')
        else:
            xml.append('/>')
        return '\n'.join(xml)


class ItemBody:
    """The main content area of an assessment item."""
    
    def __init__(self):
        self.blocks: List[Union[str, 'Interaction']] = []
    
    def add_html(self, html: str):
        """Add raw HTML content."""
        self.blocks.append(html)
    
    def add_interaction(self, interaction: 'Interaction'):
        """Add an interaction (question element)."""
        self.blocks.append(interaction)
    
    def to_xml(self) -> str:
        xml = ['<itemBody>']
        for block in self.blocks:
            if isinstance(block, str):
                xml.append(block)
            else:
                xml.append(block.to_xml())
        xml.append('</itemBody>')
        return '\n'.join(xml)


class Interaction:
    """Base class for interactions."""
    
    def __init__(self, response_identifier: str):
        self.response_identifier = response_identifier
        self.prompt: Optional[str] = None
    
    def set_prompt(self, prompt: str):
        """Set the prompt (question text)."""
        self.prompt = prompt


class ChoiceInteraction(Interaction):
    """Multiple choice or true/false interaction."""
    
    def __init__(self, response_identifier: str, shuffle: bool = False, 
                 max_choices: int = 1):
        super().__init__(response_identifier)
        self.shuffle = shuffle
        self.max_choices = max_choices
        self.choices: List['SimpleChoice'] = []
    
    def add_choice(self, identifier: str, content: str) -> 'SimpleChoice':
        """Add a choice option."""
        choice = SimpleChoice(identifier, content)
        self.choices.append(choice)
        return choice
    
    def to_xml(self) -> str:
        xml = [f'<choiceInteraction responseIdentifier="{xml_escape(self.response_identifier)}" shuffle="{"true" if self.shuffle else "false"}" maxChoices="{self.max_choices}">']
        if self.prompt:
            xml.append(f'<prompt>{self.prompt}</prompt>')
        for choice in self.choices:
            xml.append(choice.to_xml())
        xml.append('</choiceInteraction>')
        return '\n'.join(xml)


class SimpleChoice:
    """A single choice in a choice interaction."""
    
    def __init__(self, identifier: str, content: str, fixed: bool = False):
        self.identifier = identifier
        self.content = content
        self.fixed = fixed
    
    def to_xml(self) -> str:
        fixed_attr = ' fixed="true"' if self.fixed else ''
        return f'<simpleChoice identifier="{xml_escape(self.identifier)}"{fixed_attr}>{self.content}</simpleChoice>'


class TextEntryInteraction(Interaction):
    """Text entry (fill-in-the-blank / short answer) interaction."""
    
    def __init__(self, response_identifier: str, expected_length: Optional[int] = None):
        super().__init__(response_identifier)
        self.expected_length = expected_length
    
    def to_xml(self) -> str:
        attrs = f'responseIdentifier="{xml_escape(self.response_identifier)}"'
        if self.expected_length:
            attrs += f' expectedLength="{self.expected_length}"'
        return f'<textEntryInteraction {attrs}/>'


class ExtendedTextInteraction(Interaction):
    """Extended text (essay) interaction."""
    
    def __init__(self, response_identifier: str, expected_lines: Optional[int] = None,
                 expected_length: Optional[int] = None):
        super().__init__(response_identifier)
        self.expected_lines = expected_lines
        self.expected_length = expected_length
    
    def to_xml(self) -> str:
        xml = [f'<extendedTextInteraction responseIdentifier="{xml_escape(self.response_identifier)}"']
        if self.expected_lines:
            xml.append(f' expectedLines="{self.expected_lines}"')
        if self.expected_length:
            xml.append(f' expectedLength="{self.expected_length}"')
        
        if self.prompt:
            xml.append('>')
            xml.append(f'<prompt>{self.prompt}</prompt>')
            xml.append('</extendedTextInteraction>')
        else:
            xml.append('/>')
        
        return '\n'.join(xml)


class GapMatchInteraction(Interaction):
    """Gap match interaction - drag and drop words into gaps (QTI 2.1)."""
    
    def __init__(self, response_identifier: str, shuffle: bool = False):
        super().__init__(response_identifier)
        self.shuffle = shuffle
        self.gap_texts: List['GapText21'] = []
        self.content_with_gaps: str = ""
    
    def add_gap_text(self, identifier: str, text: str, match_max: int = 1) -> 'GapText21':
        """Add a draggable gap text option."""
        gap_text = GapText21(identifier, text, match_max)
        self.gap_texts.append(gap_text)
        return gap_text
    
    def set_content_with_gaps(self, content: str):
        """Set the content that contains {gap_id} placeholders."""
        # Replace {gap_id} with proper QTI gap elements
        import re
        def replace_gap(match):
            gap_id = match.group(1)
            return f'<gap identifier="{xml_escape(gap_id)}" />'
        self.content_with_gaps = re.sub(r'\{([a-zA-Z0-9_]+)\}', replace_gap, content)
    
    def to_xml(self) -> str:
        xml = [f'<gapMatchInteraction responseIdentifier="{xml_escape(self.response_identifier)}" shuffle="{"true" if self.shuffle else "false"}">']
        if self.prompt:
            xml.append(f'<prompt>{self.prompt}</prompt>')
        
        # Add gap texts (draggable options)
        for gap_text in self.gap_texts:
            xml.append(gap_text.to_xml())
        
        # Add content with gaps
        if self.content_with_gaps:
            xml.append(self.content_with_gaps)
        
        xml.append('</gapMatchInteraction>')
        return '\n'.join(xml)


class GapText21:
    """A draggable text option for gap match interaction (QTI 2.1)."""
    
    def __init__(self, identifier: str, text: str, match_max: int = 1):
        self.identifier = identifier
        self.text = text
        self.match_max = match_max
    
    def to_xml(self) -> str:
        return f'<gapText identifier="{xml_escape(self.identifier)}" matchMax="{self.match_max}">{xml_escape(self.text)}</gapText>'


class ResponseProcessing:
    """Response processing - defines how responses are scored."""
    
    def __init__(self):
        self.rules: List['ResponseRule'] = []
    
    def add_rule(self, rule: 'ResponseRule'):
        """Add a response rule."""
        self.rules.append(rule)
    
    def to_xml(self) -> str:
        xml = ['<responseProcessing>']
        for rule in self.rules:
            xml.append(rule.to_xml())
        xml.append('</responseProcessing>')
        return '\n'.join(xml)


class ResponseRule:
    """Base class for response rules."""
    
    def to_xml(self) -> str:
        return ''


class ResponseCondition(ResponseRule):
    """Conditional response processing rule."""
    
    def __init__(self):
        self.response_if: Optional['ResponseIf'] = None
        self.response_else_ifs: List['ResponseElseIf'] = []
        self.response_else: Optional['ResponseElse'] = None
    
    def set_response_if(self, response_if: 'ResponseIf'):
        self.response_if = response_if
    
    def add_response_else_if(self, response_else_if: 'ResponseElseIf'):
        self.response_else_ifs.append(response_else_if)
    
    def set_response_else(self, response_else: 'ResponseElse'):
        self.response_else = response_else
    
    def to_xml(self) -> str:
        xml = ['<responseCondition>']
        if self.response_if:
            xml.append(self.response_if.to_xml())
        for else_if in self.response_else_ifs:
            xml.append(else_if.to_xml())
        if self.response_else:
            xml.append(self.response_else.to_xml())
        xml.append('</responseCondition>')
        return '\n'.join(xml)


class ResponseIf:
    """The 'if' part of a response condition."""
    
    def __init__(self, condition: 'Expression', actions: List['ResponseRule']):
        self.condition = condition
        self.actions = actions
    
    def to_xml(self) -> str:
        xml = ['<responseIf>']
        xml.append(self.condition.to_xml())
        for action in self.actions:
            xml.append(action.to_xml())
        xml.append('</responseIf>')
        return '\n'.join(xml)


class ResponseElseIf:
    """The 'else if' part of a response condition."""
    
    def __init__(self, condition: 'Expression', actions: List['ResponseRule']):
        self.condition = condition
        self.actions = actions
    
    def to_xml(self) -> str:
        xml = ['<responseElseIf>']
        xml.append(self.condition.to_xml())
        for action in self.actions:
            xml.append(action.to_xml())
        xml.append('</responseElseIf>')
        return '\n'.join(xml)


class ResponseElse:
    """The 'else' part of a response condition."""
    
    def __init__(self, actions: List['ResponseRule']):
        self.actions = actions
    
    def to_xml(self) -> str:
        xml = ['<responseElse>']
        for action in self.actions:
            xml.append(action.to_xml())
        xml.append('</responseElse>')
        return '\n'.join(xml)


class SetOutcomeValue(ResponseRule):
    """Sets the value of an outcome variable."""
    
    def __init__(self, identifier: str, expression: 'Expression'):
        self.identifier = identifier
        self.expression = expression
    
    def to_xml(self) -> str:
        xml = [f'<setOutcomeValue identifier="{xml_escape(self.identifier)}">']
        xml.append(self.expression.to_xml())
        xml.append('</setOutcomeValue>')
        return '\n'.join(xml)


class Expression:
    """Base class for expressions."""
    
    def to_xml(self) -> str:
        return ''


class Match(Expression):
    """Match expression - checks if two values are equal."""
    
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
    
    def to_xml(self) -> str:
        return f'<match>{self.left.to_xml()}{self.right.to_xml()}</match>'


class Variable(Expression):
    """Variable reference expression."""
    
    def __init__(self, identifier: str):
        self.identifier = identifier
    
    def to_xml(self) -> str:
        return f'<variable identifier="{xml_escape(self.identifier)}"/>'


class BaseValue(Expression):
    """Literal value expression."""
    
    def __init__(self, base_type: str, value: str):
        self.base_type = base_type
        self.value = value
    
    def to_xml(self) -> str:
        return f'<baseValue baseType="{self.base_type}">{xml_escape(self.value)}</baseValue>'


class Multiple(Expression):
    """Multiple expression - creates a container with multiple values."""
    
    def __init__(self, values: List[Expression]):
        self.values = values
    
    def to_xml(self) -> str:
        xml = ['<multiple>']
        for value in self.values:
            xml.append(value.to_xml())
        xml.append('</multiple>')
        return '\n'.join(xml)


class And(Expression):
    """AND logical operator."""
    
    def __init__(self, expressions: List[Expression]):
        self.expressions = expressions
    
    def to_xml(self) -> str:
        xml = ['<and>']
        for expr in self.expressions:
            xml.append(expr.to_xml())
        xml.append('</and>')
        return '\n'.join(xml)


class Or(Expression):
    """OR logical operator."""
    
    def __init__(self, expressions: List[Expression]):
        self.expressions = expressions
    
    def to_xml(self) -> str:
        xml = ['<or>']
        for expr in self.expressions:
            xml.append(expr.to_xml())
        xml.append('</or>')
        return '\n'.join(xml)


class Not(Expression):
    """NOT logical operator."""
    
    def __init__(self, expression: Expression):
        self.expression = expression
    
    def to_xml(self) -> str:
        return f'<not>{self.expression.to_xml()}</not>'


class Sum(Expression):
    """Sum expression - adds values together."""
    
    def __init__(self, expressions: List[Expression]):
        self.expressions = expressions
    
    def to_xml(self) -> str:
        xml = ['<sum>']
        for expr in self.expressions:
            xml.append(expr.to_xml())
        xml.append('</sum>')
        return '\n'.join(xml)


class Gte(Expression):
    """Greater than or equal expression."""
    
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
    
    def to_xml(self) -> str:
        return f'<gte>{self.left.to_xml()}{self.right.to_xml()}</gte>'


class Lte(Expression):
    """Less than or equal expression."""
    
    def __init__(self, left: Expression, right: Expression):
        self.left = left
        self.right = right
    
    def to_xml(self) -> str:
        return f'<lte>{self.left.to_xml()}{self.right.to_xml()}</lte>'


class ModalFeedback:
    """Modal feedback shown to the student."""
    
    def __init__(self, identifier: str, outcome_identifier: str = 'FEEDBACK', 
                 show_hide: str = 'show'):
        self.identifier = identifier
        self.outcome_identifier = outcome_identifier
        self.show_hide = show_hide  # 'show' or 'hide'
        self.content: str = ''
    
    def set_content(self, content: str):
        """Set the feedback content (HTML)."""
        self.content = content
    
    def to_xml(self) -> str:
        xml = [f'<modalFeedback outcomeIdentifier="{xml_escape(self.outcome_identifier)}" identifier="{xml_escape(self.identifier)}" showHide="{self.show_hide}">']
        xml.append(self.content)
        xml.append('</modalFeedback>')
        return '\n'.join(xml)
