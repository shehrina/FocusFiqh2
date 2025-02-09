document.addEventListener("DOMContentLoaded", () => {
  const progressCircle = document.querySelector(".progress-circle");
  const progressValue = document.querySelector(".progress-value");

  // Set the percentage value dynamically (update this value to see changes)
  const percentage = 80;

  // Validate that the percentage is between 0 and 100
  if (percentage < 0 || percentage > 100) {
    console.error("Percentage value must be between 0 and 100");
    return;
  }

  // Dynamically update the background with a conic-gradient
  // The first color fills from 0% up to the specified percentage,
  // then the rest is filled with a semi-transparent color.
  progressCircle.style.background = `conic-gradient(
    #c084fc 0% ${percentage}%, 
    rgba(255, 255, 255, 0.15) ${percentage}% 100%
  )`;

  // Update the text inside the circle to display the current percentage
  progressValue.textContent = `${percentage}%`;
});
