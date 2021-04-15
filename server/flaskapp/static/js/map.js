
var markers = [];
var availableMarkers = [];
window.onLoad = funtion() {window.location.reload();}
let map;

//This function removes the hidden attributes from the map infowindow and its contents
function infoHider(){
    let hidden_div=document.getElementById("stationsTable")
    hidden_div.removeAttribute("hidden")
    
    let hidden_prediction=document.getElementById("predTable")
    hidden_prediction.removeAttribute("hidden")
}

// This function receives the results of running the prediction model with the given variables
function predictGetter(){
    // Returning a promise allows the predictSender function to wait for this function to complete (meaining the function has to wait for a prediction to be made before popualting the table)
    return new Promise((resolve,reject) => {
        //calls the function in the flask file
            fetch("/predSender").then(
            function(response){
                console.log(response)
                if (response.status !== 200){
                    console.log("Somethings gone horribly wrong. Status code: " +response.status);
                    return;
                    }
            response.json().then(function(data){
                //returns the prediction (e.g the predicted amount of free bikes)
                resolve(data);
            });
            });
    })

}



// This saves the default stationTable contents (the calander and button), this allows them to be added to the stationstable as it is updated without repeating the elements
var tablediv = document.getElementById("stationsTable");
var calanderContents= tablediv.innerHTML;

// async Function to return the predicted number of free bikes which is broken down into Poor,Good and Great availability
async function predictSender(number,totalStands){
    // retrieves the inputted date (from the calander)
    var date=document.getElementById("datePicker").value;
    var time=document.getElementById("timePicker").value;
    
    let pred_number
    // This sends the date and the station number to the Flask app file to be used in the prediction
    $.ajax({
        type: 'POST',
        url: '/predGetter',
        contentType: 'application/json;charset=UTF-8',
        dataType: 'json',
        data: JSON.stringify({number,date,time}),
    });
    
    // call the predictGetter function and wait for the result
    pred_number = await predictGetter()
    // convert to a float
    pred_number= parseFloat(pred_number)
    
    var message=document.getElementById("Message")
    // Testing console logs
    //console.log("TOTAL STANDS",totalStands,typeof totalStands)
    //console.log("PRED NUM",pred_number,typeof pred_number)
    //console.log("PERCENTAGE",pred_number/totalStands)
    
    // if the number of bikes available is less than 30%
    if (pred_number/totalStands < .3){
        message.innerHTML="Poor"+"<br>"+"<30% Availability"
    }// if it is between 30 and 60
    else if (pred_number/totalStands > .3 && pred_number/totalStands <.6){
        message.innerHTML="Good"+"<br>"+"<60% Availability"
    }// if it is greater than 60%
    else if (pred_number/totalStands >.6) {
        message.innerHTML="Great"+"<br>"+">60% Availability"
    }
    
};

// These variable store the current weather data which is obtained via the function underneath
let weather_desc;
let weather_temp;
let weather_visibility;
function weatherGetter(){
    fetch("/wthrGetter").then(response => {
        return response.json();
    }).then(data => {
        weather_desc = data[0].Description
        weather_temp = data[0].Temperature
        // conver the temp to a float and then to celcius
        weather_temp = parseFloat(weather_temp) -273.15
        // round to two decimal places
        weather_temp= Number((weather_temp).toFixed(2));
        weather_visibility=data[0].Visibility
        //console.log("Weather variables",weather_desc,weather_temp,weather_desc)
    }).catch(err => {
        console.log("Error in retrieving Weahter data!", err);
    });
}

weatherGetter()

function initMap() {
    
    fetch("/stations").then(response => {
        return response.json();
    }).then(data => {

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
            }); 
            
            
            marker.setMap(map);
            markers.push(marker);
            if (station.AvailableBikes > 1) { availableMarkers.push(marker); }
            
            option.setAttribute("data-station", markers.length - 1);
            
            marker.addListener("click", () => {

                
                var showDetails = document.getElementById("stationsTable");
                var contents= showDetails.innerHTML;
                showDetails.innerHTML =   "<h1 class='Number'>Number:" + station.Number +
                                            "</h1><h2>Name: " + station.Name +
                                            "</h2><h2>BikeStands: " + station.BikeStands + 
                                            "</h2><p>Available Bikes:" + station.AvailableBikes + 
                                            "</p><p>Available Stands:" + station.AvailableBikeStands + 
                                            "</p>"+"<br>"+
                                            "<h1> Weather </h1>"+
                                            "<h2>"+weather_desc+"</h2>"+
                                            "<p>Temperature:"+weather_temp +"c</p>"+
                                            "<p>Visibility:"+weather_visibility+"</p>";
                
                //Creates the button which when pressed fetches the prediction
                var oldbtn= document.getElementById("predictBtn");
                
                if(oldbtn){
                    oldbtn.remove();
                }
                var btn= document.createElement("button");
                btn.setAttribute("id","predictBtn");
                btn.innerHTML="Show me";
                //btn.disabled= true;
                // create predicted variable (got buggy if it wasnt defined outside of the addEventListener)
                let predicted
                btn.addEventListener("click",function(){
                    // sets the Onlick functionality of the button to Calling the predict sender function with the appropriate variables as argument
                    predicted = predictSender(station.Number,station.BikeStands)
                });
                document.getElementById("buttonPlace").appendChild(btn);
                
                
                // Creates the max and Min dates for the calander (Setting the seconds,milliseconds and Minnutes to 0 prevents the user from selecting those from the calander)
                var date=new Date();
                date.setSeconds(0,0);
                date.setMilliseconds(0,0);
                date.setMinutes(0,0);
                

                var now = new Date();
                now.setSeconds(0,0);
                now.setMilliseconds(0,0);
                now.setMinutes(0,0);
                //console.log(now.toISOString())

                date.setDate(date.getDate()+7)
                //console.log(date.toISOString())
                document.getElementById("datePicker").max=date.toISOString().split("T")[0];
                document.getElementById("datePicker").min=now.toISOString().split("T")[0];                            
                // Generate infoWindow with station Name and make it dissapear 
                // when clicking on another marker
                infoWindow.close();
                infoWindow.setContent("<h2>" + marker.getTitle() + "</h2>");
                infoWindow.open(marker.getMap(), marker);

                //Creates the charts;
                chartMaker(station.Number, station.Name);
                //Unhides everything (if hidden already)
                infoHider();
            });
          
            
        });
    }).catch(err => {
        console.log("OOPS!", err);
    });
}


// Get the element from the Dropdown menu and link it to the marker onClick event
document.getElementById("dropdown").addEventListener("change", stationsDropDown);

function stationsDropDown(e) {
    var selectObject = e.target;
    const targetMarkerIndex = selectObject.options[selectObject.selectedIndex].getAttribute("data-station");
    const targetMarker = markers[targetMarkerIndex];
    google.maps.event.trigger(targetMarker, "click");
    
    if(selectObject && selectObject.selected){
        const targetMarkerIndex = selectObject.getAttribute("data-station");
        const targetMarker = markers[targetMarkerIndex];
        google.maps.event.trigger(targetMarker, "click");
    }
}


// Functions that return the json data of the past week of stand history. Uses promises to allow for async operation (else the charts wouldnt be made correctly in time)
function json_getter_week(){
    return new Promise((resolve,reject) => {
            fetch("/btnFunc").then(
            function(response){
                // if the response isnt successfull
                if (response.status !== 200){
                    console.log("Somethings gone horribly wrong. Status code: " +response.status);
                    return;
                    }
            response.json().then(function(data){
                //return data;
                resolve(data)
            });
            });
    })
};


// Same logic as above but returns the data from the past 24 hours
function json_getter_day(){
    return new Promise((resolve,reject) => {
            fetch("/btnFuncDay").then(
            function(response){
                if (response.status !== 200){
                    console.log("Somethings gone horribly wrong. Status code: " +response.status);
                    return;
                }
            response.json().then(function(data){
                //return data;
                resolve(data)
            });
            });
    })
};


// This sends a variable (station number) back to flask to be used in a query to the database
function varSender(number){
    // sends the variable to the flask app in a json format with the "key" number
    $.ajax({
        type: 'POST',
        url: '/varSender',
        contentType: 'application/json;charset=UTF-8',
        dataType: 'json',
        data: JSON.stringify({number}),
    });

}


// Button functionality
async function chartMaker(station_number,station_name){
    //sends the station number to the flask app to be used in the sql query
    varSender(station_number);
    
    let dailyLoad=document.getElementById("dailyChart").getContext("2d")
    
   let weeklyLoad=document.getElementById("weeklyChart").getContext("2d")
    
    // creates a loading wheel while the data is being retrieved
    let dayload=new Chart(dailyLoad,{
        type:"doughnut",
        data:{
            labels:["Loading"],
            datasets:[{
                data:[5],
                backgroundColor:"#9bc3ca"
            }]
        },
        // disables interaction
        options:{
            tooltips:{enabled:false},
            hover: {mode:null},
            animation:{
                animateRotate:true,
                
            }
        }
    });
    
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
    });
     
    // empty arrays to save the individual variables to for chart purposes
    var daytimes = [];
    var dayAvailBike = [];
    var dayAvailStands=[];
    var weekTimes = []
    var weekAvailBikes=[]
    var weekAvailStands=[]
    
    // Calls the data from the SQL query (for the past week and the past 24 hours) into a json variable
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
    
    // create the chart for past 24 hours
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
                 title:{
                     display: true,
                     text: "Past 24 hours bike availability"
                 }
         }
    });

    //create the chart for the past week
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
                 title:{
                     display: true,
                     text: "Past 7 days bike availability"
                 }
         }
    
    });;
};
   
// as the day value returned from the SQL query is 0-6 this just converts it into is string representation for easier legibility
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
    
