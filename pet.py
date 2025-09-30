from flask import Flask, abort, jsonify, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, MetaData, Sequence, String, Table, select, event, text
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped

class Base(DeclarativeBase):
  pass

class Pet(Base):
    __tablename__ = "PET"
    id: Mapped[int] = mapped_column("ID", Integer, Sequence("PET_SEQ", start=1), primary_key=True)
    category: Mapped[str] = mapped_column("CATEGORY", String(20))
    name: Mapped[str] = mapped_column("NAME", String(30))
    photo: Mapped[str] = mapped_column("PHOTO", String(255), nullable=True)
    tags: Mapped[str] = mapped_column("TAGS", String(30))
    status: Mapped[str] = mapped_column("STATUS", String(30))

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "photo": self.photo,
            "tags": self.tags,
            "status": self.status
        }


# initialize the app with the extension

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "oracle+oracledb://app_service_user[app_schema]:SomePass4321@localhost:5521/?service_name=testpdb_service"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Ensure the app context is active so db.engine is available
    with app.app_context():
        @event.listens_for(db.engine, "connect")
        def alter_session_on_connect(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("ALTER SESSION SET EDITION = V1")
            cursor.close()

    return app


app = create_app()

@app.route('/pets', methods=["GET"])
def all_pets():
    #   update_session_version()
    pets = db.session.execute(db.select(Pet).order_by(Pet.id)).scalars().all()
    if pets is None:
       return jsonify({"error": "No Pets found"}), 404
    return jsonify([pet.to_dict() for pet in pets])

@app.route('/pets/<int:id>', methods=["GET"])
def one_pet(id):
    pet = db.session.get(Pet, id)
    if pet is None:
       return jsonify({"error": "Pet not found"}), 404
    return jsonify(pet.to_dict())

@app.route('/pets', methods=["POST"])
def add_pet():
    content = request.json
    
    new_pet = Pet(
        name = content["name"],
        category = content["category"],
        tags = content["tags"],
        status = content["status"],
    )
    db.session.add(new_pet)
    db.session.commit()
    return "added"

@app.teardown_appcontext
def teardown_db(exception):
    if db is not None:
        db.session.close_all()
        db.engine.pool.dispose()

if __name__ == "__main__":
    app.run(debug=True)
