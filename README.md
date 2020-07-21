PTPlot
======

PTPlot is a plotting tool for visualising the gravitational wave power
spectrum from first-order phase transitions.

Prerequisites
-------------

- matplotlib
- texlive
- scipy

If deploying to Elastic Beanstalk, use the following in
.ebextensions/django.config:

    packages:
      yum:
        texlive: []
        texlive-dvipng-bin: []

    option_settings:
      aws:elasticbeanstalk:container:python:
        WSGIPath: ebdjango/wsgi.py
      aws:elasticbeanstalk:container:python:staticfiles:
        /static/: "ptplot/static/"
	 
  
Quick start
-----------

1. Add "ptplot" to your INSTALLED_APPS setting like this:

       INSTALLED_APPS = [
           ...
           'ptplot',
       ]

2. Include the ptplot URLconf in your project urls.py like this::

       path('ptplot/', include('ptplot.urls')),

3. Run `python manage.py migrate`.

4. Visit http://127.0.0.1:8000/ptplot/ to test the thing.

Benchmark points
----------------

These are created in the database by running `python manage.py
populate` which calls `ptplot/management/commands/populate.py`. Edit
that file to add benchmark points.

