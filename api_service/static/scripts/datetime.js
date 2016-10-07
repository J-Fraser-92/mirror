function ordinal_suffix_of(i) {
    var j = i % 10,
        k = i % 100;
    if (j == 1 && k != 11) {
        return "st";
    }
    if (j == 2 && k != 12) {
        return "nd";
    }
    if (j == 3 && k != 13) {
        return "rd";
    }
    return "th";
}

function checkTime(i)
{
    if (i<10)
    {
        i="0" + i;
    }
    return i;
}

function setDate()
{
    var dayNames = [
        "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
    ];

    var monthNames = [
        "January", "February", "March",
        "April", "May", "June",
        "July", "August", "September",
        "October", "November", "December"
    ];

    var today=new Date();

    var day = dayNames[today.getDay()];
    var date = today.getDate();
    var suffix = ordinal_suffix_of(date);
    var month = monthNames[today.getMonth()];

    document.getElementById('day').innerHTML=day;
    document.getElementById('date').innerHTML=date+suffix+" "+month;

    t=setTimeout('startTime()',500);
}

function setTime()
{

    var today=new Date();

    var h=today.getHours();
    var m=today.getMinutes();

    h=checkTime(h);
    m=checkTime(m);

    document.getElementById("time").innerHTML=h+":"+m;


    t=setTimeout('startUpdates()',500);
}

function startUpdates()
{

    setDate();
    setTime();

    var els = document.getElementsByClassName("dateentry");

    i = 0;
    while(!!els[i]){
        var fontsizeBefore = parseFloat(window.getComputedStyle(els[i],null).getPropertyValue("font-size"));
        var widthBefore = els[i].clientWidth;
        var widthAfter = 200;
        var scaleFactor = widthBefore/fontsizeBefore;
        var fontsizeAfter = widthAfter/scaleFactor;

        els[i].style.fontSize = fontsizeAfter + "px";
        i++;
    }

}