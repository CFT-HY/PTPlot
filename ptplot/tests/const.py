"""Constants for the tests."""

from ptplot.science import const
from ptplot.science.spectrum.ssm import SSMSettings

#: Size of the axes of the SNR grids in the tests that don't depend on it.
#: This is smaller than :py:data:`ptplot.science.const.DEFAULT_GRID_SIZE` to speed up the tests.
TEST_GRID_SIZE: int = 5
assert TEST_GRID_SIZE < const.DEFAULT_GRID_SIZE

#: Low accuracy settings of the SSM for the tests whose results are not compared with reference values.
#: A spectrum is computed about ten times faster than with the default settings.
TEST_SSM_SETTINGS: SSMSettings = SSMSettings(n_z_lookup=1000, n_t=1000, nx_p_tilde_gw=200)

#: Query parameters for the SNR grid views with :py:data:`TEST_GRID_SIZE`, see :py:class:`ptplot.forms.GridAxesForm`
GRID_AXES_DATA: dict[str, int] = {"grid_size": TEST_GRID_SIZE}
#: Query parameters for :py:data:`TEST_SSM_SETTINGS`, see :py:class:`ptplot.forms.SSMSettingsForm`
SSM_SETTINGS_DATA: dict[str, int] = {
    name: value for name, value in (
        ("n_z_lookup", TEST_SSM_SETTINGS.n_z_lookup),
        ("n_t", TEST_SSM_SETTINGS.n_t),
        ("nx_p_tilde_gw", TEST_SSM_SETTINGS.nx_p_tilde_gw),
    ) if value is not None
}
#: Query parameters for the fast computation of the views whose results are not compared with reference values
FAST_DATA: dict[str, int] = {**GRID_AXES_DATA, **SSM_SETTINGS_DATA}
