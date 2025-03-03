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

// FLASHCARD ADDING FUNCTIONALITY //
let flashcardCount = 1;

function addFlashcard() {
    flashcardCount++;
    document.getElementById('flashcard_count').value = flashcardCount; // Update the hidden input field
    const container = document.getElementById('flashcards-container');
    const flashcardDiv = document.createElement('div');
    flashcardDiv.className = 'flashcard';
    flashcardDiv.innerHTML = `
        <label for="flashcard_question_${flashcardCount}">Question:</label>
        <input type="text" name="flashcard_question_${flashcardCount}" id="flashcard_question_${flashcardCount}" placeholder="Question" required>
        <label for="flashcard_answer_${flashcardCount}">Answer:</label>
        <input type="text" name="flashcard_answer_${flashcardCount}" id="flashcard_answer_${flashcardCount}" placeholder="Answer" required>
        <input type="button" value="Remove" onclick="removeFlashcard(this)">
    `;
    container.appendChild(flashcardDiv);
}

function removeFlashcard(button) {
    button.parentElement.remove();
    flashcardCount--;
    document.getElementById('flashcard_count').value = flashcardCount; // Update the hidden input field
}