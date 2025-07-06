// Common filter functionality for all pages
function initializeFilters() {
    // Initialize datepickers
    $('.datepicker').datepicker({
        format: 'dd-mm-yyyy',
        autoclose: true
    });

    // Initialize select2 for dropdowns
    $('.select2').select2({
        theme: 'bootstrap4',
        placeholder: 'Select an option',
        allowClear: true
    });

    // Common filter function
    window.filterTable = function() {
        var table = $('#dataTable').DataTable();
        
        // Get all filter values
        var filters = {};
        $('.filter-input').each(function() {
            var value = $(this).val();
            var column = $(this).data('column');
            if (value) {
                filters[column] = value;
            }
        });

        // Apply filters
        table.columns().every(function() {
            var column = this;
            var columnIndex = column.index();
            
            if (filters[columnIndex] !== undefined) {
                var filterValue = filters[columnIndex].toLowerCase();
                
                column.search(filterValue, true, false).draw();
            }
        });
    }

    // Bind filter event to all filter inputs
    $('.filter-input').on('change keyup', function() {
        filterTable();
    });

    // Clear filters
    $('#clearFilters').on('click', function() {
        $('.filter-input').val('').trigger('change');
        filterTable();
    });
}

// Export date formatter
function formatDate(date) {
    if (!date) return '';
    var d = new Date(date);
    var day = ('0' + d.getDate()).slice(-2);
    var month = ('0' + (d.getMonth() + 1)).slice(-2);
    var year = d.getFullYear();
    return day + '-' + month + '-' + year;
}

// Initialize on document ready
$(document).ready(function() {
    initializeFilters();
}); 