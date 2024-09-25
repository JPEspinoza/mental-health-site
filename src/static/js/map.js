// this file contains the javascript used to request the map to the backend and display it on the page
let report_placeholder = document.createElement('option');
report_placeholder.text = "Reporte";
report_placeholder.value = "null";
report_placeholder.disabled = true;
report_placeholder.selected = true;

let year_placeholder = document.createElement('option');
year_placeholder.text = "Año";
year_placeholder.value = "null";
year_placeholder.disabled = true;
year_placeholder.selected = true;

let report_select = document.getElementById('report');
let year_select = document.getElementById('year');
let submit = document.getElementById('submit');

// fill report list when province is selected
document.getElementById('province').addEventListener('change', function() {
    let province = document.getElementById('province').value;

    // clear the options
    year_select.disabled = true;
    year_select.innerHTML = "";
    year_select.append(year_placeholder);
    report_select.innerHTML = "";
    report_select.append(report_placeholder);
    submit.disabled = true;
    
    // make a request to the backend
    fetch(`/map_index_reports/${province}/`)
    .then(response => response.json())
    .then(data => {
        // add the options
        data.reports.forEach(report => {
            let option = document.createElement('option');
            option.value = report;
            option.text = report;
            report_select.append(option);
        });

        report_select.disabled = false;
    });
});

// fill year list when report is selected
document.getElementById('report').addEventListener('change', function() {
    let province = document.getElementById('province').value;
    let report = document.getElementById('report').value;

    // clear the options
    year_select.innerHTML = "";
    year_select.append(year_placeholder);
    submit.disabled = true;

    // make a request to the backend
    fetch(`/map_index_years/${province}/${report}/`)
    .then(response => response.json())
    .then(data => {
        // add the options
        data.years.forEach(year => {
            let option = document.createElement('option');
            option.value = year;
            option.text = year;
            year_select.append(option);
        });

        year_select.disabled = false;
    });
});

// enable submit button when year is selected
document.getElementById('year').addEventListener('change', function() {
    submit.disabled = false;
});

// request map when submit button is clicked
submit.addEventListener('click', function() {
    // get the values of the inputs
    let province = document.getElementById('province').value;
    let report = document.getElementById('report').value;
    let year = document.getElementById('year').value;

    submit.disabled = true;

    // make a request to the backend
    fetch(`/map/${province}/${report}/${year}/`)
    .then(response => response.text())
    .then(data => {
        let map = document.getElementById('map');
        map.innerHTML = data;
    });
});