import cPickle as pickle
import json
import os
from dframe.dataset.dataset import Dataset

import config as config


class VQADataset(Dataset):
    """Class that holds the VQA 1.0 dataset of the VQA challenge.
    You can find the data here: http://www.visualqa.org/download.html"""

    PARSED_DATASET_PATH = os.path.join(config.DATA_PATH, 'parsed_dataset.p')
    PARSED_IMAGES_KEY = 'images'
    PARSED_QUESTIONS_KEY = 'questions'
    PARSED_ANSWERS_KEY = 'answers'

    def __init__(self, images_path, questions_path, annotations_path):
        # Assign attributes
        self.images_path = images_path
        self.questions_path = questions_path
        self.annotations_path = annotations_path

        super(VQADataset, self).__init__()

        # Build dataset
        self.build()

    def build(self, force=False):
        """Creates the dataset with all of its samples.
        This method saves a parsed version of the VQA 1.0 dataset information in ROOT_PATH/data, which can lately
        be used to reconstruct the dataset, saving a lot of processing. You can however force to reconstruct the dataset
        from scratch with the 'force' param.
        Note that it does not save the dataset itself but a middle step with the data formatted
        Args:
            force (bool): True to force the building of the dataset from the raw data. If False is given, this method
                will look for the parsed version of the data to speed up the process
        """

        print 'Building dataset...'

        if force:
            parsed_dataset = self.__parse_dataset()
        else:
            parsed_dataset = self.__retrieve_parsed_dataset()
            if parsed_dataset is None:
                parsed_dataset = self.__parse_dataset()

        images = parsed_dataset[self.PARSED_IMAGES_KEY]
        questions = parsed_dataset[self.PARSED_QUESTIONS_KEY]
        answers = parsed_dataset[self.PARSED_ANSWERS_KEY]

    @staticmethod
    def get_image_id(image_name):
        # Image name has the form: COCO_[train|val|test][2014|2015]_{image_id 12 digits}.jpg
        image_id = image_name.split('_')[-1]  # Retrieve image_id.jpg
        image_id = image_id.split('.')[0]  # Remove file format
        return int(image_id)  # Convert to int and return

    def __retrieve_parsed_dataset(self):
        if not os.path.isfile(self.PARSED_DATASET_PATH):
            return None

        with open(self.PARSED_DATASET_PATH, 'rb') as f:
            print 'Loading parsed dataset from: {}'.format(self.PARSED_DATASET_PATH)
            parsed_dataset = pickle.load(f)

        return parsed_dataset

    def __parse_dataset(self):
        # Parse partial sets
        print 'Parsing dataset...'
        images = self.__parse_images()
        questions = self.__parse_questions()
        answers = self.__parse_annotations()
        parsed_dataset = {self.PARSED_IMAGES_KEY: images,
                          self.PARSED_QUESTIONS_KEY: questions,
                          self.PARSED_ANSWERS_KEY: answers}

        # Save parsed dataset for later reuse
        if not os.path.isdir(config.DATA_PATH):
            os.mkdir(config.DATA_PATH)
        with open(self.PARSED_DATASET_PATH, 'wb') as f:
            print 'Saving parsed dataset to: {}'.format(self.PARSED_DATASET_PATH)
            pickle.dump(parsed_dataset, f)

        return parsed_dataset

    def __parse_images(self):
        print 'Parsing images from image directory: {}'.format(self.images_path)

        image_filenames = os.listdir(self.images_path)
        images = {self.get_image_id(image_filename): Image(self.get_image_id(image_filename),
                                                           os.path.join(self.images_path, image_filename))
                  for image_filename in image_filenames}
        return images

    def __parse_questions(self):
        print 'Parsing questions json file: {}'.format(self.questions_path)

        with open(self.questions_path, 'rb') as f:
            questions_json = json.load(f)

        questions = {
            question['question_id']: Question(question['question_id'], question['image_id'], question['question'])
            for question in questions_json['questions']}

        return questions

    def __parse_annotations(self):
        print 'Parsing annotations json file: {}'.format(self.annotations_path)

        with open(self.annotations_path, 'rb') as f:
            annotations_json = json.load(f)

        # (annotation['question_id'] * 10 + (answer['answer_id'] - 1): creates a unique answer id
        # The value answer['answer_id'] it is not unique across all the answers, only on the subset of answers
        # of that question.
        # As question_id is composed by appending the question number (0-2) to the image_id (which is unique)
        # we've composed the answer id the same way. The substraction of 1 is due to the fact that the
        # answer['answer_id'] ranges from 1 to 10 instead of 0 to 9
        answers = {(annotation['question_id'] * 10 + (answer['answer_id'] - 1)):
                       Answer(answer['answer_id'], annotation['question_id'], annotation['image_id'],
                              answer['answer'])
                   for annotation in annotations_json['annotations'] for answer in annotation['answers']}

        return answers


class Image:
    def __init__(self, image_id, image_path):
        self.id = image_id
        self.path = image_path


class Question:
    def __init__(self, question_id, image_id, question_string):
        self.id = question_id
        self.image_id = image_id
        self.question = question_string


class Answer:
    def __init__(self, answer_id, question_id, image_id, answer_string):
        self.id = answer_id
        self.question_id = question_id
        self.image_id = image_id
        self.answer = answer_string