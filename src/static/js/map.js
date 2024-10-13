// start slider
const year_slider = document.getElementById('year');
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

// map spinner
const map_spinner = document.createElement('div');
map_spinner.classList.add('h-100', 'w-100', 'd-flex', 'justify-content-center', 'align-items-center');
const map_spinner_inner = document.createElement('div')
map_spinner_inner.classList.add('spinner-grow');
map_spinner_inner.style.width = "10rem";
map_spinner_inner.style.height = "10rem";
map_spinner.appendChild(map_spinner_inner);

// submit spinner
const submit_spinner = document.getElementById('submit_spinner');

// get all document elements
const submit = document.getElementById('submit');
const report_select = document.getElementById('report');
const region_select = document.getElementById('region');
const map = document.getElementById('map');

// enable submit when both selects have a value
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
    let region = region_select.value;
    let year = year_slider.noUiSlider.get(true);
    let year_low = year[0];
    let year_high = year[1];

    // show spinner
    submit_spinner.classList.remove("d-none");

    // disable submit button while we load
    submit.disabled = true;

    // show spinner
    map.innerHTML = "";
    map.appendChild(map_spinner);

    // make a request to the backend
    fetch(`/map/report=${report}/region=${region}/year_low=${year_low}/year_high=${year_high}/`)
    .then(response => response.text())
    .then(data => {
        // show map
        map.innerHTML = data;

        // enable submit button
        submit.disabled = false;

        // hide spinner
        submit_spinner.classList.add("d-none");
    });
});