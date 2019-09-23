$('.content').ready(
    // CHANGE THE CONTENT
    function(event) {
        var elem = $(event.currentTarget);
        var panel = document.createElement("div");
        panel.className = "panel panel-default"
        var panel_header = document.createElement("div");
        panel_header.className = "panel-heading";
        panel_header.innerHTML = "my Header";
        panel.append(panel_header);
        var panel_body = document.createElement("div");
        panel_body.className = "panel-body";
        panel_body.innerHTML = "Panel content";
        panel.append(panel_body);
        elem.append(panel);
    }
);
