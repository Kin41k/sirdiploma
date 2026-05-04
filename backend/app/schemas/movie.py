from typing import Optional, List
from pydantic import BaseModel


class MovieBase(BaseModel):
    id: int
    title: str
    vote_average: float
    vote_count: int
    runtime: Optional[int] = None
    original_language: Optional[str] = None
    overview: Optional[str] = None
    popularity: float
    genres: Optional[str] = None
    keywords: Optional[str] = None
    year: Optional[int] = None
    poster_url: Optional[str] = None
    country: Optional[str] = None

    model_config = {"from_attributes": True}


class MovieDetail(MovieBase):
    similar_movies: List[MovieBase] = []
    user_rating: Optional[float] = None
    clicks: int = 0
    views: int = 0


class MovieListItem(MovieBase):
    user_rating: Optional[float] = None


class MovieSearchResult(BaseModel):
    movies: List[MovieListItem]
    total: int
    page: int
    limit: int
    total_pages: int
