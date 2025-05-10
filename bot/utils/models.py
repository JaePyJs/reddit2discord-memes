from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, create_engine, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Template(Base):
    __tablename__ = 'templates'
    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True)
    uploader_id = Column(String)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    is_builtin = Column(Boolean, default=False)

class UserPreference(Base):
    __tablename__ = 'user_preferences'
    user_id = Column(String, primary_key=True)
    favorite_templates = Column(Text)  # JSON or comma-separated
    favorite_style = Column(String)
    notify_challenges = Column(Boolean, default=True)

class SavedMeme(Base):
    __tablename__ = 'saved_memes'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    meme_url = Column(Text)
    saved_time = Column(DateTime, default=datetime.datetime.utcnow)

class MemeHistory(Base):
    __tablename__ = 'meme_history'
    id = Column(Integer, primary_key=True)
    server_id = Column(String)
    user_id = Column(String)
    meme_url = Column(Text)
    created_time = Column(DateTime, default=datetime.datetime.utcnow)
    template_filename = Column(String)

class MemeRating(Base):
    __tablename__ = 'meme_ratings'
    id = Column(Integer, primary_key=True)
    meme_id = Column(Integer, ForeignKey('meme_history.id'))
    user_id = Column(String)
    rating = Column(Integer)
    rated_time = Column(DateTime, default=datetime.datetime.utcnow)
    meme = relationship('MemeHistory')

# To create tables: (example usage)
# engine = create_engine('sqlite:///meme_bot.db')
# Base.metadata.create_all(engine)
