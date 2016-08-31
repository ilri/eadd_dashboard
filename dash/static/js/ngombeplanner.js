function NppDash(){
    this.data = {};
    this.console = console;
    this.currentView = undefined;
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
    $("#tree_panel ul li div").on('mousedown', function (event) {
        var target = $(event.target).parents('li:first')[0];
        var item = $('#tree_panel').jqxTree('getItem', event.currentTarget.parentElement);
        var rightClick = npp.isRightClick(event);
        
        if (rightClick && item.parentId !== 0) {
            console.log('We have a right click on a farmer node');
            var scrollTop = $(window).scrollTop();
            var scrollLeft = $(window).scrollLeft();
            contextMenu.jqxMenu('open', parseInt(event.clientX) + 5 + scrollLeft, parseInt(event.clientY) + 5 + scrollTop);
        }
        else if(rightClick == false && item.parentId !== 0){
            console.log('We have a left click on a farmer node');
            npp.currentView = 'farmer_display';
            npp.curFarmerId = item.id;
            // npp.getFarmerData();
        }
        else if(rightClick == false && item.parentId == 0){
            console.log('We have a left click on a hub node');
            npp.currentView = 'hub_display';
            npp.curSiteName = item.label;
            // npp.getSiteData();
        }
        return false;
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
    var selectedItem = $('#tree_panel').jqxTree('selectedItem');
    npp.console.log(item+' was clicked');
    npp.console.log(npp.currentView);
    console.log(this);
    switch (item) {
        case "Edit":
            npp.currentView = 'edit_farmer';
            console.log('Editing farmer '+npp.curFarmerId);
            if (selectedItem !== null) {
                $('#tree_panel').jqxTree('addTo', { label: 'Item' }, selectedItem.element);
            }
            break;
        case "Deactivate":
            npp.currentView = 'edit_farmer';
            console.log(this.currentView = 'Deactivate farmer '+npp.curFarmerId);
            if (selectedItem !== null) {
                $('#tree_panel').jqxTree('removeItem', selectedItem.element);
            }
            break;
    }
};

NppDash.prototype.loadFarmerDetails = function(){
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