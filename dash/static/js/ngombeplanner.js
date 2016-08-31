function NppDash(){
    this.data = {};
    this.console = console;
}

NppDash.prototype.initiateFarmersTree = function(){
    npp.console.log('Creating the farmers tree');
    // prepare the data
    var source = { datatype: "json", datafields: [ {name: 'id'}, {name: 'parentid'}, {name: 'text'} ], id: 'id', localdata: NppDash.data.allFarmers };

    // create data adapter.
    var dataAdapter = new $.jqx.dataAdapter(source);
    // perform Data Binding.
    dataAdapter.dataBind();
    // get the tree items. The first parameter is the item's id. The second parameter is the parent item's id. The 'items' parameter represents
    // the sub items collection name. Each jqxTree item has a 'label' property, but in the JSON data, we have a 'text' field. The last parameter
    // specifies the mapping between the 'text' and 'label' fields.
    var records = dataAdapter.getRecordsHierarchy('id', 'parentid', 'items', [{name: 'text', map: 'label'}]);
    $('#tree_panel').jqxTree({source: records, width: '300px', theme: '', checkboxes: false });
    npp.console.log('Farmers tree created');
    npp.console.log('Adding the context menu');
    var contextMenu = $("#context_menu").jqxMenu({ width: '120px', theme: 'darkblue', height: '56px', autoOpenPopup: false, mode: 'popup' });
    
    // disable right click when the user is on the tree
    $(document).bind('contextmenu', function (e) {
        if ($(e.target).parents('.jqx-tree').length > 0) {
            return false;
        }
        return true;
    });
    
    var clickedItem = null;
    // open the context menu when the user presses the mouse right button.
    $("#tree_panel li div").on('mousedown', function (event) {
        var target = $(event.target).parents('li:first')[0];
        var rightClick = npp.isRightClick(event);
        
        if (rightClick) {
            var scrollTop = $(window).scrollTop();
            var scrollLeft = $(window).scrollLeft();
            contextMenu.jqxMenu('open', parseInt(event.clientX) + 5 + scrollLeft, parseInt(event.clientY) + 5 + scrollTop);
            // return false;
        }
        return false;
    });
    
    $("#tree_panel li div").on('click', function (event) {
        var item = $('#tree_panel').jqxTree('getItem', args.element);
        if(item.parentId == 0){
            console.log('We have a site');
           // we have a site, so lets get the sites data
           npp.curSiteName = item.label;
           // npp.getSiteData();
        }
        else{
            console.log('We have a farmer');
           npp.curFarmerId = item.id;
           // npp.getFarmerData();
        }
    });
    
    $("#context_menu").on('itemclick', npp.implementRightClick);
};

NppDash.prototype.isRightClick = function(event) {
    var rightclick;
    if (!event) var event = window.event;
    if (event.which) rightclick = (event.which == 3);
    else if (event.button) rightclick = (event.button == 2);
    return rightclick;
};

// Implement the right click when an item is clicked
NppDash.prototype.implementRightClick = function(event){
    var item = $(event.args).text();
    var selectedItem = $('#tree_menu').jqxTree('selectedItem');
    npp.console.log(item+' was clicked');
    switch (item) {
        case "Add Item":
            if (selectedItem !== null) {
                $('#tree_menu').jqxTree('addTo', { label: 'Item' }, selectedItem.element);
            }
            break;
        case "Remove Item":
            if (selectedItem !== null) {
                $('#tree_menu').jqxTree('removeItem', selectedItem.element);
            }
            break;
    }
};

NppDash.prototype.loadFarmerDetails = function(){
    // create the places where we will load the farmer details
    $('#details_panel').html("<div id='farmer'></div><div id='cows'></div>");
    
    // get the details of the farmer and the cows
    $.ajax({
        type:"POST", url:'mod_ajax.php?page=siteData&do=fetch', dataType:'json', data: {farmer_id: npp.curFarmer.id}, async: false,
        error: npp.communicationError,
        success: function(data){
           if(data.error) {
              Notification.show({create: true, hide: true, updateText: false, text: 'There was an error while communicating with the server', error:true});
              return;
           }
           else{

           }
        }
    });
};

var npp = new NppDash();