// start slider
const year_slider = document.getElementById('year');
noUiSlider.create(year_slider, {
    start: [2022, 2024],
    connect: true,
    step: 1,
    range: {
        'min': 2021,
        'max': 2025
    },
    pips: {
        mode: 'steps',
        density: 10
    }
});
year_slider.noUiSlider.disable()

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
const category_select = document.getElementById('category')
const normalize_checkbox = document.getElementById('normalize');
const map = document.getElementById('map');
const establishment = document.getElementById('establishment');

const default_option = document.createElement('option');
default_option.innerHTML = "Seleccionar"
default_option.value = "null";
default_option.disabled = true;
default_option.selected = true;

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
    let establishment_value = establishment.checked;

    // show spinner
    map.innerHTML = "";
    map.appendChild(map_spinner);

    // make a request to the backend
    fetch(`/report=${report}/region=${region}/year_low=${year_low}/year_high=${year_high}/normalize=${normalize}/establishment=${establishment_value}`)
    .then(response => response.json())
    .then(data => {
        // show map
        map.innerHTML = data["map"];
    });
}

// add event listener to slider
year_slider.noUiSlider.on('end', update);

// whenever the user changes a filter, check if we are ready to request a map
Array.from(filters).forEach(filter => filter.addEventListener("change", update));

// whenever the category is selected, clear all inputs and refresh the available reports and year slider
function update_categories() {
    let category = category_select.value;
    report_select.value = "null";

    fetch(`/category=${category}/`)
        .then(response => response.json())
        .then(data => {
            year_min = data["year_min"];
            year_max = data["year_max"];
            reports = data["reports"];

            // add the years to the slider
            year_slider.noUiSlider.updateOptions({
                range: {
                    'min': year_min,
                    'max': year_max
                },
            });
            year_slider.noUiSlider.enable()

            // add reports
            report_select.innerHTML = "";
            report_select.appendChild(default_option);
            reports.forEach(report => {
                let option = document.createElement('option');
                option.value = report[0];
                option.innerHTML = report[1];
                report_select.appendChild(option);
            });
            report_select.disabled = false;
        }
    );
}
document.getElementById("category").addEventListener("change", update_categories)