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

// Ideally, polymorphism would work here. However, it isn't, so we're doing this instead :)
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

// FLASHCARD ADDING FUNCTIONALITY //
let flashcardCount = 1;

function addFlashcard() {
    flashcardCount++;
    document.getElementById('flashcard_count').value = flashcardCount; // Update the hidden input field
    const container = document.getElementById('flashcards-container');
    const flashcardDiv = document.createElement('div');
    flashcardDiv.className = 'flashcards-container';
    flashcardDiv.innerHTML = `
        <div class="flashcard-form my-3">
            <div class="form-group">
                <label for="flashcard_question_${flashcardCount}">Question ${flashcardCount}:</label>
                <input type="text" class="form-control" name="flashcard_question_${flashcardCount}" id="flashcard_question_${flashcardCount}" placeholder="Question" required>
            </div>
            <div class="form-group">
                <label for="flashcard_answer_${flashcardCount}">Answer ${flashcardCount}:</label>
                <input type="text" class="form-control" name="flashcard_answer_${flashcardCount}" id="flashcard_answer_${flashcardCount}" placeholder="Answer" required>
            </div>
            <button type="button" class="btn btn-danger" onclick="removeFlashcard(this)">Remove</button>
        </div>
    `;
    container.appendChild(flashcardDiv);
}

function removeFlashcard(button) {
    button.parentElement.remove();
    flashcardCount--;
    document.getElementById('flashcard_count').value = flashcardCount; // Update the hidden input field
}

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
        var cells = rows[i].getElementsByTagName('td');
        var match = false;
        
        // Loop through all cells in the row
        for (var j = 0; j < cells.length; j++) {
            if (cells[j]) {
                var cellValue = cells[j].textContent || cells[j].innerText;
                if (cellValue.toLowerCase().indexOf(filter) > -1) {
                    match = true;
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
}

// Alert Dismissal

document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            alert.classList.remove('show');
            alert.classList.add('fade');
            setTimeout(function () {
                alert.remove();
            }, 1000);
        } );

    }, 5000);
});
