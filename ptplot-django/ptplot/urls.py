
from django.urls import path

from . import views

urlpatterns = [
    # Plots

    # SNR plot with alpha on the x-axis and beta on the y-axis
    path(r'snr_alphabeta',
         views.snr_alphabeta_image,
         name='snr_alphabeta'),
    # SNR plot with UbarF on the x-axis and H_n R_* on the y-axis
    path(r'snr',
         views.snr_image,
         name='snr'),
    # Power spectrum plot with sensitivity curve superimposed
    path(r'ps',
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

    
    # Display a list of theories from database
    path(r'theories',
         views.theory,
         name='theory'),

    # Display a list of benchmark points for a theory
    path(r'theories/<int:theory_id>',
         views.theory_detail,
         name='theory_detail'),

    # Display the benchmark points for a theory on the SNR plots
    path(r'theories/<int:theory_id>/plot',
         views.theory_detail_plot,
         name='theory_detail_plot'),
    
    
    # Display an individual theory point on the SNR and PS plots
    path(r'theories/<int:theory_id>/<int:point_id>/plot',
         views.theory_point_plot,
         name='theory_point_plot'),

    # Display an individual theory point on the SNR and PS plots
    path(r'theories/<int:theory_id>/<int:point_id>/snr',
         views.theory_point_snr,
         name='theory_point_snr'),

    # Display an individual theory point on the SNR and PS plots
    path(r'theories/<int:theory_id>/<int:point_id>/snr_alphabeta',
         views.theory_point_snr_alphabeta,
         name='theory_point_snr_alphabeta'),

    # Display an individual theory point on the SNR and PS plots
    path(r'theories/<int:theory_id>/<int:point_id>/ps',
         views.theory_point_ps,
         name='theory_point_ps'),

    # Display a group of scenario points on the SNR plots
    path(r'theories/<int:theory_id>/scenarios/<int:scenario_id>/plot',
         views.theory_scenario_plot,
         name='theory_scenario_plot'),

    # Display a group of scenario points on the SNR plots
    path(r'theories/<int:theory_id>/scenarios/<int:scenario_id>/snr',
         views.theory_scenario_snr,
         name='theory_scenario_snr'),

    # Display a group of scenario points on the SNR plots
    path(r'theories/<int:theory_id>/scenarios/<int:scenario_id>/snr_alphabeta',
         views.theory_scenario_snr_alphabeta,
         name='theory_scenario_snr_alphabeta'),


    
    
    
    
    path(r'theories/<int:theory_id>/snr',
         views.theory_snr,
         name='theory_snr'),
    
    path(r'theories/<int:theory_id>/snr_alphabeta',
         views.theory_snr_alphabeta,
         name='theory_snr_alphabeta'),

    path(r'parameterchoice',
         views.parameterchoice_form,
         name='parameterchoice'),

    
    # Finally, the main page
    path(r'', views.index, name='index'),
]


