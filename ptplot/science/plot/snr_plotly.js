// Shows the power spectrum and the parameters of the clicked point of an interactive SNR figure.
// This is run by Plotly after creating the figure, see ptplot.science.plot.snr.SNRFigure.plotly_html.
// Plotly replaces {plot_id} with the id of the figure,
// and PTPlot replaces __DATA__ with the data of the grid, see ptplot.science.plot.snr.SNRFigure.plotly_data.
// Plotly runs this inside a function, so the declarations are local to it,
// and several figures can be on the same page.
const gd = document.getElementById("{plot_id}");
const data = __DATA__;
const bytes = Uint8Array.from(atob(data.spectra), c => c.charCodeAt(0));
const spectra = new Float32Array(bytes.buffer);
const nF = data.f.length;
const iSpectrum = gd.data.findIndex(trace => trace.uid === "spectrum");
const iSelected = gd.data.findIndex(trace => trace.uid === "selected");
const iInfo = gd.layout.annotations.findIndex(annotation => annotation.name === "selected");

function nearest(values, value) {
    let best = 0;
    for (let i = 1; i < values.length; i++) {
        if (Math.abs(values[i] - value) < Math.abs(values[best] - value)) {
            best = i;
        }
    }
    return best;
}

// This corresponds to the "{:.3g}" format of Python, e.g. 0.000483 and 5.01e+03.
function format(value) {
    if (!Number.isFinite(value)) {
        return "NaN";
    }
    const exponent = value === 0 ? 0 : Math.floor(Math.log10(Math.abs(Number(value.toPrecision(3)))));
    if (exponent < -4 || exponent >= 3) {
        const [mantissa, exp] = value.toExponential(2).split("e");
        const sign = exp.startsWith("-") ? "-" : "+";
        return Number(mantissa).toString() + "e" + sign + exp.replace(/^[+-]/, "").padStart(2, "0");
    }
    return Number(value.toPrecision(3)).toString();
}

function info(iy, ix) {
    const lines = data.params.map(param => param.label + " = " + format(param.values[iy][ix]));
    lines.push("SNR = " + format(data.snr[iy][ix]));
    return lines.join("<br>");
}

function select(iy, ix) {
    const start = (iy * data.x.length + ix) * nF;
    const omega = Array.from(spectra.subarray(start, start + nF), v => (Number.isFinite(v) && v > 0) ? v : null);
    Plotly.restyle(gd, {y: [omega]}, [iSpectrum]);
    Plotly.restyle(gd, {x: [[data.x_log10[ix]]], y: [[data.y_log10[iy]]]}, [iSelected]);
    Plotly.relayout(gd, {[`annotations[${iInfo}].text`]: info(iy, ix)});
}

gd.on("plotly_click", event => {
    const point = event.points[0];
    if (point.xaxis._id !== "x") {
        return;
    }
    select(nearest(data.y_log10, point.y), nearest(data.x_log10, point.x));
});
