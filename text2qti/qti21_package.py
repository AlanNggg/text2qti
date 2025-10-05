# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

"""
Create QTI 2.1 packages from Quiz objects.
"""

import io
import pathlib
import zipfile
from typing import BinaryIO, Union

from .quiz import Question, Quiz, TextRegion
from .xml_assessment21 import create_assessment_item_from_question
from .xml_assessment_test21 import assessment_test, create_text_region_item
from .xml_imsmanifest21 import imsmanifest21


class QTI21(object):
    '''
    Create QTI 2.1 package from a Quiz object.
    '''
    def __init__(self, quiz: Quiz):
        self.quiz = quiz
        id_base = 'text2qti'
        self.manifest_identifier = f'{id_base}_manifest_{quiz.id}'
        self.test_identifier = f'{id_base}_test_{quiz.id}'
        self.test_filename = f'{self.test_identifier}.xml'
        
        # Generate assessment test XML
        self.assessment_test_xml = assessment_test(
            quiz=quiz,
            test_identifier=self.test_identifier
        )
        
        # Generate assessment items (questions)
        self.assessment_items = []
        for item in quiz.questions_and_delims:
            if isinstance(item, Question):
                assessment_item = create_assessment_item_from_question(item)
                self.assessment_items.append({
                    'identifier': assessment_item.identifier,
                    'filename': f'{assessment_item.identifier}.xml',
                    'xml': assessment_item.to_xml(),
                    'interaction_types': self._get_interaction_types(item)
                })
            elif isinstance(item, TextRegion):
                text_item_xml = create_text_region_item(item)
                self.assessment_items.append({
                    'identifier': f'text2qti_text_{item.id}',
                    'filename': f'text2qti_text_{item.id}.xml',
                    'xml': text_item_xml,
                    'interaction_types': []
                })
        
        # Prepare item resources for manifest
        item_resources = []
        for item in self.assessment_items:
            item_resources.append({
                'identifier': item['identifier'],
                'file': item['filename'],
                'interaction_types': item['interaction_types']
            })
        
        # Generate manifest
        self.imsmanifest_xml = imsmanifest21(
            manifest_identifier=self.manifest_identifier,
            test_identifier=self.test_identifier,
            test_file=self.test_filename,
            item_resources=item_resources,
            images=self.quiz.images
        )
    
    def _get_interaction_types(self, question: Question) -> list:
        """Get the interaction types for a question (for metadata)."""
        type_map = {
            'true_false_question': ['choiceInteraction'],
            'multiple_choice_question': ['choiceInteraction'],
            'multiple_answers_question': ['choiceInteraction'],
            'short_answer_question': ['textEntryInteraction'],
            'numerical_question': ['textEntryInteraction'],
            'essay_question': ['extendedTextInteraction'],
            'file_upload_question': ['uploadInteraction'],
        }
        return type_map.get(question.type, [])
    
    def write(self, bytes_stream: BinaryIO):
        """Write the QTI 2.1 package to a stream."""
        with zipfile.ZipFile(bytes_stream, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            # Write manifest
            zf.writestr('imsmanifest.xml', self.imsmanifest_xml)
            
            # Create directory structure (empty directories aren't stored, but we write marker files)
            zf.writestr(zipfile.ZipInfo('assessmentTests/'), b'')
            zf.writestr(zipfile.ZipInfo('assessmentItems/'), b'')
            
            # Write assessment test
            zf.writestr(f'assessmentTests/{self.test_filename}', self.assessment_test_xml)
            
            # Write assessment items
            for item in self.assessment_items:
                zf.writestr(f'assessmentItems/{item["filename"]}', item['xml'])
            
            # Write images
            for image in self.quiz.images.values():
                zf.writestr(image.qti_zip_path, image.data)
    
    def zip_bytes(self) -> bytes:
        """Get the QTI 2.1 package as bytes."""
        stream = io.BytesIO()
        self.write(stream)
        return stream.getvalue()
    
    def save(self, qti_path: Union[str, pathlib.Path]):
        """Save the QTI 2.1 package to a file."""
        if isinstance(qti_path, str):
            qti_path = pathlib.Path(qti_path)
        elif not isinstance(qti_path, pathlib.Path):
            raise TypeError
        qti_path.write_bytes(self.zip_bytes())
