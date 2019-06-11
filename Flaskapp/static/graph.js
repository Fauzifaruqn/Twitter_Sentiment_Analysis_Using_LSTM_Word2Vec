$(document).ready(function() {
	// $.getJSON('http://127.0.0.1:5000/data',function(data){
	// 	console.log(data)

	$(chart_id).highcharts({
		// chart: chart,
		// title: title,
		// xAxis: {
		// 	type: 'datetime',
		// 	tickPixelInterval: 200,
		// 	categories:data['X'],labels:{step:10}
		// },
		// yAxis: {
		// 	name:'Sentiment'
			
		// },
		// series:[ {data : data['Y'] , color: '#FF00FF'}],
		// data: {
		// 	rowsURL: 'http://127.0.0.1:5000/data',
		// 	firstRowAsNames: false,
		// 	enablePolling: true
		// }
		chart: {
			type: 'area'
		},
		plotOptions: {
		area: {
				fillColor: {
					linearGradient: {
						x1: 0,
						y1: 0,
						x2: 0,
						y2: 1
					},
					stops: [
						[0, Highcharts.getOptions().colors[0]],
						[1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
					]
				},
				marker: {
					radius: 2
				},
				lineWidth: 1,
				states: {
					hover: {
						lineWidth: 1
					}
				},
				marker: {
					enabled: false
				},
				threshold: null
			}	
		},
		title: {
			text: 'Live sentiment'
		},
	
		subtitle: {
			text: 'Data input from a remote JSON file'
		},
	
		data: {
			rowsURL: 'http://127.0.0.1:5000/static/data.json',
			firstRowAsNames: false,
			enablePolling: true
		},

	});
	$('#volume').highcharts({
		chart: {
			type: 'column',
		},
		title: {
			text: 'Volume of tweets every 2 seconds'
		},
	
		subtitle: {
			text: 'Data input from a remote JSON file'
		},
	
		data: {
			rowsURL: 'http://127.0.0.1:5000/static/bar.json',
			firstRowAsNames: false,
			enablePolling: true
		},

	});
	$('#pie').highcharts({
		chart: {
			type: 'pie',
			options3d: {
				enabled: true,
				alpha: 45,
				beta: 0
			}
		},
		title: {
			text: 'Sentiment of the last 100 recent tweets'
		},
		tooltip: {
			pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
		},
		plotOptions: {
			pie: {
				allowPointSelect: true,
				cursor: 'pointer',
				depth: 35,
				dataLabels: {
					enabled: true,
					format: '{point.name}'
				}
			}
		},
		data: {
			rowsURL: 'http://127.0.0.1:5000/static/pie.json',
			firstRowAsNames: false,
			enablePolling: true
		},

	});
});

