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
function openUserEditModal(id, username, role) { // Opens the edit modal with the given user data
    document.getElementById('edit_index').value = id;
    document.getElementById('new_username').value = username;
    document.getElementById('new_role').value = role;
    document.getElementById('editUserModal').style.display = 'block';
}

function closeUserEditModal() { // Closes the edit modal
    document.getElementById('editUserModal').style.display = 'none';
}

// Modal Functionality for List Editing
function openListEditModal(listId, listName) { // Opens the edit modal with the given list data
    document.getElementById('edit_index').value = listId;
    document.getElementById('new_listname').value = listName;
    document.getElementById('editListModal').style.display = 'block';
}

function closeListEditModal() { // Closes the edit modal
    document.getElementById('editListModal').style.display = 'none';
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