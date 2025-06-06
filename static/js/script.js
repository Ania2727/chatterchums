console.log("JavaScript Loaded Successfully!");

document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".interest-btn");

    buttons.forEach(button => {
        button.addEventListener("click", function () {
            button.classList.toggle("selected");
        });
    });

    document.querySelector(".continue-btn").addEventListener("click", function () {
        const selectedInterests = Array.from(document.querySelectorAll(".interest-btn.selected"))
            .map(btn => btn.innerText);

        console.log("Selected Interests:", selectedInterests);

        const csrfToken = document.getElementById("csrf_token").value;

        fetch('/users/forum-recommendations/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken 
            },
            credentials: 'include',  
            body: JSON.stringify({ interests: selectedInterests }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log("Forum Recommendations:", data.recommendations);

                // Store recommendations in sessionStorage or render them on the page
                sessionStorage.setItem("recommendedForums", JSON.stringify(data.recommendations));

                window.location.href = "/users/explore/";
            } else {
                console.error("Error in response:", data.error);
            }
        })
        .catch(error => console.error("Fetch error:", error));
    });
});
