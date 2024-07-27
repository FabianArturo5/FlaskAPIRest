from config import SQLALCHEMY_DATABASE_URI
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import logging
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

logging.basicConfig(level=logging.DEBUG)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    done = db.Column(db.Boolean, default=False)

class TaskResource(Resource):
    def get(self, task_id=None):
        try:
            if task_id:
                task = Task.query.get_or_404(task_id)
                return {'id': task.id, 'title': task.title, 'description': task.description, 'done': task.done}
            tasks = Task.query.all()
            return [{'id': t.id, 'title': t.title, 'description': t.description, 'done': t.done} for t in tasks]
        except SQLAlchemyError as e:
            logging.error(f"Error en GET: {str(e)}")
            return {'message': 'Error de base de datos'}, 500

    def post(self):
        try:
            data = request.get_json()
            if not data:
                return {'message': 'No input data provided'}, 400
            if 'title' not in data:
                return {'message': 'Title is required'}, 400
            
            new_task = Task(title=data['title'], description=data.get('description', ''))
            db.session.add(new_task)
            db.session.commit()
            return {'id': new_task.id, 'title': new_task.title, 'description': new_task.description, 'done': new_task.done}, 201
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error in POST: {str(e)}")
            return {'message': 'Database error occurred'}, 500
        except Exception as e:
            logging.error(f"Unexpected error in POST: {str(e)}")
            return {'message': 'An unexpected error occurred'}, 500

    def put(self, task_id):
        try:
            task = Task.query.get_or_404(task_id)
            data = request.get_json()
            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.done = data.get('done', task.done)
            db.session.commit()
            return {'id': task.id, 'title': task.title, 'description': task.description, 'done': task.done}
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Error en PUT: {str(e)}")
            return {'message': 'Error de base de datos'}, 500

    def delete(self, task_id):
        try:
            task = Task.query.get_or_404(task_id)
            db.session.delete(task)
            db.session.commit()
            return '', 204
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Error en DELETE: {str(e)}")
            return {'message': 'Error de base de datos'}, 500

api.add_resource(TaskResource, '/tasks', '/tasks/<int:task_id>')

@app.route('/')
def home():
    return "Bienvenido a la API de Tareas. Use /tasks para acceder a los endpoints."

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Base de datos creada exitosamente")
        except SQLAlchemyError as e:
            print(f"Error al crear la base de datos: {str(e)}")
    app.run(debug=True)