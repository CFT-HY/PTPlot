from django.urls import path, re_path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    # CSV

    path(r'curvedata.csv',
         views.csv,
         name='csv'),


    # Plots

    # SNR plot with alpha on the x-axis and beta on the y-axis
    path(r'snr_alphabeta.svg',
         views.snr_alphabeta_image,
         name='snr_alphabeta'),
    # SNR plot with UbarF on the x-axis and H_n R_* on the y-axis
    path(r'snr.svg',
         views.snr_image,
         name='snr'),
    # Power spectrum plot with sensitivity curve superimposed
    path(r'ps.svg',
         views.ps_image,
         name='ps'),

    # Single point page
    
    # Plot a single case - both query form and results
    path(r'single',
         views.single,
         name='single'),

    # Multiple point pages

    # Plot many points - manual input
    path(r'multiple',
         views.multiple,
         name='multiple'),

    path(r'multiple.svg',
         views.multiple,
         name='multiple'),

    
    # Display a list of models from database
    path(r'models',
         views.model,
         name='model'),

    # Old name for models
    re_path(r'theories*', RedirectView.as_view(url='/ptplot/models', permanent=True)),
    
    # Display a list of benchmark points for a model
    path(r'models/<int:model_id>',
         views.model_detail,
         name='model_detail'),

    # Display the benchmark points for a model on the SNR plots
    path(r'models/<int:model_id>/plot',
         views.model_detail_plot,
         name='model_detail_plot'),
    
    
    # Display an individual model point on the SNR and PS plots
    path(r'models/<int:model_id>/<int:point_id>/plot',
         views.model_point_plot,
         name='model_point_plot'),

    # Display an individual model point on the SNR and PS plots
    path(r'models/<int:model_id>/<int:point_id>/snr.svg',
         views.model_point_snr,
         name='model_point_snr'),

    # Display an individual model point on the SNR and PS plots
    path(r'models/<int:model_id>/<int:point_id>/snr_alphabeta.svg',
         views.model_point_snr_alphabeta,
         name='model_point_snr_alphabeta'),

    # Display an individual model point on the SNR and PS plots
    path(r'models/<int:model_id>/<int:point_id>/ps.svg',
         views.model_point_ps,
         name='model_point_ps'),

    # Download CSV data for an individual model point
    path(r'models/<int:model_id>/<int:point_id>/curvedata.csv',
         views.model_point_csv,
         name='model_point_csv'),

    
    # Display a group of scenario points on the SNR plots
    path(r'models/<int:model_id>/scenarios/<int:scenario_id>/plot',
         views.model_scenario_plot,
         name='model_scenario_plot'),

    # Display a group of scenario points on the SNR plots
    path(r'models/<int:model_id>/scenarios/<int:scenario_id>/snr.svg',
         views.model_scenario_snr,
         name='model_scenario_snr'),

    # Display a group of scenario points on the SNR plots
    path(r'models/<int:model_id>/scenarios/<int:scenario_id>/snr_alphabeta.svg',
         views.model_scenario_snr_alphabeta,
         name='model_scenario_snr_alphabeta'),


    
    
    
    
    path(r'models/<int:model_id>/snr.svg',
         views.model_snr,
         name='model_snr'),
    
    path(r'models/<int:model_id>/snr_alphabeta.svg',
         views.model_snr_alphabeta,
         name='model_snr_alphabeta'),

    path(r'parameterchoice',
         views.parameterchoice_form,
         name='parameterchoice'),

    
    # Finally, the main page
    path(r'', views.index, name='index'),
]


