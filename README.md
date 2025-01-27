PTPlot
======

PTPlot is a plotting tool for visualising the gravitational wave power
spectrum from first-order phase transitions.

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

5. Finally, run `python manage.py runserver --nothreading` and visit http://127.0.0.1:8000/ptplot/ to test the thing.

Benchmark points
----------------

These are created in the database by running `python manage.py
populate` which calls `ptplot/management/commands/populate.py`. Edit
that file to add benchmark points.

Threading issues when running locally
-------------------------------------
Since commit `5f861e5` we have removed all threading from the PTPlot code.
When deploying the production server we use gunicorn to serve requests using the default 'sync' worker
type (https://docs.gunicorn.org/en/latest/design.html#sync-workers) (see below for more details about deploying).
This helps to prevent issues with non-thread-safe code. When running locally using the `manage.py runserver`
command (see https://docs.djangoproject.com/en/4.2/ref/django-admin/) we recommend adding the argument
`--nothreading` to avoid the use of threads. Errors when using threading seem mostly to originate in matplotlib's
mathtext library (https://matplotlib.org/stable/tutorials/text/mathtext.html), so an alternative workaround would be
to change how text is rendered in plots.

Deploying
---------

For best performance, run using gunicorn behind a buffering proxy (e.g. nginx). Ensure that gunicorn has enough worker threads to handle separate plotting computations for 2-3 plots per page.

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
