PTPlot
======

PTPlot is a plotting tool for visualising the gravitational wave power
spectrum from first-order phase transitions.

Prerequisites
-------------

- django
- dulwich [pure python git implementation]
- matplotlib
- scipy

Getting started
---------------

1. Set up "ptplot" as a django project by running:

        django-admin startproject ptplot_site

    This will create a new folder called `ptplot_site`. It is useful
	to create a symbolic link to your main ptplot folder (i.e. `ptplot/`
	within this repo) here:

        ln -s <path to this repo>/ptplot ptplot_site/ptplot

    Alternatively, update the path in step 3.

2. Add "ptplot" to your INSTALLED_APPS (in `ptplot_site/ptplot_site/settings.py`) like this:

        INSTALLED_APPS = [
            ...
            'ptplot',
        ]

3. Include the ptplot URLconf in your project urls.py (i.e. `ptplot_site/ptplot_site/urls.py`) like this:

        path('ptplot/', include('ptplot.urls')),

    You will first need to import the include function:

        from django.conf.urls import include

4. Run `python manage.py makemigrations ptplot` and `python manage.py migrate`.

5. Finally, run `python manage.py runserver` and visit http://127.0.0.1:8000/ptplot/ to test the thing.

Benchmark points
----------------

These are created in the database by running `python manage.py
populate` which calls `ptplot/management/commands/populate.py`. Edit
that file to add benchmark points.

Elastic Beanstalk
-----------------

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
