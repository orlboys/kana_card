document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".card-container").forEach(function (cardContainer) {
        cardContainer.addEventListener("click", function () {
            cardContainer.classList.toggle("flipped");
        });
    });
});