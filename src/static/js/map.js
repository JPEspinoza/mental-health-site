// start slider
var year_slider = document.getElementById('year');
noUiSlider.create(year_slider, {
    start: [year_min, year_max],
    connect: true,
    step: 1,
    range: {
        'min': year_min,
        'max': year_max
    },
    pips: {
        mode: 'steps',
        density: 10
    }, 
});

// get submit button
var submit = document.getElementById('submit');

// enable submit when report and region are selected
var report_select = document.getElementById('report');
var region_select = document.getElementById('region');

report_select.addEventListener("change", function() {
    if (report_select.value != "null" && region_select.value != "null") {
        submit.disabled = false;
    } else {
        submit.disabled = true;
    }
});

region_select.addEventListener("change", function() {
    if (report_select.value != "null" && region_select.value != "null") {
        submit.disabled = false;
    } else {
        submit.disabled = true;
    }
});

// request map when submit button is clicked
submit.addEventListener('click', function() {
    // get the values of the inputs
    let report = report_select.value;
    let region = document.getElementById("region").value;
    let year = year_slider.noUiSlider.get(true);
    let year_low = year[0]
    let year_high = year[1]

    submit.disabled = true

    // make a request to the backend
    fetch(`/map/report=${report}/region=${region}/year_low=${year_low}/year_high=${year_high}/`)
    .then(response => response.text())
    .then(data => {
        let map = document.getElementById('map');
        map.innerHTML = data;
        submit.disabled = false;
    });
});