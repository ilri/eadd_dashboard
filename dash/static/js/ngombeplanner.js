function NppDash(){
    this.data = {};
    this.console = console;
    this.currentView = undefined;
    this.csrftoken = $('meta[name=csrf-token]').attr('content');
    this.reEscape = new RegExp('(\\' + ['/', '.', '*', '+', '?', '|', '(', ')', '[', ']', '{', '}', '\\'].join('|\\') + ')', 'g')
    console.log('set csrf-token: '+ this.csrftoken)

    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", npp.csrftoken)
        }
      }
   });
}

/**
 * Format the autocomplete suggestions
 */
NppDash.prototype.fnFormatResult = function (value, searchString) {
    var pattern = '(' + searchString.replace(npp.reEscape, '\\$1') + ')';
    return value.data.replace(new RegExp(pattern, 'gi'), '<strong>$1<\/strong>');
};

NppDash.prototype.confirmSelection = function () {
    console.log('Confirm the selection made...');
};

/**
 * Check whether we have a right click on a tree node
 *
 * @param   {event}     event   The event which occurred
 * @returns {Boolean}   Returns true if it was a right click else it returns false
 */
NppDash.prototype.isRightClick = function(event) {
    var rightclick;
    if (!event) var event = window.event;
    if (event.which) rightclick = (event.which == 3);
    else if (event.button) rightclick = (event.button == 2);
    return rightclick;
};

NppDash.prototype.initiateFarmersTree = function(){
    npp.console.log('Creating the farmers tree');
    // prepare the data
    var source = {datatype: "json", datafields: [{name: 'id'}, {name: 'parentid'}, {name: 'text'}], id: 'id', localdata: NppDash.data.allFarmers};

    // create data adapter.
    var dataAdapter = new $.jqx.dataAdapter(source);
    // perform Data Binding.
    dataAdapter.dataBind();
    // get the tree items. The first parameter is the item's id. The second parameter is the parent item's id. The 'items' parameter represents
    // the sub items collection name. Each jqxTree item has a 'label' property, but in the JSON data, we have a 'text' field. The last parameter
    // specifies the mapping between the 'text' and 'label' fields.
    var records = dataAdapter.getRecordsHierarchy('id', 'parentid', 'items', [{name: 'text', map: 'label'}]);
    $('#tree_panel').jqxTree({source: records, width: '300px', theme: '', checkboxes: false});
    npp.console.log('Farmers tree created');
    npp.console.log('Adding the context menu');
    var contextMenu = $("#context_menu").jqxMenu({width: '120px', theme: 'darkblue', height: '56px', autoOpenPopup: false, mode: 'popup'});

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

        console.log('Parent Id: '+ item.parentId);
        console.log('Item Id: '+ item.id);
        if (rightClick && item.parentId !== 0) {
            console.log('We have a right click on a farmer node');
            npp.curFarmerId = item.id;
            var scrollTop = $(window).scrollTop();
            var scrollLeft = $(window).scrollLeft();
            contextMenu.jqxMenu('open', parseInt(event.clientX) + 5 + scrollLeft, parseInt(event.clientY) + 5 + scrollTop);
        }
        else if(rightClick == false && item.parentId !== 0){
            console.log('We have a left click on a farmer node ');
            npp.currentView = 'farmer_display';
            npp.curFarmerId = item.id;
            // npp.getFarmerData();
        }
        else if(rightClick == false && item.parentId == 0){
            console.log('We have a left click on a hub node');
            npp.currentView = 'hub_display';
            npp.currentHubName = item.id;
            // npp.getSiteData();
        }
        return false;
    });

    $("#context_menu").on('itemclick', npp.implementRightClick);
};


/**
 * Implement the right click when an item is clicked
 */
NppDash.prototype.implementRightClick = function(event){
    var item = $(event.args).text();
    npp.console.log(item+' was clicked');
    switch (item) {
        case "Edit":
            console.log('Editing farmer '+npp.curFarmerId);
            if(npp.currentView === undefined || npp.currentView !== 'edit_farmer'){
               // load the farmer edit panel
               $('#details_panel').load('/edit_farmer');
               npp.currentView = 'edit_farmer';
            }
            npp.editFarmer();
            break;
        case "Deactivate":
            npp.currentView = 'deactivate_farmer';
            break;
    }
};

/**
 * Load the farmer display interface for editing the farmers
 * @returns {undefined}
 */
NppDash.prototype.editFarmer = function(){
   // get the farmer particulars
    var data = {farmer_id: npp.curFarmerId};
    var request = $.ajax({
        type: "POST", url: $SCRIPT_ROOT + "/farmer_details", contentType: "application/json", dataType: 'json', data: JSON.stringify(data),
        error: npp.communicationError,
        success: function (data) {
            if (data.error) {
                Notification.show({create: true, hide: true, updateText: false, text: 'There was an error while communicating with the server', error: true});
                return;
            } else {
                npp.currentFarmer = data;
                npp.initiateFarmerGrid();
            }
        }
    });
};

/**
 * Ready the edit panel as well as the jqx table
 * @returns {undefined}
 */
NppDash.prototype.initiateFarmerGrid = function () {
    // create the source for the grid
    var source = {
        datatype: 'json', datafields: [{name: 'farmer_id'}, {name: 'farmer_name'}, {name: 'hub'}, {name: 'mobile_no'}, {name: 'cf'}, {name: 'locale'}, {name: 'is_active'}],
        localdata: npp.currentFarmer.farmer
    };
    var farmerAdapter = new $.jqx.dataAdapter(source);
    // initialize jqxGrid
    if ($('#farmer_details :regex(class, jqx\-grid)').length === 0) {
        $("#farmer_details").jqxGrid({
            width: 950,
            height: 230,
            source: source,
            columnsresize: true,
            altrows: true,
            touchmode: false,
            rowdetails: true,
            initrowdetails: npp.initiateCowDetails,
            rowdetailstemplate: {rowdetails: "<div id='grid' style='margin: 5px;'></div>", rowdetailsheight: 150, rowdetailshidden: false},
            columns: [
                {datafield: 'farmer_id', hidden: true},
                {text: 'Name', datafield: 'farmer_name', width: 135, cellsrenderer: function (row, columnfield, value, defaulthtml, columnproperties, rowdata) {
                        return '<a href="javascript:;" id="' + rowdata.id + '" class="farmer_id_href">&nbsp;' + value + '</a>';
                    }
                },
                {text: 'Hub', datafield: 'hub', width: 110},
                {text: 'Mobile No', datafield: 'mobile_no', width: 100},
                {text: 'Alternative No', datafield: 'mobile_no2', width: 100},
                {text: 'CF', datafield: 'cf', width: 140},
                {text: 'Language', datafield: 'locale', width: 80},
                {text: 'Is Active', datafield: 'is_active', width: 80},
                {text: 'Actions', datafield: 'actions', width: 170, cellsalign: 'center',
                    cellsrenderer: function (row, columnfield, value, defaulthtml, columnproperties, rowdata) {
                        return '<button id="edit_farmer_' + rowdata.farmer_id + '" class="editing_farmer btn btn-success btn-xs">&nbsp;Edit</button>\
                    <buttin id="deactivate_farmer_' + rowdata.farmer_id + '" class="deact_farmer btn btn-danger btn-xs">&nbsp;Deactivate</button>';
                    }
                }
            ]
        });
    } else {
        console.log('Update the FARMER grid with the new info...')
        $("#farmer_details").jqxGrid({source: farmerAdapter});
    }

    $('.editing_farmer').on('click', npp.startFarmerEditing);
};

/**
 * Initiate the sub table of the cow details
 */
NppDash.prototype.initiateCowDetails = function(index, parentElement, gridElement, dr){
   var grid = $($(parentElement).children()[0]);

    var eventsSource = {
        datatype: "json", datafields: [{name: 'cow_id'}, {name: 'cow_name'}, {name: 'ear_tag'}, {name: 'sex'}, {name: 'dob'}, {name: 'breed_group'}, {name: 'is_milking'}, {name: 'is_active'}, {name: 'is_incalf'}, {name: 'parity'}], type: 'POST',
        localdata: npp.currentFarmer.animals
    };

    if (grid !== null) {
        grid.jqxGrid({
            source: eventsSource,
            theme: '',
            width: 890,
            height: 170,
            columnsresize: true,
            columns: [
                {datafield: 'cow_id', hidden: true},
                {text: 'Name', datafield: 'cow_name', width: 100},
                {text: 'Ear Tag', datafield: 'ear_tag', hidden: true},
                {text: 'Sex', datafield: 'sex', width: 70},
                {text: 'DoB', datafield: 'dob', width: 100},
                {text: 'Breed Group', datafield: 'breed_group', width: 130},
                {text: 'Is Active', datafield: 'is_active', width: 80},
                {text: 'Is Milking', datafield: 'is_milking', width: 140},
                {text: 'In Calf', datafield: 'is_incalf', width: 70},
                {text: 'Parity', datafield: 'parity', width: 60},
                {text: 'Actions', datafield: 'actions', width: 130, cellsalign: 'center',
                    cellsrenderer: function (row, columnfield, value, defaulthtml, columnproperties, rowdata) {
                        return '<button id="' + row + '" class="editing_cow btn btn-success btn-xs">&nbsp;Edit</button>\
                        <buttin id="deactivate_cow_' + rowdata.cow_id + '" class="deact_cow btn btn-danger btn-xs">&nbsp;Deactivate</button>';
                    }
                }
            ]
        });
    }
    $('.editing_cow').on('click', npp.startCowEditing);
};

NppDash.prototype.farmerReport = function(){};

NppDash.prototype.hubReport = function(){};

/**
 * Configure the autocomplete fields
 */
NppDash.prototype.configureEditAutocomplete = function (module) {
    var autocomplete_fields = [];
    if(module === 'farmer'){
        autocomplete_fields = [
            {field: 'cf', sub_module: 'all_cfs'},
            {field: 'hub', sub_module: 'all_hubs'},
            {field: 'locale', sub_module: 'all_locale'}
        ];
    }
    else if(module === 'cow'){
        autocomplete_fields = [
            {field: 'breed_group', sub_module: 'all_breeds'},
            {field: 'milking_status', sub_module: 'milking_statuses'}
        ];
    }

    $.each(autocomplete_fields, function () {
        npp.initiateAutocomplete(this.field, this.sub_module)
    });
};

/**
 * Initiate the autocomplete settings for the different fields
 *
 * @param   {string}    input_id    The id of the element to implement the autocomplete on
 * @param   {string}    sub_module  The identifier of the action that we are doing
 * @returns {undefined}
 */
NppDash.prototype.initiateAutocomplete = function (input_id, sub_module) {
    console.log('Set autocomplete for ' + input_id);
    var settings = {
        serviceUrl: $SCRIPT_ROOT + "/autocomplete", minChars: 1, maxHeight: 400, width: 190,
        zIndex: 9999, deferRequestBy: 300, //miliseconds
        params: {resource: sub_module}, //aditional parameters
        noCache: true, //default is false, set to true to disable caching
        onSelect: npp.confirmSelection,
        formatResult: npp.fnFormatResult,
        visibleSuggestions: true
    };

    $('#' + input_id).autocomplete(settings);
};

/**
 * Starts the process of editing the farmer details
 */
NppDash.prototype.startFarmerEditing = function(){
   // update the fields with the current farmer details
   console.log('Starting to edit the farmer...');
   var f = npp.currentFarmer.farmer;
   $('#farmer_name').val(f.farmer_name);
   $('#hub').val(f.hub);
   $('#mobile_no').val(f.mobile_no);
   $('#mobile_no1').val(f.mobile_no2);
   $('#cf').val(f.cf);
   $('#locale').val(f.locale);
   $('#gps_lat').val(f.gps_latitude);
   $('#gps_lon').val(f.gps_longitude);
   if(f.is_active === 'Yes'){
       $('#is_active_yes').prop('checked', true);
   }
   else if(f.is_active === 'No'){
       $('#is_active_no').prop('checked', true);
   }
   $('#edit_farmer').removeClass('hidden');
   npp.configureEditAutocomplete('farmer');

    // validate and save the entered data when the user clicks on submit
    $('#farmer_editing').validator().on('submit', function (e) {
        if (e.isDefaultPrevented()) {
            console.log('We have an invalid form');
        } else {
            console.log('All looks good... so create the ajax request');
            var data = $('#farmer_editing').serializeObject();
            data.farmer_id = npp.curFarmerId;

            var request = $.ajax({
                type: "POST", url: $SCRIPT_ROOT + "/save_farmer", contentType: "application/json", dataType: 'json', data: JSON.stringify(data),
                error: npp.communicationError,
                success: function (data) {
                    if (data.error) {
                        npp.showNotification(data.msg, 'error');
                        return;
                    } else {
                        $('#farmer_editing').clearForm();
                        $('#edit_farmer').addClass('hidden');
                        console.log('All saved successfully');
                        npp.showNotification(data.msg, 'success');
                    }
                }
            });
            return false;
        }
    });
};

/**
 * Start editing the cow details
 */
NppDash.prototype.startCowEditing = function () {
    // update the fields with the cow details
    console.log('Starting to edit the cow...');
    var cow = $('#grid0').jqxGrid('getrowdata', this.id);
    $('#cow_name').val(cow.cow_name);
    $('#ear_tag').val(cow.ear_tag);
    $('#dob').val(cow.dob);
    $('#breed_group').val(cow.breed_group);
    $('#sire').val(cow.sire);
    $('#dam').val(cow.dam);
    if (cow.is_active === 'Yes'){
        $('#active_cow_yes').prop('checked', true);
    }
    else if (cow.is_active === 'No'){
        $('#active_cow_no').prop('checked', true);
    }

    // gender related fields
    if (cow.sex === 'Female'){
        $('#female').prop('checked', true);
        $('#parity').val(cow.parity);
        $('#milking_status').val(cow.is_milking);
        if (cow.is_incalf === 'Yes'){
            $('#incalf_yes').prop('checked', true);
        }
        else if (cow.is_incalf === 'No'){
            $('#incalf_no').prop('checked', true);
        }
    }
    else if (cow.sex === 'Male'){
        $('#male').prop('checked', true);
        $('#parity').prop('disabled', true);
        $('#milking_status').prop('disabled', true);
        $('[name=is_incalf]').prop('disabled', true);
    }

    npp.currentCow = cow;

    $('#edit_cow').removeClass('hidden');
    npp.configureEditAutocomplete('cow');

    // validate and save the entered data when the user clicks on submit
    $('#cow_editing').validator().on('submit', function (e) {
        if (e.isDefaultPrevented()) {
            console.log('We have an invalid form');
        } else {
            console.log('All looks good... so create the ajax request');
            var data = $('#cow_editing').serializeObject();
            data.cow_id = npp.currentCow.cow_id;
            data.farmer_id = npp.currentFarmer.farmer.farmer_id;

            var request = $.ajax({
                type: "POST", url: $SCRIPT_ROOT + "/save_cow", contentType: "application/json", dataType: 'json', data: JSON.stringify(data),
                error: npp.communicationError,
                success: function (data) {
                    if (data.error) {
                        npp.showNotification(data.msg, 'error');
                        return;
                    } else {
                        $('#cow_editing').clearForm();
                        $('#edit_cow').addClass('hidden');
                        console.log('All saved successfully..now refresh the page');
                        npp.editFarmer();
                        npp.showNotification(data.msg, 'success');
                    }
                }
            });
            return false;
        }
    });
};


/**
 * Show a notification on the page
 *
 * @param   message     The message to be shown
 * @param   type        The type of message
 */
NppDash.prototype.showNotification = function(message, type, autoclose){
   if(type === undefined) { type = 'error'; }
   if(autoclose === undefined) { autoclose = true; }

   $('#messageNotification div').html(message);
   if($('#messageNotification').jqxNotification('width') === undefined){
      $('#messageNotification').jqxNotification({
         width: 350, position: 'top-right', opacity: 0.9,
         autoOpen: false, animationOpenDelay: 800, autoClose: autoclose, template: type
       });
   }
   else{ $('#messageNotification').jqxNotification({template: type}); }

   $('#messageNotification').jqxNotification('open');
};

var npp = new NppDash();

/**
 * A jQuery addition to add Regex selection capacity
 */
jQuery.expr[':'].regex = function (elem, index, match) {
    var matchParams = match[3].split(','),
          validLabels = /^(data|css):/,
          attr = {
              method: matchParams[0].match(validLabels) ?
                    matchParams[0].split(':')[0] : 'attr',
              property: matchParams.shift().replace(validLabels, '')
          },
    regexFlags = 'ig',
          regex = new RegExp(matchParams.join('').replace(/^\s+|\s+$/g, ''), regexFlags);
    return regex.test(jQuery(elem)[attr.method](attr.property));
}