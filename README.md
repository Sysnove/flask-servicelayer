# LDAPOM Model

This package provides some classes to build a Service layer and expose an API that interacts with the model. The first idea is to remove all logic of the routes and model of the Flask application, and put it in the service layer. The second goal is to provide a common API that can be use to manipulate a model regardless of its storage backend.

## Sorry… What?

A common Flask organisation consists in separating model (SQLAlchemy classes, for instance), and routes. When the application grows, you can also use Blueprints. One Blueprint by model for instance :

```
app/ # Flask main application
    __init__.py
    customer/ # Customer Blueprint
        __init__.py
        forms.py # User forms
        models.py # User model
        views.py # User views
        templates/ # User templates
            ...
    product/ # Product Blueprint
        __init__.py
        forms.py
        models.py
        views.py
        templates/
            ...
    templates/ # Common templates
        layout.html
        macros.html
    config.py
    filters.py
    ...
```

That's great. But where do you put the logic ? "Yeah… It depends…". "Sometimes in the model, sometimes in the views…". You see what I mean, right ? Problem is, as the application grows, it became impossible to maintain, because you just doesn't know where the logic is done.

First, "model layer" is supposed to be only data storage manipulation. But putting the logic in the "view layer" really is bad idea. What if you want to add a REST API to you application ? You just copy paste all the code from your classic route to make the new API routes ?

Finally, if you want to replace SQL database by LDAP, you should be able to do it without modifying anything but the model. So you can't put any logic in "models.py". So, please, stop using SQLAlchemy methods in your views.

This package gives you a solution.

## Installation

    pip install flask-servicelayer

## Example

The package provides to main classes, one to build a Flask SQLAlchemy-based service, and one to build a LDAPom-model-based service.

### SQLAlchemyService

See how the route became clean when all the logic and the SQLAlchemy specifics code are put in a service layer.

`app/product/services.py` :

```python
from flask.ext.servicelayer import SQLAlchemyService

from .models import Product
from .. import db

class ProductService(SQLAlchemyService):
    __model__ = Product
    __db__ = db
```

`app/product/views.py`:

```python
products = ProductService()

@product.route("/")
def index():
    return render_template('product/list.html', products=products.all())

@product.route("/new", methods=['GET', 'POST'])
def new():
    form = ProductForm()
    if form.validate_on_submit():
        products.create(**{field.name: field.data for field in form})
        return redirect(url_for('.index'))
    return render_template('product/new.html', form=form)

@product.route("/delete/<int:id>")
def delete(id):
    products.delete(products.get_or_404(id))
    return redirect(url_for('.index'))
```

### LDAPOMService

And see how customer views are really looking like product views, even if the Customer model is based on [LDAPOM-model](https://github.com/sysnove/ldapom-model). Do you see any complex retrieve functions in the views?

`app/customer/services.py`:

```python
from flask.ext.servicelayer import LDAPOMService

from .. import ldap
from .models import Customer

class CustomerService(LDAPOMService):
    __model__ = Customer
    __ldap__ = ldap
```

`app/customer/views.py`:

```python
customers = CustomerService()

@customer.route("/")
def index():
    return render_template('customer/list.html', customers=customers.all())

@customer.show(/<id>)
def show(id):
    customer = customers.get_or_404(id)
    return render_template("customer/show.html", customer=customer)
```

## Tips

### Instantiation

Depending on how you have structure the rest of your application, you can instantiate a service object when you need it, or instantiate on object of each service at the beginning of each request, and store it in `g` to use it everywhere. Personally, I like to instantiate each service in the `before_request` method of its Blueprint. For instance, in `app/customer/__init__.py`:

```python
from flask import Blueprint, g

domain = Blueprint("customer", __name__, template_folder='templates')

from .services import CustomerService

@customer.before_app_request
def before_request():
    if 'ldap' in g:
        g.customers = CustomerService(g.ldap)

from . import views
```

### LDAP Cache

The package provides an `LDAPOMCachedService` class. This class inherits `LDAPOMService` and can be use exactly the same way. The only difference is that `all()`, `get()` and `find()` methods are cached within the service object to avoid doing a new LDAP request every time. This is very powerful when your service object is put in the global var `g` to be used everywhere during your request.

## Licence

This code is under [WTFPL](https://en.wikipedia.org/wiki/WTFPL). Just do what the fuck you want with it.

The idea is based on [Matt Wright's article How do I Structure My Flask Application](http://mattupstate.com/python/2013/06/26/how-i-structure-my-flask-applications.html#s2c). Matt, if you read this, thank you!
