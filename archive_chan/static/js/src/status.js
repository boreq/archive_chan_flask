google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(update);

var statsData, timeout;

// This is necessary to make the chart responsive.
$(window).resize(function(){
    drawChart(statsData);
});

// Trigger the update manually.
$(document).ready(function(){
    $('.last-update-info').on('click', '#update-now', function(){
        update();
    });
});

// Main function updating the data.
function update(){
    // Stop the function from running again in case of a manual update.
    clearTimeout(timeout);

    $('#update-now i').addClass('fa-spin');

    var jsonData = $.ajax({
        url: info_data.api_url,
        dataType: 'json'
    }).done(function(data){
        // Data has to be stored because the chart is redrawn on resize event.
        statsData = data.chart_data;

        // Display the data.
        drawData(data);
        drawChart(data.chart_data);

        // Set the text with the time of the last update.
        var date = new Date();
        $('#last-update').attr("datetime", date.toISOString()).attr("title", date).data("timeago", null).timeago();
    }).always(function(){
        // Schedule the next update.
        timeout = setTimeout(update, 30 * 1000);

        // Stop the icon rotation.
        $('#update-now i').removeClass('fa-spin');
    });
}

// Function filling in the statistics.
function drawData(data) {
    $('#value-last-updates').empty();

    var length = data.last_updates.length;

    for (var i = 0; i < length; i++){
        var entry = data.last_updates[i];

        var date = null;

        if (entry.status > 0){
            date = entry.end;
        }else{
            date = entry.start;
        }

        var css_class = ['started', 'failed', 'completed'];

        $('#value-last-updates').append('<li class="update ' + css_class[entry.status] + '">' + entry.board + ' ' + entry.status_verbose.toLowerCase() + ' <time class="timeago" datetime="' + date + '">' + date + '</time></li>');
    }

    $('#value-last-updates li time').data("timeago", null).timeago();
}

// Function drawing the chart.
function drawChart(data) {
  var options = {
    fontSize: 12,
    chartArea: {
        left: 30,
        top: 10,
        width: '100%',
        height: '90%'
    },
    legend: {
        position: 'none'
    },
    tooltip: {
        isHtml: true
    },
    series: [{
        color: '#65c6bb'
    }],
    explorer: {
        maxZoomOut: 2,
        actions: ['dragToZoom', 'rightClickToReset'],
        keepInBounds: true
    },
    vAxis:{
        minValue: 0
    }
  };

  var chartData = new google.visualization.DataTable(data);
  var chart = new google.visualization.ColumnChart(document.getElementById('chart'));
  chart.draw(chartData, options);
}
