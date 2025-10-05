# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

"""
Generate QTI 2.1 assessment items from Quiz objects.
"""

from .qti21 import (And, AssessmentItem, BaseValue, ChoiceInteraction,
                    ExtendedTextInteraction, Gte, ItemBody, Lte, Match,
                    ModalFeedback, Multiple, Not, ResponseCondition,
                    ResponseElse, ResponseElseIf, ResponseIf,
                    ResponseProcessing, SetOutcomeValue, TextEntryInteraction,
                    Variable)
from .quiz import GroupEnd, GroupStart, Question, Quiz, TextRegion


def create_assessment_item_from_question(question: Question) -> AssessmentItem:
    """
    Convert a Question object to a QTI 2.1 AssessmentItem.
    """
    # Create the assessment item
    item = AssessmentItem(
        identifier=f'text2qti_question_{question.id}',
        title=question.title_xml
    )
    
    # Add response and outcome declarations based on question type
    if question.type in ('true_false_question', 'multiple_choice_question'):
        item.add_response_declaration('RESPONSE', 'single', 'identifier')
    elif question.type == 'multiple_answers_question':
        item.add_response_declaration('RESPONSE', 'multiple', 'identifier')
    elif question.type == 'short_answer_question':
        item.add_response_declaration('RESPONSE', 'single', 'string')
    elif question.type == 'numerical_question':
        item.add_response_declaration('RESPONSE', 'single', 'float')
    elif question.type == 'essay_question':
        item.add_response_declaration('RESPONSE', 'single', 'string')
    elif question.type == 'file_upload_question':
        item.add_response_declaration('RESPONSE', 'single', 'file')
    
    # Add outcome declarations
    item.add_outcome_declaration('SCORE', 'single', 'float', default_value='0')
    item.add_outcome_declaration('FEEDBACK', 'multiple', 'identifier')
    
    # Create item body with interaction
    item_body = ItemBody()
    
    # Add question content and interaction based on type
    if question.type in ('true_false_question', 'multiple_choice_question', 'multiple_answers_question'):
        interaction = create_choice_interaction(question)
        item_body.add_interaction(interaction)
    elif question.type == 'short_answer_question':
        # Add question text as HTML
        item_body.add_html(question.question_html_xml)
        interaction = TextEntryInteraction('RESPONSE', expected_length=20)
        item_body.add_interaction(interaction)
    elif question.type == 'numerical_question':
        # Add question text as HTML
        item_body.add_html(question.question_html_xml)
        interaction = TextEntryInteraction('RESPONSE', expected_length=10)
        item_body.add_interaction(interaction)
    elif question.type == 'essay_question':
        interaction = ExtendedTextInteraction('RESPONSE', expected_lines=10)
        interaction.set_prompt(question.question_html_xml)
        item_body.add_interaction(interaction)
    elif question.type == 'file_upload_question':
        # File upload - just show question text
        item_body.add_html(question.question_html_xml)
    
    item.set_item_body(item_body)
    
    # Add response processing
    response_processing = create_response_processing(question)
    if response_processing:
        item.set_response_processing(response_processing)
    
    # Add modal feedback
    add_modal_feedback(item, question)
    
    return item


def create_choice_interaction(question: Question) -> ChoiceInteraction:
    """Create a choice interaction for MC/TF/multiple answer questions."""
    shuffle = False  # Could be made configurable
    
    if question.type == 'multiple_answers_question':
        max_choices = len([c for c in question.choices if c.correct])
    else:
        max_choices = 1
    
    interaction = ChoiceInteraction('RESPONSE', shuffle=shuffle, max_choices=max_choices)
    interaction.set_prompt(question.question_html_xml)
    
    for choice in question.choices:
        interaction.add_choice(f'text2qti_choice_{choice.id}', choice.choice_html_xml)
    
    return interaction


def create_response_processing(question: Question) -> ResponseProcessing:
    """Create response processing logic for a question."""
    rp = ResponseProcessing()
    
    if question.type in ('true_false_question', 'multiple_choice_question'):
        # Single correct answer
        correct_choice = next((c for c in question.choices if c.correct), None)
        if not correct_choice:
            return rp
        
        # Create response condition
        rc = ResponseCondition()
        
        # If correct
        correct_match = Match(
            Variable('RESPONSE'),
            BaseValue('identifier', f'text2qti_choice_{correct_choice.id}')
        )
        
        actions_correct = [
            SetOutcomeValue('SCORE', BaseValue('float', str(question.points_possible)))
        ]
        
        # Add feedback identifier if there is correct feedback
        if question.correct_feedback_raw:
            actions_correct.append(
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'correct_fb'))
            )
        
        # Add individual choice feedback if present
        if correct_choice.feedback_raw:
            actions_correct.append(
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', f'text2qti_choice_{correct_choice.id}_fb'))
            )
        
        # Add general feedback if present
        if question.feedback_raw:
            actions_correct.append(
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
            )
        
        rc.set_response_if(ResponseIf(correct_match, actions_correct))
        
        # Else (incorrect)
        if question.incorrect_feedback_raw or question.feedback_raw:
            actions_incorrect = []
            if question.incorrect_feedback_raw:
                actions_incorrect.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'incorrect_fb'))
                )
            if question.feedback_raw:
                actions_incorrect.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
                )
            rc.set_response_else(ResponseElse(actions_incorrect))
        
        # Add choice-specific feedback for incorrect choices
        for choice in question.choices:
            if not choice.correct and choice.feedback_raw:
                choice_match = Match(
                    Variable('RESPONSE'),
                    BaseValue('identifier', f'text2qti_choice_{choice.id}')
                )
                actions_choice = [
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', f'text2qti_choice_{choice.id}_fb'))
                ]
                rc.add_response_else_if(ResponseElseIf(choice_match, actions_choice))
        
        rp.add_rule(rc)
    
    elif question.type == 'multiple_answers_question':
        # Multiple correct answers - check all must be selected
        rc = ResponseCondition()
        
        # Build AND condition: all correct choices selected, no incorrect choices selected
        conditions = []
        
        for choice in question.choices:
            if choice.correct:
                # This choice should be selected
                conditions.append(Match(
                    Variable('RESPONSE'),
                    BaseValue('identifier', f'text2qti_choice_{choice.id}')
                ))
            else:
                # This choice should NOT be selected
                conditions.append(Not(Match(
                    Variable('RESPONSE'),
                    BaseValue('identifier', f'text2qti_choice_{choice.id}')
                )))
        
        if len(conditions) > 1:
            all_correct = And(conditions)
        else:
            all_correct = conditions[0] if conditions else None
        
        if all_correct:
            actions_correct = [
                SetOutcomeValue('SCORE', BaseValue('float', str(question.points_possible)))
            ]
            
            if question.correct_feedback_raw:
                actions_correct.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'correct_fb'))
                )
            if question.feedback_raw:
                actions_correct.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
                )
            
            rc.set_response_if(ResponseIf(all_correct, actions_correct))
            
            # Else (incorrect)
            if question.incorrect_feedback_raw or question.feedback_raw:
                actions_incorrect = []
                if question.incorrect_feedback_raw:
                    actions_incorrect.append(
                        SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'incorrect_fb'))
                    )
                if question.feedback_raw:
                    actions_incorrect.append(
                        SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
                    )
                rc.set_response_else(ResponseElse(actions_incorrect))
            
            rp.add_rule(rc)
    
    elif question.type == 'short_answer_question':
        # Multiple possible correct answers (string matching)
        rc = ResponseCondition()
        
        # Create OR condition for all correct answers
        if len(question.choices) == 1:
            # Single correct answer
            correct_match = Match(
                Variable('RESPONSE'),
                BaseValue('string', question.choices[0].choice_xml)
            )
        else:
            # Multiple acceptable answers - check each one
            # In QTI 2.1, we need to check each possibility
            # For simplicity, check the first one in responseIf, others in responseElseIf
            correct_match = Match(
                Variable('RESPONSE'),
                BaseValue('string', question.choices[0].choice_xml)
            )
        
        actions_correct = [
            SetOutcomeValue('SCORE', BaseValue('float', str(question.points_possible)))
        ]
        
        if question.correct_feedback_raw:
            actions_correct.append(
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'correct_fb'))
            )
        if question.feedback_raw:
            actions_correct.append(
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
            )
        
        rc.set_response_if(ResponseIf(correct_match, actions_correct))
        
        # Add additional correct answers as elseif
        for i, choice in enumerate(question.choices[1:], start=1):
            alt_match = Match(
                Variable('RESPONSE'),
                BaseValue('string', choice.choice_xml)
            )
            rc.add_response_else_if(ResponseElseIf(alt_match, actions_correct))
        
        # Else (incorrect)
        if question.incorrect_feedback_raw or question.feedback_raw:
            actions_incorrect = []
            if question.incorrect_feedback_raw:
                actions_incorrect.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'incorrect_fb'))
                )
            if question.feedback_raw:
                actions_incorrect.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
                )
            rc.set_response_else(ResponseElse(actions_incorrect))
        
        rp.add_rule(rc)
    
    elif question.type == 'numerical_question':
        # Numerical answer within range
        rc = ResponseCondition()
        
        # Check if response is within acceptable range
        in_range_conditions = [
            Gte(Variable('RESPONSE'), BaseValue('float', str(question.numerical_min))),
            Lte(Variable('RESPONSE'), BaseValue('float', str(question.numerical_max)))
        ]
        
        in_range = And(in_range_conditions)
        
        actions_correct = [
            SetOutcomeValue('SCORE', BaseValue('float', str(question.points_possible)))
        ]
        
        if question.correct_feedback_raw:
            actions_correct.append(
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'correct_fb'))
            )
        if question.feedback_raw:
            actions_correct.append(
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
            )
        
        rc.set_response_if(ResponseIf(in_range, actions_correct))
        
        # Else (incorrect/out of range)
        if question.incorrect_feedback_raw or question.feedback_raw:
            actions_incorrect = []
            if question.incorrect_feedback_raw:
                actions_incorrect.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'incorrect_fb'))
                )
            if question.feedback_raw:
                actions_incorrect.append(
                    SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
                )
            rc.set_response_else(ResponseElse(actions_incorrect))
        
        rp.add_rule(rc)
    
    elif question.type in ('essay_question', 'file_upload_question'):
        # No automatic scoring for essays/uploads, just add feedback if present
        if question.feedback_raw:
            rc = ResponseCondition()
            # Always show general feedback
            actions = [
                SetOutcomeValue('FEEDBACK', BaseValue('identifier', 'general_fb'))
            ]
            # For essay/upload, we use a simple "always true" condition
            # by checking if RESPONSE is defined (has any value)
            rc.set_response_if(ResponseIf(
                Variable('RESPONSE'),  # This evaluates to true if response exists
                actions
            ))
            rp.add_rule(rc)
    
    return rp


def add_modal_feedback(item: AssessmentItem, question: Question):
    """Add modal feedback to an assessment item."""
    
    # General feedback (shown always or based on conditions)
    if question.feedback_raw:
        feedback = ModalFeedback('general_fb', 'FEEDBACK', 'show')
        feedback.set_content(question.feedback_html_xml)
        item.add_modal_feedback(feedback)
    
    # Correct feedback
    if question.correct_feedback_raw:
        feedback = ModalFeedback('correct_fb', 'FEEDBACK', 'show')
        feedback.set_content(question.correct_feedback_html_xml)
        item.add_modal_feedback(feedback)
    
    # Incorrect feedback
    if question.incorrect_feedback_raw:
        feedback = ModalFeedback('incorrect_fb', 'FEEDBACK', 'show')
        feedback.set_content(question.incorrect_feedback_html_xml)
        item.add_modal_feedback(feedback)
    
    # Individual choice feedback
    if question.type in ('true_false_question', 'multiple_choice_question', 'multiple_answers_question'):
        for choice in question.choices:
            if choice.feedback_raw:
                feedback = ModalFeedback(f'text2qti_choice_{choice.id}_fb', 'FEEDBACK', 'show')
                feedback.set_content(choice.feedback_html_xml)
                item.add_modal_feedback(feedback)
