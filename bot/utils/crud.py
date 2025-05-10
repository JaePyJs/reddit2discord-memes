from sqlalchemy.orm import Session
from bot.utils.models import Template, UserPreference, SavedMeme, MemeHistory, MemeRating
import datetime

# --- Template CRUD ---
def create_template(session: Session, filename, uploader_id, is_builtin=False):
    t = Template(filename=filename, uploader_id=uploader_id, is_builtin=is_builtin)
    session.add(t)
    session.commit()
    return t

def get_template(session: Session, filename):
    return session.query(Template).filter_by(filename=filename).first()

def list_templates(session: Session):
    return session.query(Template).all()

def delete_template(session: Session, filename):
    t = get_template(session, filename)
    if t:
        session.delete(t)
        session.commit()

# --- UserPreference CRUD ---
def get_user_pref(session: Session, user_id):
    up = session.query(UserPreference).filter_by(user_id=user_id).first()
    if not up:
        up = UserPreference(user_id=user_id, favorite_templates='', favorite_style=None)
        session.add(up)
        session.commit()
    return up

def set_favorite_templates(session: Session, user_id, templates):
    up = get_user_pref(session, user_id)
    up.favorite_templates = ','.join(templates)
    session.commit()

def set_favorite_style(session: Session, user_id, style):
    up = get_user_pref(session, user_id)
    up.favorite_style = style
    session.commit()

# --- SavedMeme CRUD ---
def save_meme(session: Session, user_id, meme_url):
    s = SavedMeme(user_id=user_id, meme_url=meme_url)
    session.add(s)
    session.commit()
    return s

def list_saved_memes(session: Session, user_id):
    return session.query(SavedMeme).filter_by(user_id=user_id).all()

def delete_saved_meme(session: Session, meme_id):
    m = session.query(SavedMeme).filter_by(id=meme_id).first()
    if m:
        session.delete(m)
        session.commit()

# --- MemeHistory CRUD ---
def add_meme_history(session: Session, server_id, user_id, meme_url, template_filename):
    m = MemeHistory(server_id=server_id, user_id=user_id, meme_url=meme_url, template_filename=template_filename)
    session.add(m)
    session.commit()
    return m

def list_meme_history(session: Session, server_id=None, user_id=None):
    q = session.query(MemeHistory)
    if server_id:
        q = q.filter_by(server_id=server_id)
    if user_id:
        q = q.filter_by(user_id=user_id)
    return q.all()

# --- MemeRating CRUD ---
def rate_meme(session: Session, meme_id, user_id, rating):
    r = MemeRating(meme_id=meme_id, user_id=user_id, rating=rating)
    session.add(r)
    session.commit()
    return r

def list_ratings_for_meme(session: Session, meme_id):
    return session.query(MemeRating).filter_by(meme_id=meme_id).all()

def get_user_rating(session: Session, meme_id, user_id):
    return session.query(MemeRating).filter_by(meme_id=meme_id, user_id=user_id).first()
