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

    // Hide obvious statistics.
    if (info_data.thread){
        $('#value-average-thread').closest('li').hide();
        $('#value-total-threads').closest('li').hide();
    }
});

// Main function updating the data.
function update(){
    // Stop the function from running again in case of a manual update.
    clearTimeout(timeout);

    $('#update-now i').addClass('fa-spin');

    request_data = {}

    if (info_data.thread)
        request_data['thread'] = info_data.thread;

    if (info_data.board)
        request_data['board'] = info_data.board;

    var jsonData = $.ajax({
        url: info_data.api_url,
        data: request_data,
        dataType: 'json'
    }).done(function(data){
        // Data has to be stored because the chart is redrawn on resize event.
        statsData = data;

        // Display the data.
        drawStats(data);
        drawChart(data);

        // Set the text with the time of the last update.
        var date = new Date();
        $('#last-update').attr("datetime", date.toISOString()).attr("title", date).data("timeago", null).timeago();
    }).always(function(){
        // Schedule the next update.
        timeout = setTimeout(update, 15 * 1000);

        // Stop the icon rotation.
        $('#update-now i').removeClass('fa-spin');
    });
}

// Function filling in the statistics.
function drawStats(data) {
    $('#value-total-threads').text(data.total_threads);
    $('#value-total-posts').text(data.total_posts);
    $('#value-total-text').text(data.total_posts - data.total_image_posts);
    $('#value-total-image').text(data.total_image_posts);

    // Show more detailed value if it is small.
    var averageHour = data.recent_posts / data.recent_posts_timespan;
    if (averageHour > 10){
        averageHour = Math.round(averageHour);
    }else{
        averageHour = Math.round(averageHour * 100) / 100;
    }
    $('#value-average-hour').text(averageHour);

    if (data.total_threads > 0){
        $('#value-average-thread').text(Math.round(data.total_posts / data.total_threads));
    }else{
        $('#value-average-thread').text('0');
    }

    if (data.total_posts > 0){
        $('#value-percent-image').text(Math.round(data.total_image_posts / data.total_posts * 100) + '%');
    }else{
        $('#value-percent-image').text('0%');
    }

}

// Function drawing the chart.
function drawChart(data) {
  var options = {
    fontSize: 12,
    chartArea: {
        left: 50,
        top: 10,
        width: '100%',
        height:  '80%'
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
    curveType: 'function'
  };

  var chartData = new google.visualization.DataTable(data.chart_data);
  var chart = new google.visualization.LineChart(document.getElementById('chart'));
  chart.draw(chartData, options);
}
