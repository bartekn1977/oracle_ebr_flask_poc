from flask import Flask, abort, jsonify, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, MetaData, Sequence, String, Table, select
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
metadata_obj = MetaData()


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
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "oracle+oracledb://app_service_user[app_schema]:SomePass4321@localhost:5521/?service_name=testpdb_service"
db.init_app(app)


@app.route('/pets', methods=["GET"])
def all_pets():
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