from mongoengine import *
from datetime import datetime
from bson import ObjectId

class SpecsModel(EmbeddedDocument):
    _id = ObjectIdField(default=ObjectId)
    name = StringField(max_length=50)
    value = StringField(max_length=50)
    units = StringField(max_length=50)

class SourcesModel(EmbeddedDocument):
    _id = ObjectIdField(default=ObjectId)
    title = StringField(max_length=200)
    link = StringField(max_length=200)
    summary = StringField(max_length=300)
    authors = StringField(max_length=200)

class GalleryModel(EmbeddedDocument):
    _id = ObjectIdField(default=ObjectId)
    src = StringField(max_length=200)
    type = StringField(max_length=20)

class OverviewModel(EmbeddedDocument):
    summary = StringField()
    body = StringField()
    goal = StringField()
    team = StringField()
    roadmap = StringField()
    spec_table = ListField(EmbeddedDocumentField(SpecsModel))
    sources = ListField(EmbeddedDocumentField(SourcesModel))
    gallery = ListField(EmbeddedDocumentField(GalleryModel))

class ProjectModel(Document):
    name = StringField(max_length=120, required=True)
    welder_uri = StringField(max_length=300, required=True)
    created_user = IntField()
    created_user_id = ObjectIdField()
    slug = StringField(max_length=120, required=True, unique_with="user_slug")
    created_at = DateTimeField(default=datetime.utcnow(), required=True)
    user_slug = StringField(max_length=120, required=True)
    university = StringField(max_length=120)
    privacy = IntField(default=1, required=True)
    imported = BooleanField()
    description = StringField(max_length=1000)
    version = StringField(max_length=10)
    created_at = DateTimeField()
    bookmark_count = IntField(default=0)
    fork_origin = StringField(max_length=220)
    forkers = ListField()
    tags = ListField(StringField(max_length=120))
    hidden_tags = ListField(StringField(max_length=120))
    members = ListField(DictField())
    followers = ListField(DictField())
    picture = DictField()
    comments = ListField(DictField())
    comments_enabled = BooleanField()
    legacy_id = IntField()
    overview = EmbeddedDocumentField(OverviewModel)
    license = StringField(max_length=120)
    meta = {
        'collection': 'project',
        'strict': False,
        'indexes': [
            'tags',
            'user_slug',
            'slug',
        ]
    }

class UserModel(Document):
    legacy_id = IntField()
    email = StringField(max_length=120, required=True, unique=True)
    location = StringField(max_length=120)
    picture = DictField()
    slug = StringField(max_length=120, required=True, unique=True, sparse=True)
    first_name = StringField(max_length=120)
    last_name = StringField(max_length=120)
    bio = StringField(max_length=1000)
    website = StringField(max_length=120)
    profession = StringField(max_length=120)
    twitter = StringField(max_length=120)
    linkedin = StringField(max_length=120)
    facebook = StringField(max_length=120)
    instagram = StringField(max_length=120)
    accepts_newsletter = BooleanField(default=False)
    accepts_cookies = BooleanField(default=False)
    notify_toggle = BooleanField(default=False)
    company_profile = BooleanField(default=False)
    tags_followed = ListField()
    followers = ListField()
    auth0_id = StringField(max_length=120)
    plan=StringField(max_length=90)
    meta = {'collection': 'user'}

class BookmarkModel(Document):
    legacy_user_id = IntField()
    user_id = ObjectIdField()
    project_id = ObjectIdField()
    created_at = DateTimeField(default=datetime.utcnow(), required=True)
    meta = {
        'indexes': [
            'project_id',
        ]
    }

class TagModel(Document):
    name = StringField(max_length=120, required=True, unique=True)
    displayName = StringField(max_length=120)
    weight = IntField(default=0)
    followCount = IntField(default=0)
    counts = DictField()
    meta = {
        'collection': 'tag',
        'indexes': [
            'name'
        ]
    }

class TagCategoryModel(Document):
    name = StringField(max_length=120, required=True, unique=True)
    searchTags = ListField()
    relatedTags = ListField()
    active = BooleanField()

class SearchModel(Document):
    query = StringField(max_length=120, required=True)
    ipAddress = StringField(max_length=120)
    date_searched = DateTimeField(default=datetime.utcnow(), required=True)

class CommentModel(Document):
    text = StringField(max_length=20000, required=True)
    author = IntField()
    author_id = ObjectIdField()
    dateCreated = DateTimeField(required=True)
    discusses = ObjectIdField() # the object id that this comment is about (project_id most likely)
    parentItem = ObjectIdField(default=None)
    meta = {
        'collection': 'comment',
        'indexes': [
            'discusses'
        ]
    }
