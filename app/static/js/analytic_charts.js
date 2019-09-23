var timer = null;
var xhr = null;
$('.content').ready(
    // change the content
    function(event) {
        var elem = $(event.currentTarget);
        timer = setTimeout(function() {
            timer = null;
            var ctx = document.getElementById("myChart").getContext('2d');
            var color = Chart.helpers.color;
            var myChart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'My Personality',
                        borderColor: "#ff0033",
                        backgroundColor: color("#ff0033").alpha(0.2).rgbString(),
                        data: [
                            {% for i in range(5) %}
                            {
                            x: {{ i }},
                            y: {{ data['user_personality'][i] }}
                            },
                            {% endfor %}
                        ]
                    }]
                },
                options: {
                    scales: {
                        xAxes: [{
                            type: 'category',
                            labels: ['EXT', 'OPE', 'STA', 'AGR', 'CON']
                        }]
                    }
                }
            });
        }, 1000);
    }
)
