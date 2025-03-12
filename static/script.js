// FLASHCARDS //

// Card Flip Functionality
document.addEventListener("DOMContentLoaded", function () { // Wait for the DOM to be fully loaded
    document.querySelectorAll(".card-container").forEach(function (cardContainer) { // For each card container
        cardContainer.addEventListener("click", function () { // Listen for when the card container is clicked
            cardContainer.classList.toggle("flipped"); // change the 'flipped' class on the card container
        });
    });
});

// MODALS //

// Ideally, polymorphism would work here. However, it isn't, so we're doing this instead
// Modal Functionality for User Editing
function openUserEditModal(id, username, f_name, l_name, email, role) { // Opens the edit modal with the given user data
    document.getElementById('edit_index').value = id;
    document.getElementById('new_username').value = username;
    document.getElementById('new_first_name').value = f_name;
    document.getElementById('new_last_name').value = l_name;
    document.getElementById('new_email').value = email;
    document.getElementById('new_role').value = role;
    var editUserModal = new bootstrap.Modal(document.getElementById('editUserModal'));
    editUserModal.show();
}

function closeUserEditModal() { // Closes the edit modal
    var editUserModal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
    editUserModal.hide();
}

// Modal Functionality for List Editing
function openListEditModal(listId, listName) { // Opens the edit modal with the given list data
    document.getElementById('edit_index').value = listId;
    document.getElementById('new_listname').value = listName;
    var editListModal = new bootstrap.Modal(document.getElementById('editListModal'));
    editListModal.show();
}

function closeListEditModal() { // Closes the edit modal
    var editListModal = bootstrap.Modal.getInstance(document.getElementById('editListModal'));
    editListModal.hide();
}

// Modal Functionality for MFA Verification
function openMfaModal() { // Opens the MFA modal
    var mfaModal = new bootstrap.Modal(document.getElementById('verifyMfaModal'));
    mfaModal.show();
}

function closeMfaModal() { // Closes the MFA modal
    var mfaModal = bootstrap.Modal.getInstance(document.getElementById('verifyMfaModal'));
    mfaModal.hide();
}

// Delete User Modal (Confirmation)
function openUserDeleteModal(id) {
    console.log('Setting delete index to:', id); // debugging
    document.getElementById('delete-index').value = id;
    var modalEl = document.getElementById('deleteUserModal');
    var deleteUserModal = new bootstrap.Modal(modalEl);
    $('#deleteUserModal').modal('show') // Show the modal - JQuery syntax here because Bootstrap's modal() function doesn't work
}

// Delete List Modal (Confirmation)
function openListDeleteModal(id) {
    console.log('Setting delete index to:', id); // debugging
    document.getElementById('delete-index').value = id;
    var modalEl = document.getElementById('deleteListModal');
    var deleteListModal = new bootstrap.Modal(modalEl);
    $('#deleteListModal').modal('show') // Show the modal - JQuery syntax here because Bootstrap's modal() function doesn't work
}



// FLASHCARD ADDING FUNCTIONALITY //
function addFlashcard() {
    let container = document.getElementById('flashcards-container');
    let index = container.children.length + 1; // Get current count of flashcards

    let flashcardDiv = document.createElement('div'); // Create a new flashcard div
    flashcardDiv.className = 'flashcard-form my-3';
    flashcardDiv.innerHTML = `
        <div class="form-group">
            <label>Question ${index}:</label>
            <input type="text" class="form-control" name="flashcards-${index}-question" required>
        </div>
        <div class="form-group">
            <label>Answer ${index}:</label>
            <input type="text" class="form-control" name="flashcards-${index}-answer" required>
        </div>
        <button type="button" class="btn btn-danger" onclick="removeFlashcard(this)">Remove</button>
    `;

    container.appendChild(flashcardDiv); // Place the newly created flashcard form query in the question container
}

function removeFlashcard(button) {
    button.parentElement.remove(); // Remove the flashcard

    // Re-index all remaining flashcards
    document.querySelectorAll('.flashcard-form').forEach((flashcard, i) => {
        let newIndex = i + 1; // New index for the flashcard - is 1-based therefore +1
        let labels = flashcard.querySelectorAll("label");
        labels[0].textContent = `Question ${newIndex}:`; 
        labels[1].textContent = `Answer ${newIndex}:`;

        let inputs = flashcard.querySelectorAll("input");
        inputs[0].name = `flashcards-${newIndex}-question`;
        inputs[0].id = `flashcards-${newIndex}-question`;
        inputs[1].name = `flashcards-${newIndex}-answer`;
        inputs[1].id = `flashcards-${newIndex}-answer`;
    });
}

// SEARCH FUNCTIONALITY //

function searchListTable() {
    // Get the input field and its value
    var input = document.getElementById('search');
    var filter = input.value.toLowerCase();
    
    // Get the table and its rows
    var table = document.querySelector('.listList');
    var rows = table.getElementsByTagName('tr');
    
    // Loop through all table rows (except the first, which contains table headers)
    var found = false;
    for (var i = 1; i < rows.length; i++) {
        var cells = rows[i].getElementsByTagName('td'); // Get all cells in the row
        var match = false;
        
        // Loop through all cells in the row
        for (var j = 0; j < cells.length; j++) {
            if (cells[j]) { // If the cell exists
                var cellValue = cells[j].textContent || cells[j].innerText; // Get the cell's text content
                if (cellValue.toLowerCase().indexOf(filter) > -1) { // If the cell's text content contains the filter
                    match = true; // Set match to true and break the loop
                    break;
                }
            }
        }
        
        // Show or hide the row based on the match
        if (match) {
            rows[i].style.display = '';
            found = true;
        } else {
            rows[i].style.display = 'none';
        }
    }
    
    // Show or hide the "No results found" message
    var searchError = document.getElementById('search-error');
    if (found) {
        searchError.style.display = 'none';
    }
    else {
        searchError.style.display = '';
    }
}

// User Search Functionality - same as above, but for the user table
function searchUserTable() {
    var input = document.getElementById('search');
    var filter = input.value.toLowerCase();

    var table = document.querySelector('.userList');
    var rows = table.getElementsByTagName('tr');

    var found = false;
    for (var i = 1; i < rows.length; i++) {
        var cells = rows[i].getElementsByTagName('td');
        var match = false;

        for (var j = 0; j < cells.length; j++) {
            if (cells[j]) {
                var cellValue = cells[j].textContent || cells[j].innerText;
                if (cellValue.toLowerCase().indexOf(filter) > -1) {
                    match = true;
                    break;
                }
            }
        }

        if (match) {
            rows[i].style.display = '';
            found = true;
        } else {
            rows[i].style.display = 'none';
        }
    }

    var searchError = document.getElementById('search-error');
    if (found) {
        searchError.style.display = 'none';
    } 
    else {
        searchError.style.display = '';
    }

    // Show or hide the "No results found" message
    var searchError = document.getElementById('search-error');
    if (found) {
        searchError.style.display = 'none';
    }
    else {
        searchError.style.display = '';
    }
}

// ALERT FUNCTIONALITY //

// Alert Dismissal
document.addEventListener("DOMContentLoaded", function () { // Wait for the DOM to be fully loaded
    setTimeout(function () { // After 5 seconds
        document.querySelectorAll('.alert').forEach(function (alert) { 
            alert.classList.remove('show'); // Remove the 'show' class from the alert
            alert.classList.add('fade'); // Add the 'fade' class to the alert
            setTimeout(function () { 
                alert.remove(); // Remove the alert from the DOM
            }, 1000); // After 1 second
        } ); 
    }, 5000); // Begin the fading process after 5 seconds
});
