from datetime import datetime, timedelta
from hashlib import md5
from flask import current_app
from app import login, db, ma
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import jwt
from time import time
from flask import url_for
from sqlalchemy import Table, Column, Float, Integer, String, MetaData
import base64
import os
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from marshmallow_sqlalchemy.fields import Nested

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        print('------------------')
        print(resources.items)
        print('------------------')
        
        data = {
            'items': [item.to_dict() for item in resources.items]
            # ,
            # '_meta': {
            #     'page': page,
            #     'per_page': per_page,
            #     'total_pages': resources.pages,
            #     'total_items': resources.total
            # },
            # '_links': {
            #     'self': url_for(endpoint, page=page, per_page=per_page,
            #                     **kwargs),
            #     'next': url_for(endpoint, page=page + 1, per_page=per_page,
            #                     **kwargs) if resources.has_next else None,
            #     'prev': url_for(endpoint, page=page - 1, per_page=per_page,
            #                     **kwargs) if resources.has_prev else None
            # }
        }
        return data


class User(UserMixin, PaginatedAPIMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def __repr__(self):
        return '<User {} Email {}>'.format(self.username, self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password_bruh(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        gravatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
                                                                        digest,
                                                                        size)
        print(gravatar)
        return gravatar

    # followed_posts 
    def timeline(self):
        followed_posts = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed_posts.union(own).order_by(Post.timestamp.desc())

    # Start API ###########
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    # start api authentication
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def get_token(self, expires_in=360):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(240))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    soso = db.Column(db.String(100))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Resource(PaginatedAPIMixin, db.Model):
    id = db.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    parent_name = db.Column(db.String(128), index=True, nullable=True)
    instance_type = db.Column(db.String(32), nullable=True)
    # posts = db.relationship('Post', backref='author', lazy='dynamic')
    # bruh = db.Column(db.String(32))
    resource_usages = db.relationship('ResourceUsage',
                                      backref='resource',
                                      lazy='dynamic')
    imported_at = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)

    def __repr__(self):
        return '< Instance {} {} Parent {} Imported at {}>'.format(self.instance_type,
                                                                      self.name,
                                                                      self.parent_name,
                                                                      self.imported_at)

    # Start API ###########
    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'parent_name': self.parent_name,
            'instance_type': self.instance_type,
            'imported_at': self.imported_at.isoformat() + 'Z'
            # ,
            # 'resource_usage_count': self.resource_usages.count()
        }
        return data

    def from_dict(self, data, new_data=False):
        for field in ['name', 'parent_name', 'instance_type', 'imported_at']:
            if field == 'imported_at':
                data[field] = datetime.strptime(data[field],
                                                '%Y-%m-%d %H:%M:%S')# '%m/%d/%y %H:%M:%S')
            if field in data:
                setattr(self, field, data[field])
        if new_data:
            print('-before add save--------------')
            # self = data
            # self.set_password(data['password'])


class ResourceUsage(PaginatedAPIMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usage_type_code = db.Column(db.String(32), nullable=True)
    resource_name = db.Column(db.String(128), nullable=False)
    capacity = db.Column(db.Float())
    usage = db.Column(db.Float())
    available = db.Column(db.Float())
    uom_code = db.Column(db.String(128), nullable=False)
    imported_at = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    resource_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resource.id'))

    # def __init__(self, usage_type_code, resource_id, resource_name, usage,
    #              capacity, available, uom_code, imported_at):
    #     self.usage_type_code = usage_type_code
    #     self.resource_id = resource_id
    #     self.resource_name = resource_name
    #     self.usage = usage
    #     self.capacity = capacity
    #     self.available = available
    #     self.uom_code = uom_code
    #     self.imported_at = imported_at

    def __repr__(self):
        message = '< {} {} Capacity: {} Usage: {} Available: {}{} imported at: {} >'
        return message.format(self.resource_name, self.usage_type_code,
                              self.capacity, self.usage,
                              self.available, self.uom_code, self.imported_at)

    # Start API ###########
    def to_dict(self):
        data = {
            'id': self.id,
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'usage_type_code': self.usage_type_code,
            'capacity': self.capacity,
            'usage': self.usage,
            'available': self.available,
            'uom_code': self.uom_code,
            'imported_at': self.imported_at.isoformat() + 'Z'
            # ,
            # 'resource_usage_count': self.resource_usages.count()
        }
        return data

    def from_dict(self, data, new_data=False):
        for field in ['resource_id', 'resource_name', 'usage_type_code', 'capacity', 
                      'usage', 'available', 'uom_code', 'imported_at']:
            if field == 'imported_at':
                data[field] = datetime.strptime(data[field],
                                                '%Y-%m-%d %H:%M:%S')# '%m/%d/%y %H:%M:%S')
            if field in data:
                setattr(self, field, data[field])
        if new_data:
            print('-before add save--------------')
            # self = data
            # self.set_password(data['password'])


class ResourceUsageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ResourceUsage
        include_fk = True
        # include_relationships = True
        load_instance = True


class ResourceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Resource
        include_relationships = True
        load_instance = True
    resource_usages = Nested(ResourceUsageSchema, many=True,
                             exclude=['resource_id'])
