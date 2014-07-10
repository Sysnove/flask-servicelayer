# -*- coding: utf-8 -*-
'''
    flask.ext.servicelayer
    ----------------------

    This modules provides some classes to build a Service layer and expose
    an API that interacts with the model. The idea is to remove all
    intelligence of the routes and model, and put it in the service layer.

    :copyright: (c) 2014 by Guillaume Subiron.
'''

import abc
from math import ceil

from flask import abort


class ServiceError(Exception):
    """Base application error class."""

    def __init__(self, msg):
        self.msg = msg


class ServiceForbidden(Exception):
    """Raise when an action is forbidden."""

    def __init__(self, msg):
        self.msg = msg


class ServiceFormError(Exception):
    """Raise when an error processing a form occurs."""

    def __init__(self, errors=None):
        self.errors = errors


class BaseService(object):
    __metaclass__ = abc.ABCMeta
    __model__ = None

    def _isinstance(self, obj, raise_error=True):
        """
            Checks if the specified object matches the service's model.
            By default this method will raise a `ValueError` if the model is
            not the expected type.

            :param obj: the object to check
            :param raise_error: flag to raise an error on a mismatch
        """
        rv = isinstance(obj, self.__model__)
        if not rv and raise_error:
            raise ValueError('%s is not of type %s' % (obj, self.__model__))
        return rv

    def _preprocess_params(self, kwargs):
        """
            Returns a preprocessed dictionary of parameters. Used by default
            before creating a new instance or updating an existing instance.

            :param kwargs: a dictionary of parameters
        """
        kwargs.pop('csrf_token', None)
        kwargs.pop('submit', None)
        return kwargs

    @abc.abstractmethod
    def save(self, obj):
        """
            Commits the object to the database and returns the object.
        """

    @abc.abstractmethod
    def all(self, obj):
        """
            Returns a generator containing all instances of model.
            :param obj: the object to save
        """

    @abc.abstractmethod
    def get(self, obj):
        """
            Returns an instance of the service's model with the specified id.
        """

    @abc.abstractmethod
    def get_all(self, *ids):
        """
            Returns a list of instances of the service's model with the
            specified ids.

            :param *ids: instance ids
        """

    @abc.abstractmethod
    def find(self, **kwargs):
        """
            Returns a list of instances of the service's model filtered by the
            specified key word arguments.

            :param **kwargs: filter parameters
        """

    @abc.abstractmethod
    def first(self, **kwargs):
        """
            Returns the first instance found of the service's model filtered by
            the specified key word arguments.

            :param **kwargs: filter parameters
        """

    @abc.abstractmethod
    def one(self, **kwargs):
        """
            Returns the instance found of the service's model filtered by
            the specified key word arguments. Exception if there is more
            than one instance.

            :param **kwargs: filter parameters
        """

    def get_or_404(self, id):
        """
            Returns an instance of the service's model with the specified id or
            raises an 404 error if an instance with the specified id does not
            exist.

            :param id: the instance id
        """
        return self.get(id) or abort(404)

    @abc.abstractmethod
    def new(self, **kwargs):
        """
            Returns a new, unsaved instance of the service's model class.

            :param **kwargs: instance parameters
        """

    @abc.abstractmethod
    def create(self, **kwargs):
        """
            Returns a new, saved instance of the service's model class.

            :param **kwargs: instance parameters
        """
        return self.save(self.new(**kwargs))

    @abc.abstractmethod
    def update(self, obj, **kwargs):
        """
            Returns an updated instance of the service's model class.

            :param obj: the object to update
            :param **kwargs: update parameters
        """

    @abc.abstractmethod
    def delete(self, obj):
        """
            Immediately deletes the specified model instance.

            :param obj: the model instance to delete
        """

    @abc.abstractmethod
    def paginate(self, page=1, per_page=10, order_by=None, desc=False,
                 filter_by={}, error_out=True):
        """
            :TODO:maethor:140407: Pagination

            :param page: page to return
            :param per_page: number of items in a page
            :param order_by: model attribute used to order elements, default=id
            :param desc: descendant sort, default=False
            :param filter_by: filter parameters
            :param error_out: abort 404 if no items where found on the page?
        """


class SQLAlchemyService(BaseService):
    """
        A `Service` instance that encapsulates common SQLAlchemy model
        operations in the context of a `Flask` application.
    """
    __db__ = None

    def save(self, obj):
        self._isinstance(obj)
        self.__db__.session.add(obj)
        self.__db__.session.commit()
        return obj

    def all(self):
        return self.__model__.query.all()

    def get(self, id):
        return self.__model__.query.get(id)

    def get_all(self, *ids):
        return self.__model__.query.filter(self.__model__.id.in_(ids)).all()

    def _find(self, **kwargs):
        return self.__model__.query.filter_by(**kwargs)

    def find(self, **kwargs):
        return self._find(**kwargs).all()

    def first(self, **kwargs):
        return self._find(**kwargs).first()

    def one(self, **kwargs):
        return self._find(**kwargs).one()

    def get_or_404(self, id):
        return self.__model__.query.get_or_404(id)

    def new(self, **kwargs):
        return self.__model__(**self._preprocess_params(kwargs))

    def update(self, model, **kwargs):
        self._isinstance(model)
        for k, v in self._preprocess_params(kwargs).items():
            setattr(model, k, v)
        self.save(model)
        return model

    def delete(self, obj):
        self._isinstance(obj)
        self.__db__.session.delete(obj)
        self.__db__.session.commit()

    def paginate(self, page=1, per_page=10, order_by=None, desc=False,
                 filter_by={}, error_out=True):
        """
            Returns a SQLAlchemy Pagination object of all results.
        """
        order_by = order_by or self.__model__.id
        order_by = order_by.desc() if desc else order_by.asc()
        return self.__model__.query.filter_by(**filter_by).order_by(order_by)\
            .paginate(page, per_page, error_out)


class LDAPOMService(BaseService):
    """
        A `Service` instance that encapsulates Python 3 LDAPOM model
        operations in the context of a `Flask` application.
    """
    __ldap__ = None

    def _compute_dn(self, kwargs):
        """
            Returns the dn of the entry. Used by default to create a new
            instance.

            :param kwargs: a dictionary of parameters
        """
        return "%s=%s,%s" % (self.__model__._rdn,
                             kwargs[self.__model__._rdn],
                             self.__ldap__._base)

    def save(self, obj):
        obj.save()
        return obj

    def all(self):
        return list(self.__model__.search(self.__ldap__))

    def get(self, id):
        return self.__model__.retrieve(self.__ldap__, id)

    def get_or_404(self, id):
        from ldapom_model import NoResultFound
        try:
            return self.get(id)
        except NoResultFound:
            return abort(404)

    def get_all(self, *ids):
        # :DEBUG:maethor:140604: Find a better algo using find
        return [self.get(id) for id in ids]

    def find(self, **kwargs):
        return list(self.__model__.search(self.__ldap__, **kwargs))

    def first(self, **kwargs):
        try:
            return self.find(**kwargs)[0]
        except IndexError:
            # :TODO:maethor:140604: Return an error
            return abort(404)

    def one(self, **kwargs):
        # :TODO:maethor:140604: Personalize exceptions
        res = self.find(**kwargs)
        if not res:
            raise Exception
        if len(res) > 1:
            raise Exception
        else:
            return res[0]

    def _preprocess_params(self, kwargs):
        kwargs = super()._preprocess_params(kwargs)
        return {k: v for k, v in kwargs.items() if v != ''}

    def new(self, **kwargs):
        return self.__model__(self.__ldap__, self._compute_dn(kwargs),
                              **self._preprocess_params(kwargs))

    def update(self, obj, **kwargs):
        self._isinstance(obj)
        for k, v in kwargs.items():
            if v == '':
                delattr(obj, k)
        for k, v in self._preprocess_params(kwargs).items():
            setattr(obj, k, v)
        self.save(obj)
        return obj

    def delete(self, obj):
        obj.delete()

    def paginate(self, page=1, per_page=10, order_by=None, desc=False,
                 filter_by={}, error_out=True):
        if filter_by:
            raise NotImplementedError("filter_by parameter is not implemented \
                                       yet.")
        else:
            objects = self.all()
            total = len(objects)
        if error_out and (page-1)*per_page < total:
            abort(404)
        objects = objects[(page-1)*per_page:page*per_page]
        return Pagination(page, per_page, total, objects)


class LDAPOMCachedService(LDAPOMService):

    def __init__(self):
        super().__init__()
        self._all_cache = None
        self._get_cache = dict()
        self._find_cache = dict()

    def all(self):
        if self._all_cache is None:
            self._all_cache = super().all()
        for e in self._all_cache:
            self._get_cache[e.id] = e
        return self._all_cache

    def get(self, id):
        if id not in self._get_cache:
            self._get_cache[id] = super().get(id)
        return self._get_cache[id]

    def find(self, **kwargs):
        h = hash(tuple([i for i in kwargs.items()]))
        if h not in self._find_cache:
            self._find_cache[h] = super().find(**kwargs)
        return self._find_cache[h]


class Pagination(object):

    def __init__(self, page, per_page, total, items):
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self):
        return int(ceil(self.total / float(self.per_page)))

    @property
    def has_prev(self):
        """
            True if a previous page exists.
        """
        return self.page > 1

    @property
    def has_next(self):
        """
            True if a next page exists.
        """
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
