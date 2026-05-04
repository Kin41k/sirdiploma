from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from app.models.rating import Rating
from app.models.movie import Movie
from app.schemas.rating import RatingCreate, RatingResponse


def upsert_rating(db: Session, user_id: int, data: RatingCreate) -> RatingResponse:
    movie = db.query(Movie).filter(Movie.id == data.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing = db.query(Rating).filter(
        Rating.user_id == user_id, Rating.movie_id == data.movie_id
    ).first()

    if existing:
        existing.rating = data.rating
        db.commit()
        db.refresh(existing)
        return RatingResponse.model_validate(existing)

    rating = Rating(user_id=user_id, movie_id=data.movie_id, rating=data.rating)
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return RatingResponse.model_validate(rating)


def get_user_ratings(db: Session, user_id: int) -> list[RatingResponse]:
    ratings = db.query(Rating).filter(Rating.user_id == user_id).order_by(Rating.timestamp.desc()).all()
    return [RatingResponse.model_validate(r) for r in ratings]


def count_user_ratings(db: Session, user_id: int) -> int:
    return db.query(Rating).filter(Rating.user_id == user_id).count()
