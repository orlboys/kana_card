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