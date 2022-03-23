const phoneInputField = document.querySelector("#field-phonenumber");
const phoneInput = window.intlTelInput(phoneInputField, {
    preferredCountries: ["mw"],
    utilsScript:
        "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
});

const error = document.querySelector(".phonenumber.alert-error");

function process(event) {

    const phoneNumber = phoneInput.getNumber();
    const emptyNumber = phoneNumber === "";
    if (emptyNumber || phoneInput.isValidNumber()) {
        phoneInputField.value = phoneNumber;
    } else {
        error.style.display = "";
        error.innerHTML = `Invalid phone number. Please verify your input.`;
        event.preventDefault();
    }
}
