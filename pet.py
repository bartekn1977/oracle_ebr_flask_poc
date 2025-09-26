from flask import Flask, abort, jsonify, redirect, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, MetaData, Sequence, String, Table, select, ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship
from typing import List

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
metadata_obj = MetaData()


class Pet(Base):
    __tablename__ = "PET"
    id: Mapped[int] = mapped_column("ID", Integer, Sequence("PET_SEQ", start=1), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("CATEGORY.ID"))
    category: Mapped["Category"] = relationship(back_populates="pets")
    name: Mapped[str] = mapped_column("NAME", String(30))
    photo: Mapped[str] = mapped_column("PHOTO", String(255), nullable=True)
    tags: Mapped[str] = mapped_column("TAGS", String(30))
    status: Mapped[str] = mapped_column("STATUS", String(30))

    def to_dict(self):
        return {
            "id": self.id,
            "category": dict(self.category.to_dict_no_pets()),
            "name": self.name,
            "photo": self.photo,
            "tags": self.tags,
            "status": self.status
        }
    
    def to_dict_category_id(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "photo": self.photo,
            "tags": self.tags,
            "status": self.status
        }
    

class Category(Base):
    __tablename__ = "CATEGORY"
    id: Mapped[int] = mapped_column("ID", Integer, Sequence("CATEGORY_SEQ", start=1), primary_key=True)
    name: Mapped[str] = mapped_column("NAME", String(20))
    pets: Mapped[List["Pet"]] = relationship(back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "pets": [pet.to_dict_category_id() for pet in self.pets]
        }
    
    def to_dict_no_pets(self):
        return {
            "name": self.name
        }


# initialize the app with the extension
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "oracle+oracledb://app_service_user[app_schema]:SomePass4321@localhost:5521/?service_name=testpdb_service_v2"
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
    app.logger.info('Found Pet %s', pet.to_dict())
    if pet is None:
       return jsonify({"error": "Pet not found"}), 404
    return jsonify(pet.to_dict())

@app.route('/pets', methods=["POST"])
def add_pet():
    content = request.json
    app.logger.info('JSON %s', content)
    category = db.session.scalars(db.select(Category).where(Category.name == content["category"])).first()
    if category is None:
        app.logger.info('No category found, adding new')
        new_category = Category(
            name = content["category"]
        )
        db.session.add(new_category)
        db.session.commit()
        app.logger.info('Added new category: %s', new_category.to_dict_no_pets())
        cat_id = new_category.id
    else:
        app.logger.info('Found category', category.to_dict_no_pets())
        cat_id = category.id

    app.logger.info('Category ID: %s', cat_id)
    new_pet = Pet(
        name = content["name"],
        category_id = cat_id,
        tags = content["tags"],
        status = content["status"],
    )
    db.session.add(new_pet)
    db.session.commit()
    return "added"

@app.route('/categories', methods=["GET"])
def all_categories():
    categories = db.session.execute(db.select(Category).order_by(Category.id)).scalars().all()
    if categories is None:
       return jsonify({"error": "No Category found"}), 404
    return jsonify([category.to_dict() for category in categories])
