# Database Models with SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app import db # Assuming 'app' is your Flask instance

class Movie(db.Model):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1024))
    release_year = Column(Integer)
    genre_id = Column(Integer, ForeignKey('genres.id'))

    genre = relationship("Genre", back_populates="movies")


class Genre(db.Model):
    __tablename__ = 'genres'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    movies = relationship("movie", back_populates="genre")


#  GraphQL Schema with Graphene
# GraphQL Types
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from models import Movie, Genre

class MovieType(SQLAlchemyObjectType):
    class Meta:
        model = Movie
    
class GenreType(SQLAlchemyObjectType):
    class Meta:
        model = Genre

# Mutations for Genre
from app import db

class CreateGenre(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
    
    genre = graphene.Field(lambda: GenreType)

def mutate(self, info, name):
    if not name or len(name) > 100:
        raise Exception("Genre name must be provided and less than 100 characters")
    
    genre = Genre(name=name)
    db.session.add(genre)
    db.session.commit()

    return CreateGenre(genre=genre)

class UpdateGenre(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String(required=True)

    genre = graphene.Field(lambda: GenreType)


    def mutate(self, info, id, name):
        genre = Genre.query.get(id)
        if not genre:
            raise Exception("Genre not found")
        if not name or len(name) > 100:
            raise Exception("Invalid genre name")
        
        genre.name = name
        db.session.commit()

        return UpdateGenre(genre=genre)

class DeleteGenre(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        genre = Genre.query.get(id)
        if not genre:
            raise Exception("Genre not found")
        
        db.session.delete(genre)
        db.session.commit()

        return DeleteGenre(success=True)

# Mutations Root
class Mutation(graphene.ObjectType):
    create_genre = CreateGenre.Field()
    update_genre = UpdateGenre.Field()
    delete_genre = DeleteGenre.Field()

# GraphQL Queries
# Queries to Fetch Movies by Genre and Genre by Movie

class Query(graphene.ObjectType):
    movies_by_genre = graphene.List(MovieType, genre_id=graphene.Int())
    genre_by_movie = graphene.Field(GenreType, movie_id=graphene.Int())

    def resolve_genre_by_movie(self, info, movie_id):
        movie = Movie.query.get(movie_id)
        if not movie:
            raise Exception("Movie not found")
        return movie.genre

# Complete Schema Definition
schema = graphene.Schema(query=Query, mutation=Mutation)

# Flask App Setup
from flask import Flask
from flask_graphql import GraphQLView
from models import db
from schema import Schema # Assuming the schema code above is in schema.py

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:password@localhost/moviedb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True # Enable GraphiQL interface
    )
)


if __name__ == '__main__':
    app.run(debug=True)

# Migration Setup
# pip install Flask-Migrate
# In app.py:
from flask_migrate import Migrate

migrate = Migrate(app, db)

# Run the migrations:
flask db init
flask db migrate
flask upgrade



