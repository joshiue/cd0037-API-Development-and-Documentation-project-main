import os
from unicodedata import category

from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# Questions pagination <--Done
def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]

    return questions[start:end]


def create_app(test_config=None):
    # create and configure Triva app <--Done
    app = Flask(__name__)
    setup_db(app)

    # CORS app <--Done
    CORS(app, resource={"/": {"origins": "*"}})

    # CORS <--Done
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    # Endpoint to handle GET requests for all available categories ---Done

    @app.route("/categories")
    def available_categories_type():

        # get all type category
        selection = Category.query.order_by(Category.id).all()
        current_category = paginate_questions(request, selection)

        if len(current_category) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "categories": {category.id: category.type for category in selection},
                "total_categories": len(Category.query.all()),
            }
        )

    # Endpoint to handling GET questions, pagination (10 questions). Endpoint returns a list of questions, total questions, type, categories.

    @app.route("/questions")
    def available_questions():
        try:
            # all questions 
            selection = Question.query.order_by(Question.id).all()

            # list questions in a page
            current_questions = paginate_questions(request, selection)

            if len(current_questions) == 0:
                abort(404)

            return jsonify(
                {
                    "success": True,
                    "list_of_questions": current_questions,
                    "total_questions": len(Question.query.all()),
                    "current_category": [],
                    "categories": [category.type for category in Category.query.all()],
                }
            )
        except Exception:
            abort(422)

    # Endpoint to DELETE question via ? question ID.

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            # fetch question through question id filtering
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            # Post to reflect in front end
            current_question = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question.id,
                    "questions": current_question,
                    "total_questions": len(Question.query.all()),
                }
            )

        except Exception:
            abort(422)

    @app.route("/questions", methods=["POST"])
    def create_question():
        # body from frontend input
        body = request.get_json()

        # data frontend `input`
        question = body.get("question", None)
        answer = body.get("answer", None)
        category = body.get("category", None)
        difficulty = body.get("difficulty", None)
        search = body.get("searchTerm", None)

        # Endpoint POST to get questions based on search term. Return questions from search term is a substring of question.
        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike(f"%{search}%")
                )

                # Post to reflect in the front end
                current_questions = paginate_questions(request, selection)

                categories = Category.query.all()
                current_category = {
                    category.id: category.type for category in categories
                }

                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(selection.all()),
                        "current_category": current_category,
                    }
                )

            # Endpoint to POST a new question, require the question and answer text, category, and difficulty rate.
            else:
                question = Question(
                    question=question,
                    answer=answer,
                    category=category,
                    difficulty=difficulty,
                )
                question.insert()

                selection = Question.query.order_by(Question.id).all()

                # Post to reflect in the front end
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "created": question.id,
                        "questions": current_questions,
                        "question_created": question.question,
                        "total_questions": len(Question.query.all()),
                    }
                )

        except Exception:
            abort(422)

    # A GET endpoint to get question in particular path.
    @app.route("/categories/<int:category_id>/questions")
    def category_question_list(category_id):
        try:
            c_id = category_id + 1

            # fetch question in a path by id
            category = Category.query.filter(Category.id == c_id).one_or_none()

            if category is None:
                abort(404)

            # fetch all question in the selected category
            selection = (
                Question.query.filter(Question.category == category.id)
                .order_by(Question.id)
                .all()
            )

            # Post the update in the front end
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                    "categories": [category.type for category in Category.query.all()],
                    "current_category": category.type,
                }
            )
        except Exception:
            abort(400)

    # A POST endpoint to get questions to play the quiz.
    # This endpoint takes category and previous question parametersand return a random questions within the given category, if provided, and that is not one of the previous questions.

    @app.route("/quizzes", methods=["POST"])
    def fetch_quizzes_list():
        # get the qestion category
        body = request.get_json()
        quiz_category = body.get("quiz_category", None)
        previous_questions = body.get("previous_questions", None)
        category_id = quiz_category["id"]

        try:

            # Filter available questions by all category and new questions
            if category_id == 0:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions)
                ).all()

            else:
                category = Category.query.get(category_id)
                # Filter available questions by chosen category & new questions
                if category is not None:
                    questions = Question.query.filter(
                        Question.id.notin_(previous_questions),
                        Question.category == category_id,
                    ).all()

            next_question = None

            # randomize the question
            if len(questions) > 0:
                next_question = random.choice(questions).format()

            return jsonify(
                {
                    "success": True,
                    "question": next_question,
                    "total_questions": len(questions),
                }
            )

        except Exception:
            abort(404)

    ############# Error handlers #############

    @app.errorhandler(404)
    def file_absent(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable_path(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request_log(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def file_absent(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405,
        )

    @app.errorhandler(505)
    def file_absent(error):
        return (
            jsonify(
                {"success": False, "error": 505, "message": "Internal server error"}
            ),
            405,
        )

    return app