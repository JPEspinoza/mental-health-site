// start slider
const year_slider = document.getElementById('year');
noUiSlider.create(year_slider, {
    start: [year_max - 1, year_max],
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

// get all document elements
const filters = document.getElementsByClassName('filter');

const report_select = document.getElementById('report');
const region_select = document.getElementById('region');
const normalize_checkbox = document.getElementById('normalize');
const map = document.getElementById('map');

function update() {
    if(report_select.value == "null" || region_select.value == "null") {
        // if we are missing the main filters dont do anything
        return;
    }

    // get the values of the inputs
    let report = report_select.value;
    let region = region_select.value;
    let year = year_slider.noUiSlider.get(true);
    let year_low = year[0];
    let year_high = year[1];
    let normalize = normalize_checkbox.checked;

    // show spinner
    map.innerHTML = "";
    map.appendChild(map_spinner);

    // make a request to the backend
    fetch(`/map/report=${report}/region=${region}/year_low=${year_low}/year_high=${year_high}/normalize=${normalize}`)
    .then(response => response.text())
    .then(data => {
        // show map
        map.innerHTML = data;
    });
}

// add event listener to slider
year_slider.noUiSlider.on('end', update);

// whenever the user changes a filter, check if we are ready to request a map
Array.from(filters).forEach(filter => filter.addEventListener("change", update));