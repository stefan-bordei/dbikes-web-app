
var markers = [];
var availableMarkers = [];

/*
// Load the Visualization API and the corechart package.
google.charts.load('current', {'packages':['corechart']});

// Set a callback to run when the Google Visualization API is loaded.
google.charts.setOnLoadCallback(drawChart);
*/


let map;

function infoHider(){
    let hidden_div=document.getElementById("stationsTable")
    hidden_div.removeAttribute("hidden")
    
    let hidden_cal=document.getElementById("timePicker")
    hidden_cal.removeAttribute("hidden")
}

//Behold chart eater, destroyer of charts, conquerer of systems (i need coffee)
/*
function chartEater(){
    console.log("NOM NOM NOM")
    window.dailyChart.destroy();
    window.weeklyChart.destroy();

    var daycanvas= document.createElement("canvas");
    daycanvas.setAttribute("id","dailyChart");
    
    var weekcanvas= document.createElement("canvas");
    daycanvas.setAttribute("id","weeklyChart")
    
    
    document.getElementById("daychart_wrapper").appendChild(daycanvas);
    document.getElementById("weekchart_wrapper").appendChild(weekcanvas);
    */
    
//}

function predictSender(number){
    console.log("PREDICT BUTTON")
    var date=document.getElementById("timePicker").value
    
    console.log("HERE",typeof date)
    
    console.log("date",date)
    console.log("number",number)
    
    $.ajax({
        type: 'POST',
        url: '/predGetter',
        contentType: 'application/json;charset=UTF-8',
        dataType: 'json',
        data: JSON.stringify({number,date}),
    });
    
    
};

function initMap() {
    
    fetch("/stations").then(response => {
        return response.json();
    }).then(data => {
        console.log("data: ", data);
        
        map = new google.maps.Map(document.getElementById("map"), {
            center: { lat: 53.349804, lng: -6.260310 },
            zoom: 14,
        });
        const bikegreen ={
            url: $("#bycicleGreen").val(),
            scaledSize: new google.maps.Size(50, 50), 
            origin: new google.maps.Point(0,0),
            anchor: new google.maps.Point(0, 0) 
        };
        const bikered ={
            url: $("#bycicleRed").val(),
            scaledSize: new google.maps.Size(50, 50), 
            origin: new google.maps.Point(0,0),
            anchor: new google.maps.Point(0, 0) 
        };
        const bikeyel ={
            url: $("#bycicleYel").val(),
            scaledSize: new google.maps.Size(50, 50), 
            origin: new google.maps.Point(0,0),
            anchor: new google.maps.Point(0, 0) 
        };
        
        // Find closest station with AvailableBikes to the click location
        google.maps.event.addListener(map, 'click', find_closest_marker);
        // Create infoWindow for the markers to display station Name
        const infoWindow = new google.maps.InfoWindow();
        
        data.forEach(station => {
            var iconColor;
            if (station.AvailableBikes>=20){
                iconColor = bikegreen;
            }else if (station.AvailableBikes < 20 && station.AvailableBikes>5){
                iconColor = bikeyel;
            }else if (station.AvailableBikes <= 5){
                iconColor = bikered;
            }

            const marker = new google.maps.Marker({
                title: station.Name,
                position: { lat: station.PosLat, lng: station.PosLng },
                icon: iconColor,
                map: map,
            });
            
            // This creates a dropdown menu item with the text of the station name and a value of the station number (This will be used for displaying the right stations information)
            var dropdown = document.getElementById("dropdown");
            var option = document.createElement("option");
            option.text = station.Name;
            option.value = station.Number;
            dropdown.appendChild(option);
            
              
            option.addEventListener("click", () => {
                google.maps.event.trigger(marker, "click");
                console.log("CLICKED!!" + option.text);
            }); 
            
            
            marker.setMap(map);
            markers.push(marker);
            if (station.AvailableBikes > 1) { availableMarkers.push(marker); }
            
            option.setAttribute("data-station", markers.length - 1);
            
            marker.addListener("click", () => {
                var showDetails = document.getElementById("stationsTable");
                var contents= showDetails.innerHTML;
                showDetails.innerHTML="";
                 
                showDetails.innerHTML =   "<h1 class='Number'>Number:" + station.Number +
                                            "</h1><h1>Name: " + station.Name +
                                            "</h1><h1>BikeStands: " + station.BikeStands + 
                                            "</h1><p>Available Bikes:" + station.AvailableBikes + 
                                            "</p><p>Available Stands:" + station.AvailableBikeStands + 
                                            "</p>"+
                                            contents;
                var btn= document.createElement("button")
                btn.innerHTML="Show me";
                btn.id=station.Number;
                btn.addEventListener("click",function(){
                    predictSender(station.Number)
                });
                
                document.getElementById("calander").appendChild(btn);
                //showDetails.appendChild(btn);
                var date=new Date();
                date.setSeconds(0,0);
                date.setMilliseconds(0,0);
                date.setMinutes(0,0);
                
                var now = new Date();
                now.setSeconds(0,0);
                now.setMilliseconds(0,0);
                now.setMinutes(0,0);
                
                date.setDate(date.getDate()+7)
                document.getElementById("timePicker").max=date.toISOString().split(".")[0];
                document.getElementById("timePicker").min=now.toISOString().split(".")[0];
                // Generate infoWindow with station Name and make it dissapear 
                // when clicking on another marker
                infoWindow.close();
                infoWindow.setContent("<h2>" + marker.getTitle() + "</h2>");
                infoWindow.open(marker.getMap(), marker);

                //drawChart(station, station.AvailableBikes, station.AvailableBikeStands);
                buttonPrediction(station.Number, station.Name);
                infoHider();
            });
          
            
        });
    }).catch(err => {
        console.log("OOPS!", err);
    });
}

function stationsDropDown(selectObject) {
    if(selectObject && selectObject.selected){
        const targetMarkerIndex = selectObject.getAttribute("data-station");
        const targetMarker = markers[targetMarkerIndex];
        google.maps.event.trigger(targetMarker, "click");
    }
}

/*
// draw the PIE Chart    
function drawChart(station, bikes, bstands) {
    console.log("Printing chart")
    if (!station) {return false;}
    
    // Create the data table.
    var chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'Name');
    chartData.addColumn('number', 'Available Bikes');
    chartData.addRows([
    ['AvailableBikes', bikes],
    ['AvailableBikeStands', bstands]
    ]);

    // Set chart options
    var options = {
                'width':'100%',
                'height':'500',
                'margin-left': 'auto',
                'margin-right': 'auto',};
          
    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.PieChart(document.getElementById('pieChart'));
    chart.draw(chartData, options);
}
*/

// Functions that return the json data of calling the queries. Uses promises to allow for async operation (else the charts wouldnt be made correctly in time)
function json_getter_week(){
    return new Promise((resolve,reject) => {
            fetch("/btnFunc").then(
            function(response){
                console.log(response)
                if (response.status !== 200){
                    console.log("Somethings gone horribly wrong. Status code: " +response.status);
                    return;
                    }
            response.json().then(function(data){
                console.log("Table data week: ",data)
                //return data;
                resolve(data)
            });
            });
    })
};

function json_getter_day(){
    return new Promise((resolve,reject) => {
            fetch("/btnFuncDay").then(
            function(response){
                console.log(response)
                if (response.status !== 200){
                    console.log("Somethings gone horribly wrong. Status code: " +response.status);
                    return;
                }
            response.json().then(function(data){
                console.log("Table data day: ",data)
                //return data;
                resolve(data)
            });
            });
    })
};

// This sends a variable (going to be the station number) back to flask to be used in a query
function varSender(number){
    console.log("WORKING")
    console.log(number)

    $.ajax({
        type: 'POST',
        url: '/varSender',
        contentType: 'application/json;charset=UTF-8',
        dataType: 'json',
        data: JSON.stringify({number}),
    });
    // stop link reloading the page
    // event.preventDefault();
        
}



// Button functionality
async function buttonPrediction(station_number,station_name){
    varSender(station_number);
    
    let dailyLoad=document.getElementById("dailyChart").getContext("2d")
    
   let weeklyLoad=document.getElementById("weeklyChart").getContext("2d")
    
    
    let dayload=new Chart(dailyLoad,{
        type:"doughnut",
        data:{
            labels:["Loading"],
            datasets:[{
                data:[5],
                backgroundColor:"#9bc3ca"
            }]
        },
        options:{
            tooltips:{enabled:false},
            hover: {mode:null},
            animation:{
                animateRotate:true,
                
            }
        }
    }
            );
    
     let weekload=new Chart(weeklyLoad,{
        type:"doughnut",
        data:{
            labels:["Loading"],
            datasets:[{
                data:[5],
                backgroundColor:"#9bc3ca"
            }]
        },
        options:{
            tooltips:{enabled:false},
            hover: {mode:null},
            animation:{
                animateRotate:true,
                
            }
        }
    }
            );
    // empty arrays to save the individual variables to for chart purposes
    var daytimes = [];
    var dayAvailBike = [];
    var dayAvailStands=[];
    var weekTimes = []
    var weekAvailBikes=[]
    var weekAvailStands=[]

    var jsonweek = await json_getter_week();
    var jsonday = await json_getter_day();
    
    // Assign each variable in the json files to its appropriate list
    for(i in jsonweek){
        weekTimes.push(dayConverter(new Date(jsonweek[i].LastUpdate).getDay()));
        weekAvailBikes.push(jsonweek[i].AvailableBikes);
        weekAvailStands.push(jsonweek[i].AvailableBikeStands);
        
    }
    
    for(i in jsonday){
        daytimes.push(String(new Date(jsonday[i].LastUpdate).getHours()) + ":00");
        dayAvailBike.push(jsonday[i].AvailableBikes);
        dayAvailStands.push(jsonday[i].AvailableBikeStands);             
    }
    
    
    // this destroys any previous charts (Got buggy once you tried a few times, old ones would pop in and out)
    
    dayload.destroy();
    weekload.destroy();
        
    let dailyChart=document.getElementById("dailyChart")
    dailyChart.getContext("2d")
    
    let weeklyChart=document.getElementById("weeklyChart")
    weeklyChart.getContext("2d")
    
   let daychart= new Chart(dailyChart,{
        type:"line",
        data:{
            labels:daytimes,
            datasets:[{
                label:"Free bikes",
                data:dayAvailBike,
                borderColor:"#4f8c96",
               backgroundColor:"#9bc3ca"
                
            },{
                label:"Free Stands",
                data:dayAvailStands,
                borderColor:"#006c7f",
                backgroundColor:"#b3f4ff"
            }]
        },
         options:{
             plugins:{
                 title:{
                     display: true,
                     text: "Past 24 hours"
                 }
             }
         }
    });

    
    let weekChart =new Chart(weeklyChart,{
        type:"line",
        data:{
            labels:weekTimes,
            datasets:[{
                label:"Free bikes",
                data:weekAvailBikes,
                borderColor:"#4f8c96",
               backgroundColor:"#9bc3ca"
                
            },{
                label:"Free Stands",
                data:weekAvailStands,
                borderColor:"#006c7f",
                backgroundColor:"#b3f4ff"
            }]
    },
            options:{
             plugins:{
                 title:{
                     display: true,
                     text: "Past 7 days"
                 }
             }
         }
    
    });;
};
    
function dayConverter(day_number){
    var days={
        0 : "Sunday",
        1 : "Monday",
        2 : "Tuesday",
        3 : "Wednesday",
        4 : "Thursday",
        5 : "Friday",
        6 : "Saturday",

    };
    return days[day_number];
}

// Finding closest station on the mapbikes
function rad(x) {return x*Math.PI/180;}
function find_closest_marker( event ) {
    var lat = event.latLng.lat();
    var lng = event.latLng.lng();
    var R = 6371; // radius of earth in km
    var distances = [];
    var closest = -1;
    for( i=0;i<markers.length; i++ ) {
        var mlat = markers[i].position.lat();
        var mlng = markers[i].position.lng();
        var dLat  = rad(mlat - lat);
        var dLong = rad(mlng - lng);
        var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(rad(lat)) * Math.cos(rad(lat)) * Math.sin(dLong/2) * Math.sin(dLong/2);
        var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        var d = R * c;
        distances[i] = d;
        if ( closest == -1 || d < distances[closest] ) {
            closest = i;
        }
    }

    alert("Closest station with AvailableBikes to that location is:\n\n" + markers[closest].title);
}
    
