// guide.js for Noteify Guide Page

document.addEventListener('DOMContentLoaded', function() {
  console.log('Welcome to the Noteify Guide!');

  // Initialize search functionality
  initializeSearch();
  
  // Initialize button handlers
  initializeButtons();
  
  // Initialize smooth scrolling
  initializeSmoothScrolling();
  
  // Initialize video placeholder
  initializeVideoPlaceholder();
});

function initializeSearch() {
  const searchInput = document.querySelector('.search-input');
  const faqItems = document.querySelectorAll('.faq-item');
  
  if (searchInput) {
    searchInput.addEventListener('input', function(e) {
      const searchTerm = e.target.value.toLowerCase();
      
      faqItems.forEach(item => {
        const question = item.querySelector('strong').textContent.toLowerCase();
        const answer = item.querySelector('p').textContent.toLowerCase();
        
        if (question.includes(searchTerm) || answer.includes(searchTerm)) {
          item.style.display = 'block';
          item.style.opacity = '1';
        } else {
          item.style.opacity = '0.3';
        }
      });
    });
  }
}

function initializeButtons() {
  // Action buttons
  const actionButtons = document.querySelectorAll('.action-button');
  
  actionButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      const buttonText = this.textContent.trim();
      
      // Add click animation
      this.style.transform = 'scale(0.95)';
      setTimeout(() => {
        this.style.transform = '';
      }, 150);
      
      // Handle different button actions
      switch(buttonText) {
        case 'Install Extension':
          console.log('Opening extension installation...');
          // Add your extension installation logic here
          break;
        case 'Connect Notion':
          console.log('Opening Notion connection...');
          // Add your Notion connection logic here
          break;
        case 'Try It Now':
          console.log('Opening capture demo...');
          // Add your capture demo logic here
          break;
        case 'Open Dashboard':
          console.log('Opening dashboard...');
          // Add your dashboard opening logic here
          break;
        case 'Watch Tutorial':
          console.log('Opening video tutorial...');
          // Add your video tutorial logic here
          break;
        case 'Contact Support':
          console.log('Opening support contact...');
          // Add your support contact logic here
          break;
        case 'Documentation':
          console.log('Opening documentation...');
          // Add your documentation opening logic here
          break;
        default:
          console.log('Button clicked:', buttonText);
      }
    });
  });
}

function initializeSmoothScrolling() {
  // Smooth scroll for anchor links (future-proofing)
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
  
  // Add smooth scrolling to step navigation
  const steps = document.querySelectorAll('.step');
  steps.forEach((step, index) => {
    step.addEventListener('click', function() {
      const nextStep = steps[index + 1];
      if (nextStep) {
        nextStep.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  });
}

function initializeVideoPlaceholder() {
  const videoPlaceholder = document.querySelector('.video-placeholder');
  const watchButton = document.querySelector('.video-container .action-button');
  
  if (videoPlaceholder) {
    videoPlaceholder.addEventListener('click', function() {
      console.log('Video placeholder clicked - opening tutorial video...');
      // Add your video opening logic here
      
      // Add a subtle animation
      this.style.transform = 'scale(0.98)';
      setTimeout(() => {
        this.style.transform = '';
      }, 200);
    });
  }
  
  if (watchButton) {
    watchButton.addEventListener('click', function() {
      console.log('Watch tutorial button clicked...');
      // Add your video opening logic here
    });
  }
}

// Add some additional utility functions
function showNotification(message, type = 'info') {
  // Create a simple notification system
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 1000;
    animation: slideIn 0.3s ease;
  `;
  
  if (type === 'success') {
    notification.style.background = '#6CD97B';
  } else if (type === 'error') {
    notification.style.background = '#FF6B6B';
  } else {
    notification.style.background = '#2EC4F1';
  }
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 300);
  }, 3000);
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
`;
document.head.appendChild(style); 