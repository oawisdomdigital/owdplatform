//Javascript for adspost photo id
document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById('exampleModal');
    modal.addEventListener('show.bs.modal', function (event) {
        var button = event.relatedTarget; // Button that triggered the modal
        var photoId = button.getAttribute('data-photo-id'); // Extract info from data-* attributes
        var input = document.getElementById('photoId');
        input.value = photoId; // Update the hidden input field
    });
});


// JavaScript code for handling interactions (e.g., like, subscribe, comment)
document.addEventListener('DOMContentLoaded', function () {
    // Example code for copying share link to clipboard
    document.getElementById('copyLinkButton').addEventListener('click', function () {
        var shareLink = document.getElementById('shareLink').innerText;
        navigator.clipboard.writeText(shareLink).then(function () {
            alert('Link copied to clipboard!');
        }, function (err) {
            console.error('Unable to copy link: ', err);
        });
    });

    // Example code for handling like/unlike button click
    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function () {
            var postId = this.dataset.postId;
            // Implement logic to toggle like/unlike and update UI
            // Example: Simulate toggle effect
            if (this.textContent.trim() === 'Like') {
                this.textContent = 'Unlike';
                this.classList.remove('btn-light');
                this.classList.add('btn-primary');
            } else {
                this.textContent = 'Like';
                this.classList.remove('btn-primary');
                this.classList.add('btn-light');
            }
        });
    });

    // Example code for handling subscribe/unsubscribe button click
    document.querySelectorAll('.subscribe-button').forEach(button => {
        button.addEventListener('click', function () {
            var authorId = this.dataset.authorId;
            // Implement logic to toggle subscribe/unsubscribe and update UI
            // Example: Simulate toggle effect
            if (this.textContent.trim() === 'Subscribe') {
                this.textContent = 'Unsubscribe';
                this.classList.remove('btn-light');
                this.classList.add('btn-primary');
            } else {
                this.textContent = 'Subscribe';
                this.classList.remove('btn-primary');
                this.classList.add('btn-light');
            }
        });
    });

    // Example code for displaying comments modal
    document.querySelectorAll('.view-comments-button').forEach(button => {
        button.addEventListener('click', function () {
            var postId = this.dataset.postId;
            // Implement logic to fetch comments via AJAX and populate modal
            // Example: Simulate loading comments
            var commentList = document.getElementById('commentList');
            commentList.innerHTML = '<li class="list-group-item">Comment 1</li><li class="list-group-item">Comment 2</li>';
        });
    });

    // Example code for sharing post modal
    document.querySelectorAll('.share-button').forEach(button => {
        button.addEventListener('click', function () {
            var postId = this.dataset.postId;
            // Implement logic to share post via modal
            // Example: Display share modal
            $('#shareModal').modal('show');
        });
    });
});


// Script to pop up modal based on the photo id
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('adType').addEventListener('change', function () {
        var selectedOption = this.value;
        var options = document.querySelectorAll('.ad-options');
        options.forEach(function (option) {
            option.style.display = 'none';
        });
        if (selectedOption === 'more_messages_whatsapp') {
            document.getElementById('whatsappOptions').style.display = 'block';
        } else if (selectedOption === 'more_website_visitors') {
            document.getElementById('websiteVisitorsOptions').style.display = 'block';
        } else if (selectedOption === 'more_calls') {
            document.getElementById('callsOptions').style.display = 'block';
        } else if (selectedOption === 'more_followers') {
            document.getElementById('followersOptions').style.display = 'block';
        } else if (selectedOption === 'grow_customer_base') {
            document.getElementById('customerBaseOptions').style.display = 'block';
        }
    });
});


// Data purchase
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

$(document).ready(function () {
    $('#network').change(function () {
        let network = $(this).val();
        let options = [];

        switch (network) {
            case 'MTN':
                options = [
                    '500mb (N200) (30 Days)',
                    '1gb (N400)',
                    '2gb (N700) (30 Days)',
                    '3gb (N1,000) (30 Days)',
                    '5gb (N1500) (30 Days)',
                    '10gb (N3,000) (30 Days)'
                ];
                break;
            case 'AIRTEL':
                options = [
                    '300mb (N100) (30 Days)',
                    '500mb (N200) (30 Days)',
                    '1gb (N300) (30 Days)',
                    '2gb (N700) (30 Days)',
                    '5gb (N1,600) (30 Days)',
                    '10gb (N3,000) (30 Days)'
                ];
                break;
            case 'GLO':
                options = [
                    '500mb (N200) (30 Days)',
                    '1gb (N400)',
                    '2gb (N800) (30 Days)',
                    '3gb (N1,200) (30 Days)',
                    '5gb (N1,800) (30 Days)',
                    '10gb (N3,500) (30 Days)'
                ];
                break;
            case '9MOBILE':
                options = [
                    '500mb (N200) (30 Days)',
                    '1gb (N400)',
                    '2gb (N800) (30 Days)',
                    '3gb (N1,100) (30 Days)',
                    '5gb (N1,500) (30 Days)',
                    '10gb (N3,000) (30 Days)'
                ];
                break;
            default:
                options = [];
                break;
        }

        // Clear previous options
        $('#dataPlan').empty();

        // Append new options
        if (options.length > 0) {
            options.forEach(option => {
                $('#dataPlan').append(new Option(option, option));
            });
        }
    });

    $('#submitBtn').click(function () {
        // Perform form submission via AJAX
        $.ajax({
            type: 'POST',
            url: $('#serviceForm').attr('action'),
            data: $('#serviceForm').serialize(),
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            success: function (response) {
                // Close the modal
                $('#serviceModal').modal('hide');
                // Check if there's a redirect_url in the response
                if (response.redirect_url) {
                    // Redirect the user to Paystack
                    window.location.replace(response.redirect_url);
                } else {
                    // Show success message if no redirect_url
                    alert('Purchase Successful! Thank you for your purchase.');
                }
            },
            error: function (error) {
                // Show error message
                alert('An error occurred. Please try again.');
            }
        });
    });
});




