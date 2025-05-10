from sqlalchemy.orm import Session
from bot.utils.models import MemeRating
from sqlalchemy import func

def rate_meme(session: Session, meme_id: int, user_id: int, rating: int):
    """
    Add or update a user's rating for a meme.
    """
    existing = session.query(MemeRating).filter_by(meme_id=meme_id, user_id=user_id).first()
    if existing:
        existing.rating = rating
    else:
        new_rating = MemeRating(meme_id=meme_id, user_id=user_id, rating=rating)
        session.add(new_rating)
    session.commit()


def get_meme_rating(session: Session, meme_id: int):
    """
    Get the average rating and number of ratings for a meme.
    Returns (average, count), or (None, 0) if no ratings.
    """
    result = session.query(func.avg(MemeRating.rating), func.count(MemeRating.rating)).filter_by(meme_id=meme_id).first()
    if result and result[1]:
        return float(result[0]), int(result[1])
    else:
        return None, 0
