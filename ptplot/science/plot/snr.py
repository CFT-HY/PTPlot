"""SNR figures of the SNR grids.

The figures can be created with Matplotlib as static images, see :py:meth:`SNRFigure.matplotlib`,
or with Plotly as interactive figures, see :py:meth:`SNRFigure.plotly` and :py:meth:`SNRFigure.plotly_html`.
In the interactive figures, clicking on the SNR plot shows the power spectrum at that point of the grid.
"""

import base64
import json
import typing as tp

from matplotlib import cm, rc_context
from matplotlib.colors import LogNorm, to_hex
from matplotlib.figure import Figure
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ptplot.science import const
from ptplot.science.plot.lock import matplotlib_lock
from ptplot.science.plot.logarithmic import add_points, log_figure, nested_labels
from ptplot.science.plot.utils import add_text, find_label_place, has_lines, latex_to_html, watermark
from ptplot.science.snr.grid import SNRGrid
import ptplot.science.type_hints as th
from ptplot.science.utils import atleast_2d

COLOR_TUPLE: th.FloatArr2D = cm.plasma_r(np.linspace(0.1, 1, 6))
LEVELS: th.FloatArr1D = np.array([1, 5, 10, 20, 50, 100])
LEVELS_TSH: th.FloatArr1D = np.array([0.001, 0.01, 0.1, 1, 10, 100])
LEVELS_TSH_HUGE_ALPHA: th.FloatArr1D = np.array([1e-7, 1e-6, 1e-5, 1e-4])
#: Default number of frequencies of the power spectra in the interactive figures.
#: The spectra are subsampled from the frequencies of the noise curve to reduce the size of the figures.
PLOTLY_N_F: int = 100
#: Range of $\mathcal{H}_* \eta_\text{sh}$ of the shaded region, where turbulence may be significant
TURBULENCE_RANGE: tuple[float, float] = (1e-4, 1)
#: JavaScript that shows the power spectrum at the clicked point of the SNR plot.
#: ``{plot_id}`` is replaced by Plotly with the id of the figure, and ``__DATA__`` with the data of the grid,
#: see :py:meth:`SNRFigure.plotly_data`.
PLOTLY_SCRIPT: str = """
(function () {
    const gd = document.getElementById("{plot_id}");
    const data = __DATA__;
    const bytes = Uint8Array.from(atob(data.spectra), c => c.charCodeAt(0));
    const spectra = new Float32Array(bytes.buffer);
    const nF = data.f.length;
    const iSpectrum = gd.data.findIndex(trace => trace.uid === "spectrum");
    const iSelected = gd.data.findIndex(trace => trace.uid === "selected");

    function nearest(values, value) {
        let best = 0;
        for (let i = 1; i < values.length; i++) {
            if (Math.abs(values[i] - value) < Math.abs(values[best] - value)) {
                best = i;
            }
        }
        return best;
    }

    function format(value) {
        return Number.isFinite(value) ? value.toPrecision(3) : "NaN";
    }

    function select(iy, ix) {
        const start = (iy * data.x.length + ix) * nF;
        const omega = Array.from(spectra.subarray(start, start + nF), v => (Number.isFinite(v) && v > 0) ? v : null);
        const name = data.x_label + " = " + format(data.x[ix]) + ", " + data.y_label + " = " + format(data.y[iy])
            + ", SNR = " + format(data.snr[iy][ix]);
        Plotly.restyle(gd, {y: [omega], name: [name]}, [iSpectrum]);
        Plotly.restyle(gd, {x: [[data.x_log10[ix]]], y: [[data.y_log10[iy]]]}, [iSelected]);
    }

    gd.on("plotly_click", event => {
        const point = event.points[0];
        if (point.xaxis._id !== "x") {
            return;
        }
        select(nearest(data.y_log10, point.y), nearest(data.x_log10, point.x));
    });
})();
"""


class SNRFigure:
    r"""SNR figure of an SNR grid.

    The SNR is shown as contours, together with the contours of $\mathcal{H}_* \eta_\text{sh}$
    and the points of the grid, if any.
    The axes are logarithmic, but the contours are drawn on linear axes of the base-10 logarithms of the values,
    so that the contour plots are created correctly.
    """

    #: The base-10 logarithm of the $y$ value at which the SNR contour labels are placed
    LABEL_WANTED_Y: tp.ClassVar[float] = 0.

    def __init__(
            self,
            grid: SNRGrid,
            labels: th.StrOrListOrNestedList | None = None,
            titles: th.StrOrList | None = None,
            huge_alpha: bool = False,
            filled: bool = False,
            snr_label_locs: list[tuple[float, float]] | None = None,
            shock_label_locs: list[tuple[float, float]] | None = None,
            levels: th.FloatArr1D = LEVELS,
            levels_tsh: th.FloatArr1D = LEVELS_TSH,
            levels_tsh_huge_alpha: th.FloatArr1D = LEVELS_TSH_HUGE_ALPHA,
            xtickpos: th.IntArr1D | None = None,
            ytickpos: th.IntArr1D | None = None,
            xticklabels: list[str] | None = None,
            yticklabels: list[str] | None = None,
            label_fontsize: int = const.DEFAULT_LABEL_FONTSIZE,
            contour_label_fontsize: int = 8):
        r"""Set up the SNR figure. The figures are created by :py:meth:`matplotlib` and :py:meth:`plotly`.

        :param grid: Precomputed SNR grid
        :param labels: Labels for the points [scenario, point], defaults to those of the grid
        :param titles: Titles for the scenarios, defaults to those of the grid
        :param huge_alpha: Whether $\alpha$ is very large.
            If so, the contours of :py:attr:`levels_tsh_huge_alpha` are also drawn.
        :param filled: Whether to fill the SNR contour plot
        :param snr_label_locs: Locations of the SNR contour labels in the Matplotlib figure,
            in the base-10 logarithms of the axis values
        :param shock_label_locs: Locations of the $\mathcal{H}_* \eta_\text{sh}$ contour labels
            in the Matplotlib figure, in the base-10 logarithms of the axis values
        :param levels: SNR values of the contours
        :param levels_tsh: $\mathcal{H}_* \eta_\text{sh}$ values of the contours
        :param levels_tsh_huge_alpha: $\mathcal{H}_* \eta_\text{sh}$ values of the additional contours
            for a huge $\alpha$
        :param xtickpos: Positions of the x-axis ticks in the Matplotlib figure
        :param ytickpos: Positions of the y-axis ticks in the Matplotlib figure
        :param xticklabels: Labels of the x-axis ticks in the Matplotlib figure
        :param yticklabels: Labels of the y-axis ticks in the Matplotlib figure
        :param label_fontsize: Font size of the axis labels in the Matplotlib figure
        :param contour_label_fontsize: Font size of the contour labels
        """
        self.grid: SNRGrid = grid
        self.labels: th.StrOrListOrNestedList | None = grid.labels_points if labels is None else labels
        self.titles: th.StrOrList | None = grid.titles if titles is None else titles
        self.huge_alpha: bool = huge_alpha
        self.filled: bool = filled
        self.levels: th.FloatArr1D = levels
        self.levels_tsh: th.FloatArr1D = levels_tsh
        self.levels_tsh_huge_alpha: th.FloatArr1D = levels_tsh_huge_alpha
        self.xtickpos: th.IntArr1D | None = xtickpos
        self.ytickpos: th.IntArr1D | None = ytickpos
        self.xticklabels: list[str] | None = xticklabels
        self.yticklabels: list[str] | None = yticklabels
        self.label_fontsize: int = label_fontsize
        self.contour_label_fontsize: int = contour_label_fontsize

        #: Base-10 logarithms of the x values of the grid
        self.x_log10: th.FloatArr1D = np.log10(grid.x)
        #: Base-10 logarithms of the y values of the grid
        self.y_log10: th.FloatArr1D = np.log10(grid.y)
        self.snr_label_locs: list[tuple[float, float]] = [
            find_label_place(
                x=self.x_log10, y=self.y_log10,
                snr=grid.snr, wanted_y=self.LABEL_WANTED_Y, wanted_contour=wanted_contour
            )
            for wanted_contour in levels
        ] if snr_label_locs is None else snr_label_locs
        self.shock_label_locs: list[tuple[float, float]] = \
            self.default_shock_label_locs() if shock_label_locs is None else shock_label_locs

    @property
    def levels_tsh_all(self) -> th.FloatArr1D:
        r"""All the $\mathcal{H}_* \eta_\text{sh}$ values of the contours."""
        if self.huge_alpha:
            return np.concatenate((self.levels_tsh_huge_alpha, self.levels_tsh))
        return self.levels_tsh

    def default_shock_label_locs(self) -> list[tuple[float, float]]:
        r"""Locations of the $\mathcal{H}_* \eta_\text{sh}$ contour labels in the Matplotlib figure.

        :return: A label at the middle of the x-axis for each integer power of ten on the y-axis
        """
        x_mid = (self.x_log10[0] + self.x_log10[-1]) / 2
        return [(x_mid, float(y)) for y in self.y_decades()]

    def y_decades(self) -> range:
        """The integer powers of ten within the range of the y-axis, as for the labels of the shock time contours."""
        return range(int(self.y_log10[0]), int(self.y_log10[-1]) + 1)

    @matplotlib_lock
    def matplotlib(self) -> Figure:
        """Create the SNR figure with Matplotlib.

        :return: Matplotlib figure
        """
        grid = self.grid
        x_log10 = self.x_log10
        y_log10 = self.y_log10
        with rc_context(const.DEFAULT_RC_CONTEXT):
            fig, ax, extent = log_figure(
                x=x_log10, y=y_log10,
                xlabel=grid.X_LABEL, ylabel=grid.Y_LABEL,
                xtickpos=self.xtickpos, ytickpos=self.ytickpos,
                xticklabels=self.xticklabels, yticklabels=self.yticklabels,
                label_fontsize=self.label_fontsize
            )

            if self.filled:
                contour = ax.contourf(x_log10, y_log10, grid.snr, extent=extent, norm=LogNorm())
                fig.colorbar(
                    contour,
                    ax=ax,
                    label=rf"$\text{{SNR}}_{{{grid.engine}}}$"
                )
            else:
                contour = ax.contour(
                    x_log10, y_log10, grid.snr, self.levels,
                    linewidths=1, colors=COLOR_TUPLE, extent=extent
                )

            contour_shock = ax.contour(
                x_log10, y_log10, grid.shock_times, self.levels_tsh,
                linewidths=1, linestyles="dashed", colors="k", extent=extent
            )

            if self.huge_alpha:
                ax.contour(
                    x_log10, y_log10, grid.shock_times, self.levels_tsh_huge_alpha,
                    linewidths=1, linestyles="dashed", colors="k", extent=extent
                )

            # Greying out the area according to turbulence
            # TODO: Explain this better
            if not self.filled:
                contour_shock_hatch = ax.contourf(  # noqa: F841
                    x_log10, y_log10, grid.shock_times, TURBULENCE_RANGE,
                    colors="white",
                    alpha=0.2, hatches="x", extent=extent
                )
                # contour_shock_hatch.set_edgecolor((0.3, 0.3, 0.3, 1))

            # Placing the labels manually fails if there are no contour lines, e.g. for a coarse grid.
            if not self.filled and has_lines(contour):
                ax.clabel(
                    contour, inline=1, fontsize=self.contour_label_fontsize, fmt="%.0f", manual=self.snr_label_locs
                )
            if has_lines(contour_shock):
                ax.clabel(
                    contour_shock, inline=1, fontsize=self.contour_label_fontsize, fmt="%g",
                    manual=self.shock_label_locs
                )
            # ax.set_title(r"SNR (solid), $\tau_{\rm sh} H_{\rm n}$ (dashed) from Acoustic GWs")
            # ax.set_xlabel(r"$\log_{10}(H_{\rm n} R_*) / (T_{\rm n}/100\, {\rm Gev}) $",fontsize=16)

            # July 2023: No longer watermark with LISACosWG
            # # position bottom right
            # fig.text(
            #     0.95, 0.05, "LISACosWG",
            #     fontsize=50, color="gray",
            #     ha="right", va="bottom", alpha=0.4
            # )

            if grid.has_points:
                x_points, y_points = grid.points()
                add_points(ax=ax, x=x_points, y=y_points, labels=self.labels, titles=self.titles)

            add_text(ax, watermark())
            return fig

    def f_indices(self, n_f: int = PLOTLY_N_F) -> th.IntArr1D:
        """Indices of the frequencies of the noise curve to which the spectra are subsampled in the Plotly figures.

        The frequencies of the noise curve are logarithmically spaced,
        and therefore the subsampled frequencies are as well.

        :param n_f: Maximum number of frequencies
        :return: Indices of the frequencies
        """
        n_f_grid = self.grid.f.size
        return np.unique(np.linspace(0, n_f_grid - 1, min(n_f, n_f_grid)).round().astype(np.int64))

    def initial_indices(self) -> tuple[int, int]:
        """Indices [y, x] of the grid point whose spectrum is shown when the Plotly figure is loaded.

        :return: The grid point nearest to the first point drawn on the grid, or the middle of the grid
        """
        if self.grid.has_points:
            x_points, y_points = atleast_2d(*self.grid.points())
            return (
                int(np.abs(self.y_log10 - np.log10(y_points[0][0])).argmin()),
                int(np.abs(self.x_log10 - np.log10(x_points[0][0])).argmin())
            )
        return self.y_log10.size // 2, self.x_log10.size // 2

    def plotly(self, n_f: int = PLOTLY_N_F) -> go.Figure:
        """Create the SNR figure with Plotly.

        The SNR plot is on the left, and the power spectrum of a point of the grid on the right.
        To show the spectrum of the clicked point, the figure has to be exported with :py:meth:`plotly_html`,
        which adds the spectra of the grid and the JavaScript that handles the clicks.
        Otherwise, the spectrum of :py:meth:`initial_indices` is shown.

        :param n_f: Maximum number of frequencies of the spectra, see :py:meth:`f_indices`
        :return: Plotly figure
        """
        grid = self.grid
        x_log10 = self.x_log10
        y_log10 = self.y_log10
        fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.15)
        contour_kwargs: dict[str, tp.Any] = {
            "x": x_log10,
            "y": y_log10,
            "showscale": False,
            "showlegend": False,
            "hoverinfo": "skip",
        }

        # An invisible heatmap, which shows the SNR values when hovering, and catches the clicks.
        x_grid, y_grid = np.meshgrid(grid.x, grid.y)
        fig.add_trace(go.Heatmap(
            x=x_log10, y=y_log10, z=grid.snr,
            customdata=np.stack((x_grid, y_grid), axis=-1),
            opacity=0,
            showscale=False,
            hovertemplate=(
                f"{grid.X_LABEL_HTML} = %{{customdata[0]:.3g}}<br>"
                f"{grid.Y_LABEL_HTML} = %{{customdata[1]:.3g}}<br>"
                "SNR = %{z:.3g}<extra></extra>"
            ),
            name="SNR"
        ), row=1, col=1)

        if self.filled:
            with np.errstate(divide="ignore", invalid="ignore"):
                snr_log10 = np.log10(np.where(grid.snr > 0, grid.snr, np.nan))
            decades = np.arange(np.floor(np.nanmin(snr_log10)), np.ceil(np.nanmax(snr_log10)) + 1) \
                if np.isfinite(snr_log10).any() else np.array([])
            fig.add_trace(go.Contour(
                z=snr_log10,
                colorscale="Viridis",
                contours={"coloring": "fill", "showlines": False},
                ncontours=10,
                colorbar={
                    "title": {"text": f"SNR<sub>{grid.engine}</sub>"},
                    "tickvals": decades,
                    "ticktext": [f"10<sup>{decade:.0f}</sup>" for decade in decades],
                    "x": 0.43,
                    "xanchor": "left",
                    "thickness": 15,
                },
                **(contour_kwargs | {"showscale": True})
            ), row=1, col=1)
        else:
            fig.add_trace(go.Contour(
                z=grid.shock_times,
                contours={"type": "constraint", "operation": "[]", "value": list(TURBULENCE_RANGE)},
                fillcolor="rgba(128, 128, 128, 0.2)",
                line={"width": 0},
                **contour_kwargs
            ), row=1, col=1)
            for i, level in enumerate(self.levels):
                fig.add_trace(go.Contour(
                    z=grid.snr,
                    contours=self._single_contour(level, labelformat=".0f"),
                    line={"color": to_hex(COLOR_TUPLE[i % len(COLOR_TUPLE)]), "width": 1.5},
                    **contour_kwargs
                ), row=1, col=1)

        for level in self.levels_tsh_all:
            fig.add_trace(go.Contour(
                z=grid.shock_times,
                contours=self._single_contour(level, labelformat=".3~g"),
                line={"color": "black", "width": 1, "dash": "dash"},
                **contour_kwargs
            ), row=1, col=1)

        if grid.has_points:
            self._plotly_points(fig)

        f_indices = self.f_indices(n_f)
        f = grid.f[f_indices]
        iy, ix = self.initial_indices()
        fig.add_trace(go.Scatter(
            x=[x_log10[ix]], y=[y_log10[iy]],
            mode="markers",
            marker={"symbol": "x-thin", "size": 12, "line": {"width": 2, "color": "black"}},
            hoverinfo="skip",
            showlegend=False,
            uid="selected"
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=f, y=grid.noise.noise[f_indices],
            mode="lines",
            line={"color": "gray", "dash": "dot"},
            name="Noise",
            legend="legend2"
        ), row=1, col=2)
        spectrum = grid.spectra[iy, ix, f_indices]
        fig.add_trace(go.Scatter(
            x=f, y=np.where(spectrum > 0, spectrum, np.nan),
            mode="lines",
            line={"color": "black"},
            name=self._spectrum_name(iy, ix),
            legend="legend2",
            uid="spectrum"
        ), row=1, col=2)

        fig.update_xaxes(
            title_text=grid.X_LABEL_HTML, range=[x_log10[0], x_log10[-1]], **self._decade_ticks(x_log10),
            row=1, col=1
        )
        fig.update_yaxes(
            title_text=grid.Y_LABEL_HTML, range=[y_log10[0], y_log10[-1]], **self._decade_ticks(y_log10),
            row=1, col=1
        )
        fig.update_xaxes(title_text="f (Hz)", type="log", exponentformat="power", row=1, col=2)
        fig.update_yaxes(title_text="h<sup>2</sup> Ω<sub>GW</sub>(f)", type="log", exponentformat="power", row=1, col=2)
        fig.update_layout(
            height=600,
            template="simple_white",
            legend={"x": 0.01, "y": 0.01, "xanchor": "left", "yanchor": "bottom", "bgcolor": "rgba(255,255,255,0.9)"},
            legend2={"x": 1, "y": 1, "xanchor": "right", "yanchor": "bottom"},
            hovermode="closest",
            margin={"t": 80},
        )
        fig.add_annotation(
            text=watermark(),
            xref="x domain", yref="y domain", x=0, y=1, xanchor="left", yanchor="bottom",
            showarrow=False, font={"size": 10, "color": "gray"}
        )
        return fig

    def plotly_data(self, n_f: int = PLOTLY_N_F) -> dict[str, tp.Any]:
        """The data of the grid that is embedded in the HTML of the Plotly figure, see :py:meth:`plotly_html`.

        The spectra are encoded as base64 of little-endian 32-bit floats in the [y, x, f] order,
        as this is significantly more compact than JSON.

        :param n_f: Maximum number of frequencies of the spectra, see :py:meth:`f_indices`
        :return: Data that can be converted to JSON
        """
        grid = self.grid
        f_indices = self.f_indices(n_f)
        spectra = np.ascontiguousarray(grid.spectra[:, :, f_indices], dtype="<f4")
        return {
            "x": grid.x.tolist(),
            "y": grid.y.tolist(),
            "x_log10": self.x_log10.tolist(),
            "y_log10": self.y_log10.tolist(),
            "x_label": grid.X_LABEL_HTML,
            "y_label": grid.Y_LABEL_HTML,
            "f": grid.f[f_indices].tolist(),
            # JSON does not support NaN, so the invalid values are converted to null.
            "snr": [[float(value) if np.isfinite(value) else None for value in row] for row in grid.snr],
            "spectra": base64.b64encode(spectra.tobytes()).decode("ascii"),
        }

    def plotly_html(
            self,
            n_f: int = PLOTLY_N_F,
            full_html: bool = True,
            include_plotlyjs: bool | str = "cdn",
            **kwargs: tp.Any) -> str:
        """Create the interactive SNR figure as HTML.

        The spectra of the grid are embedded in the HTML together with the figure,
        so that the spectrum of the clicked point can be shown without further requests to the server.

        :param n_f: Maximum number of frequencies of the spectra, see :py:meth:`f_indices`
        :param full_html: Whether to create a full HTML document instead of a ``<div>`` element
        :param include_plotlyjs: How to include the Plotly JavaScript library,
            see :py:func:`plotly.io.to_html`
        :param kwargs: Additional arguments for :py:func:`plotly.io.to_html`
        :return: HTML of the figure
        """
        # Escaping "</" ensures that the data cannot end the <script> element.
        data = json.dumps(self.plotly_data(n_f)).replace("</", "<\\/")
        return self.plotly(n_f).to_html(
            full_html=full_html,
            include_plotlyjs=include_plotlyjs,
            post_script=PLOTLY_SCRIPT.replace("__DATA__", data),
            **kwargs
        )

    def _plotly_points(self, fig: go.Figure) -> None:
        """Add the points of the grid to the SNR plot of a Plotly figure."""
        x_points, y_points = atleast_2d(*self.grid.points())
        labels = nested_labels(self.labels)
        titles = [self.titles] if isinstance(self.titles, str) else self.titles
        for i, (x_set, y_set) in enumerate(zip(x_points, y_points, strict=True)):
            fig.add_trace(go.Scatter(
                x=np.log10(x_set), y=np.log10(y_set),
                mode="markers+text" if labels else "markers",
                text=[latex_to_html(label) for label in labels[i]] if labels else None,
                textposition="middle right",
                name=latex_to_html(titles[i]) if titles and i < len(titles) else None,
                showlegend=bool(titles) and i < len(titles),
                hoverinfo="skip"
            ), row=1, col=1)

    def _spectrum_name(self, iy: int, ix: int) -> str:
        """Legend entry of the spectrum of a grid point, as created also by :py:data:`PLOTLY_SCRIPT`."""
        grid = self.grid
        return (
            f"{grid.X_LABEL_HTML} = {grid.x[ix]:.3g}, {grid.Y_LABEL_HTML} = {grid.y[iy]:.3g}, "
            f"SNR = {grid.snr[iy, ix]:.3g}"
        )

    @staticmethod
    def _decade_ticks(values_log10: th.FloatArr1D) -> dict[str, tp.Any]:
        """Ticks of a Plotly axis of base-10 logarithms at the integer powers of ten."""
        decades = np.arange(np.ceil(values_log10.min()), np.floor(values_log10.max()) + 1)
        return {
            "tickvals": decades,
            "ticktext": [f"10<sup>{decade:.0f}</sup>" for decade in decades],
        }

    def _single_contour(self, level: float, labelformat: str) -> dict[str, tp.Any]:
        """Contours of a Plotly contour trace that consist of a single labelled level."""
        return {
            "start": level,
            "end": level,
            "size": 1,
            "coloring": "none",
            "showlabels": True,
            "labelformat": labelformat,
            "labelfont": {"size": self.contour_label_fontsize + 2},
        }
