import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category

from dotenv import load_dotenv

dotenv_path = os.path.abspath(os.path.dirname(__file__))

# Get environment variables from .env.
load_dotenv(dotenv_path+'/.env')

DATABASE_USER = os.environ.get('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_HOST = os.environ.get('DATABASE_HOST')
TEST_DATABASE_NAME = os.getenv('TEST_DATABASE_NAME')


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    ####### Tests for /categories 
    def test_get_all_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["categories"])

    def test_error_get_all_categories(self):
        res = self.client().get("/categorie")
        data = json.loads(res.data)
        
        ## print("\n Categories error: ", data)
        
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource absent")

    ####### Tests for /questions?page 

    def test_get_paginated_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        ## confirm the presence every necessary key and values
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data['totalQuestions'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['categories'])
        self.assertTrue(data['currentCategory'])

        ## confirm total number of questions are correct
        self.assertEqual(len(data['questions']), data['totalQuestions'])

    ### request beyond the valid page number

    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get("/questions?page=10000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        
    ####### Tests for /questions method = ['POST']

    def test_add_a_new_question(self):
        testQuestion = {
            'question':  'Test Heres a another new question string',
            'answer':  'Heres the new answer string',
            'difficulty': 5,
            'category': 2
        }

        res = self.client().post('/questions', json=testQuestion)

        question = Question.query.filter(
            Question.question == testQuestion['question']).one_or_none()

        data = json.loads(res.data)
        ## print("\n\nadd new question: ", data, '\n\n')
        self.assertTrue(data['success'], True)

    ## test 422_body incomplete (body has no question)
    def test_422_adding_question_without_a_required_field(self):
        testQuestion = {
            'answer':  'testing for wrong answer',
            'difficulty': 1,
            'category': 3,
        }

        res = self.client().post('/questions', json=testQuestion)
        data = json.loads(res.data)

        question = Question.query.filter(
            Question.answer == testQuestion['answer']).one_or_none()
        self.assertIsNone(question)
        self.assertTrue(res.status_code, 422)
        
    ####### Test /questions/{id} method = ['DELETE']

    def test_delete_question(self):
        question = Question.query.with_entities(
            Question.id).order_by(Question.id.desc()).first()
        question_id = question.id
        res = self.client().delete('/questions/{}'.format(question_id))
        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        self.assertEqual(data['id'], question_id)

        self.assertEqual(question, None)

    ## unsuccessful 
    def test_422_if_question_does_not_exit(self):
        question_id = Question.query.count() + 100
        res = self.client().delete('/questions/{}'.format(question_id))
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')
        
    ####### Test /questions?page=${integer}
    
    def test_get_paginated_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        # confirm presence of necessary keys and values
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data['totalQuestions'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['categories'])
        self.assertTrue(data['currentCategory'])

        # confirm number of questions are valid
        self.assertEqual(len(data['questions']), data['totalQuestions'])

    ## request if beyond valid page number

    def test_404_sent_requesting_beyond_valid_page(self):
        res = self.client().get("/questions?page=10000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        
    ####### Tests for /quizzes method = ['POST']
    
    ## successful
    def test_quizzes(self):
        sendData = {
            'previous_questions': [1, 4, 20, 15],
            'quiz_category': {
                'type': 'Arts',
                'id': 1
            }
        }
        res = self.client().post("/quizzes", json=sendData)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data['question'])

    ## successful
    def test_400_missing_request_data_quizzes(self):
        sendData = {
            'quiz_category': {
                'type': 'Arts',
                'id': 1
            }
        }
        res = self.client().post("/quizzes", json=sendData)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["success"], False)
    
    ####### Test search /questions method = ['POST']
    ## successful 
    def test_search(self):
        res = self.client().post("/questions", json={"searchTerm": "ancient"})

        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data['totalQuestions'])
        self.assertTrue(data['questions'])
        self.assertTrue(data['currentCategory'])

    ## unsuccessful
    def test_search_empty_results(self):
        res = self.client().post("/questions", 
        json={"searchTerm": "cbaucvvbvue;89764777736375quvevccquecbecue785387e5127e128e1e7521e"})
        data = json.loads(res.data)
        # print("search: ", data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)



# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()