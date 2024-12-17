const phoneInputField = document.querySelector("#field-phonenumber");
const phoneInput = window.intlTelInput(phoneInputField, {
    preferredCountries: ["mw"],
    formatOnDisplay: false,
    utilsScript:
        "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
});

const error = document.querySelector(".phonenumber.alert-error");

function process() {

    const phoneNumber = phoneInput.getNumber();
    const emptyNumber = phoneNumber === "";
    if (emptyNumber || phoneInput.isValidNumber()) {
        error.innerHTML = ""
        error.style.display = "none";
        phoneInputField.value = phoneNumber;

    } else {
        error.style.display = "";
        error.innerHTML = `Invalid phone number. Please verify your input.`;
    }
}

phoneInputField.onkeyup = process;
