google.load("visualization","1",{packages:["corechart"]});google.setOnLoadCallback(drawChart);$(window).resize(function(){drawChart()});function drawChart(){var a={fontSize:12,chartArea:{top:0,width:"100%",height:"80%"},legend:{position:"none"},tooltip:{isHtml:true},series:[{color:"#65c6bb"}],curveType:"function"};if($("#chart").length){var c=new google.visualization.DataTable(chartData);var b=new google.visualization.LineChart(document.getElementById("chart"));b.draw(c,a)}};