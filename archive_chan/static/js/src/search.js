google.load('visualization', '1', {packages:['corechart']});
google.setOnLoadCallback(drawChart);

// This is necessary to make the chart responsive.
$(window).resize(function(){
    drawChart();
});

// Function drawing the chart.
function drawChart() {
  var options = {
    fontSize: 12,
    chartArea: {
        top: 0,
        width: '100%',
        height: '80%'
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

  if ($('#chart').length){
      var data = new google.visualization.DataTable(chartData);
      var chart = new google.visualization.LineChart(document.getElementById('chart'));
      chart.draw(data, options);
  }
}
