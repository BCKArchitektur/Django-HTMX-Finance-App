$(document).ready(function() {
    // Calculate the remaining time for the fixed_preset card
    const totalHoursToday = parseFloat("{{ total_hours_today }}");
    const hoursAssigned = parseFloat("{{ hours_assigned }}");
    const remainingTime = hoursAssigned - totalHoursToday;

    // Ensure remaining time is not negative
    const remainingTimeFormatted = remainingTime > 0 ? remainingTime.toFixed(2) : '0.00';

    // Set the remaining time in the fixed_preset card's hidden input field
    $('.fixed_preset .card').each(function() {
        const card = $(this);
        card.find('input[name="log_time"]').val(remainingTimeFormatted);
    });

    $('.preset-card').each(function() {
        const card = $(this);
        const ItemId = card.data('Item-id');

        if (ItemId) {
            $.ajax({
                url: `/ajax/load-tasks/?Item_id=${ItemId}`,
                method: 'GET',
                success: function(data) {
                    if (data.tasks && data.tasks.length > 0) {
                        const taskContainer = card.find('.task-container');
                        taskContainer.empty(); // Clear any existing buttons

                        data.tasks.forEach(function(task) {
                            const button = $('<button>')
                                .addClass('task-btn')
                                .text(task.task_name)
                                .attr('data-task-id', task.id)
                                .on('click', function() {
                                    $(this).toggleClass('selected');
                                    updateSelectedTasks(card);
                                });

                            taskContainer.append(button);
                        });
                    } else {
                        card.find('.task-container').html("<p>No tasks available</p>");
                    }
                },
                error: function(error) {
                    console.error("Error loading tasks:", error);
                    card.find('.task-container').html("<p>Error loading tasks</p>");
                }
            });
        }

        // Populate form fields with preset data
        card.find('input[name="log_project_name"]').val(card.data('project-name'));
        card.find('input[name="log_contract"]').val(card.data('contract-name'));
        card.find('input[name="log_section"]').val(card.data('section-name'));
        card.find('input[name="log_Item"]').val(card.data('Item-name'));
        card.find('input[name="log_task"]').val(card.find('.task-name').data('task-id'));

        // Update tasks when the custom tasks input field changes
        card.find('input[name="custom_tasks"]').on('input', function() {
            updateSelectedTasks(card);
        });
    });

    function updateSelectedTasks(card) {
        let selectedTasks = [];
        card.find('.task-btn.selected').each(function() {
            selectedTasks.push($(this).text());
        });
        let customTasks = card.find('input[name="custom_tasks"]').val();
        if (customTasks) {
            customTasks = customTasks.split(',').map(task => task.trim()).filter(task => task.length > 0);
            selectedTasks = selectedTasks.concat(customTasks);
        }
        card.find('input[name="log_tasks"]').val(selectedTasks.join(', '));
    }
});


$(document).ready(function() {


    $('#id_log_project_name').change(function() {
        var projectId = $(this).val();
        console.log('Project selected:', projectId);

        $.ajax({
            url: '/ajax/load-contracts/',
            data: { 'project_id': projectId },
            success: function(data) {
                console.log('Contracts loaded:', data);
                $("#id_log_contract").html('<option value="">---------</option>');
                $.each(data.contracts, function(key, value) {
                    $("#id_log_contract").append('<option value="' + value.id + '">' + value.contract_name + '</option>');
                });

                // Fetch and apply user presets
                getUserPresets(projectId);
            }
        });
    });

    $('#id_log_contract').change(function() {
        var contractId = $(this).val();
        console.log('Contract selected:', contractId);
        $.ajax({
            url: '/ajax/load-sections/',
            data: { 'contract_id': contractId },
            success: function(data) {
                console.log('Sections loaded:', data);
                $("#id_log_section").html('<option value="">---------</option>');
                $.each(data.sections, function(key, value) {
                    $("#id_log_section").append('<option value="' + value.id + '">' + value.section_name + '</option>');
                });
            }
        });
    });

    $('#id_log_section').change(function() {
        var sectionId = $(this).val();
        console.log('Section selected:', sectionId);
        $.ajax({
            url: '/ajax/load-Items/',
            data: { 'section_id': sectionId },
            success: function(data) {
                console.log('Items loaded:', data);
                $("#id_log_Item").html('<option value="">---------</option>');
                $.each(data.Items, function(key, value) {
                    $("#id_log_Item").append('<option value="' + value.id + '">' + value.Item_name + '</option>');
                });
            }
        });
    });

    $('#id_log_Item').change(function() {
        var ItemId = $(this).val();
        console.log('Item selected:', ItemId);
        $.ajax({
            url: '/ajax/load-tasks/',
            data: { 'Item_id': ItemId },
            success: function(data) {
                console.log('Tasks loaded:', data);
                let taskContainer = $("#task-buttons-container");
                taskContainer.html('');
                $.each(data.tasks, function(key, value) {
                    let button = $('<div class="task-button"></div>').text(value.task_name).data('taskName', value.task_name);
                    taskContainer.append(button);
                });
                $(".task-button").click(function() {
                    $(this).toggleClass('selected');
                    console.log('Task button clicked:', $(this).data('taskName'));
                    updateSelectedTasks();
                });
            }
        });
    });

    function updateSelectedTasks() {
        let selectedTasks = [];
        $(".task-button.selected").each(function() {
            selectedTasks.push($(this).data('taskName')); // Use task name instead of task ID
        });
        let customTasks = $("#custom-tasks").val().split(',').map(task => task.trim()).filter(task => task.length > 0);
        selectedTasks = selectedTasks.concat(customTasks);
        $("#id_log_tasks").val(selectedTasks.join(',')); // Join as a string of comma-separated values
        console.log('Selected tasks updated:', selectedTasks);
    }

    $("#custom-ttasks").on('input', updateSelectedTasks);

    function getUserPresets(projectId) {
        console.log('Fetching user presets for project:', projectId);
        $.ajax({
            url: '/get-preset-values/',
            data: { 'project_id': projectId },
            success: function(data) {
                console.log('User presets loaded:', data);
                // Update the contract field
                if (data.contract) {
                    updateField('#id_log_contract', data.contract, function() {
                        // Update the section field after contract is set
                        if (data.section) {
                            updateField('#id_log_section', data.section, function() {
                                // Update the Item field after section is set
                                if (data.Item) {
                                    updateField('#id_log_Item', data.Item);
                                }
                            });
                        }
                    });
                }
            }
        });
    }

    function updateField(fieldId, value, callback) {
        console.log('Updating field:', fieldId, 'with value:', value);
        $(fieldId).val(value || '').trigger('change');

        // Wait for the field to be fully updated and for any dependent AJAX calls to complete
        setTimeout(function() {
            console.log('Field updated:', fieldId);
            if (callback) {
                callback();
            }
        }, 250); // Adjust timeout as necessary based on the time it takes for AJAX calls to complete
    }
});

function deleteLog(logId, csrfToken) {
    if (confirm('Are you sure you want to delete this log?')) {
        console.log('Deleting log:', logId);
        fetch(`/delete-log/${logId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        })
        .then(response => {
            if (response.ok) {
                console.log('Log deleted successfully:', logId);
                document.getElementById(`log-${logId}`).remove();
                window.location.reload();  // Use window.location to reload the page
            } else {
                alert('Failed to delete the log.');
                console.error('Failed to delete log:', response.statusText);
            }
        })
        .catch(error => {
            alert('Error deleting log: ' + error);
            console.error('Error deleting log:', error);
        });
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const selects = document.querySelectorAll('#selectbar select');

    selects.forEach(select => {
        select.addEventListener('change', function() {
            // Remove active class from all other selects
            selects.forEach(s => s.classList.remove('active'));
            // Add active class to the currently changed select
            this.classList.add('active');
            console.log('Select changed:', this.id, 'Value:', this.value);
        });
    });
});
