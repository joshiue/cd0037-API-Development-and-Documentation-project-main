import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]

    return questions[start:end]

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resource={"/": {"origins": "*"}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
# Get categories looped in array
    @app.route("/categories")
    def get_categories_function(): 
        get_category = Category.query.all()
        current_category = paginate_questions(request, get_category)
        if len(current_category) == 0:
            abort(404)
        return jsonify(
            {
                "success": True,
                "categories": {category.id: category.type for category in get_category},
                "total_categories": len(Category.query.all()),
            }
        )

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route("/question")
    def get_question_function(): 
        try:
            get_Question = Question.query.all()
            current_questions = paginate_questions(request, get_Question)
            if len(current_questions) == 0:
                abort(404)
            return jsonify(
                {
                    "success": True,
                    "list_of_questions": current_questions,
                    "total_questions": len(get_Question),
                    "current_category": [],
                    "categories": [category.type for category in Category.query.all()],
                }
            )
        except:
            abort(422)
    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_questions_function(question_id):
        selection = Question.query.filter(Question.id == question_id).one_or_none()
        if selection is None: 
            abort(404)
        selection.delete()
        return jsonify(
                {
                    "success": True,
                    "deleted": selection.id,
                    "total_questions": len(Question.query.all()),
                }
            )

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route("/questions", methods=["POST"])
    def create_question_list():
        body = request.get_json()

        question = body.get("question", None)
        answer = body.get("answer", None)
        category = body.get("category", None)
        difficulty = body.get("difficulty", None)
        search = body.get("searchTerm", None)

        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike(f"%{search}%")
                )

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

            else:
                question = Question(
                    question=question,
                    answer=answer,
                    category=category,
                    difficulty=difficulty,
                )
                question.insert()

                selection = Question.query.order_by(Question.id).all()

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

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route("/categories/<int:category_id>/questions")
    def category_question_list(category_id):
        try:
            c_id = category_id + 1

            # fetch the question of a category by their id
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

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/quizzes", methods=["POST"])
    def fetch_quizzes_list():
        # get the qestion category
        body = request.get_json()
        quiz_category = body.get("quiz_category", None)
        previous_questions = body.get("previous_questions", None)
        category_id = quiz_category["id"]

        try:
            if category_id == 0:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions)
                ).all()

            else:
                category = Category.query.get(category_id)
                if category is not None:
                    questions = Question.query.filter(
                        Question.id.notin_(previous_questions),
                        Question.category == category_id,
                    ).all()

            next_question = None

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

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
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

