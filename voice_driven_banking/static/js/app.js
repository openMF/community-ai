document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const loginSection = document.getElementById('login-section');
    const registerSection = document.getElementById('register-section');
    const bankingSection = document.getElementById('banking-section');
    const userInfo = document.getElementById('user-info');
    const usernameSpan = document.getElementById('username');
    
    const loginForm = document.getElementById('login-form');
    const loginButton = document.getElementById('login-button');
    const registerForm = document.getElementById('register-form');
    const registerButton = document.getElementById('register-button');
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');
    
    const logoutBtn = document.getElementById('logout-btn');
    const recordBtn = document.getElementById('record-btn');
    const recordText = document.getElementById('record-text');
    const recordingIndicator = document.getElementById('recording-indicator');
    const languageSelect = document.getElementById('language-select');
    const examplePhrases = document.getElementById('example-phrases');
    
    const resultSection = document.getElementById('result-section');
    const recognizedText = document.getElementById('recognized-text');
    const preprocessedText = document.getElementById('preprocessed-text');
    const detectedIntent = document.getElementById('detected-intent');
    const responseMessage = document.getElementById('response-message');
    const balanceContainer = document.getElementById('balance-container');
    const balanceInfo = document.getElementById('balance-info');
    const transactionContainer = document.getElementById('transaction-container');
    const transactionsBody = document.getElementById('transactions-body');
    
    // App state
    let isRecording = false;
    let mediaRecorder;
    let audioChunks = [];
    let currentUser = JSON.parse(localStorage.getItem('user'));
    let isProcessing = false; // Track if we're currently processing a request
    
    // Debounce function to prevent multiple rapid button clicks
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Set button state
    function setButtonState(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            button.classList.add('loading');
        } else {
            button.disabled = false;
            button.classList.remove('loading');
        }
    }
    
    // Show toast message
    function showToast(message, type = 'success') {
        // Remove any existing toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Create new toast
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Automatically remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }
    
    // Check if user is logged in
    if (currentUser) {
        showBankingInterface();
    }
    
    // Event listeners for auth
    showRegisterLink.addEventListener('click', function(e) {
        e.preventDefault();
        // Smooth transition
        loginSection.style.opacity = 0;
        setTimeout(() => {
            loginSection.classList.add('hidden');
            registerSection.classList.remove('hidden');
            setTimeout(() => {
                registerSection.style.opacity = 1;
            }, 10);
        }, 300);
    });
    
    showLoginLink.addEventListener('click', function(e) {
        e.preventDefault();
        // Smooth transition
        registerSection.style.opacity = 0;
        setTimeout(() => {
            registerSection.classList.add('hidden');
            loginSection.classList.remove('hidden');
            setTimeout(() => {
                loginSection.style.opacity = 1;
            }, 10);
        }, 300);
    });
    
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Prevent multiple submissions
        if (isProcessing) return;
        isProcessing = true;
        
        const username = document.getElementById('username-input').value;
        const password = document.getElementById('password-input').value;
        
        // Validate
        if (!username || !password) {
            showToast('Please enter both username and password', 'error');
            isProcessing = false;
            return;
        }
        
        // Visual feedback
        setButtonState(loginButton, true);
        
        // Send login request
        fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentUser = data.user;
                localStorage.setItem('user', JSON.stringify(currentUser));
                showBankingInterface();
                loginForm.reset();
                showToast(`Welcome back, ${currentUser.name}!`);
            } else {
                showToast(data.message || 'Login failed. Please check your credentials.', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred during login. Please try again.', 'error');
        })
        .finally(() => {
            isProcessing = false;
            setButtonState(loginButton, false);
        });
    });
    
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Prevent multiple submissions
        if (isProcessing) return;
        isProcessing = true;
        
        const userData = {
            username: document.getElementById('reg-username').value,
            password: document.getElementById('reg-password').value,
            name: document.getElementById('reg-name').value,
            email: document.getElementById('reg-email').value,
            phone: document.getElementById('reg-phone').value,
            language: document.getElementById('reg-language').value
        };
        
        // Basic validation
        for (const [key, value] of Object.entries(userData)) {
            if (!value) {
                showToast(`Please complete all fields (${key} is missing)`, 'error');
                isProcessing = false;
                return;
            }
        }
        
        // Visual feedback
        setButtonState(registerButton, true);
        
        // Send registration request
        fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Registration successful! Please log in.');
                registerForm.reset();
                // Smooth transition
                registerSection.style.opacity = 0;
                setTimeout(() => {
                    registerSection.classList.add('hidden');
                    loginSection.classList.remove('hidden');
                    setTimeout(() => {
                        loginSection.style.opacity = 1;
                    }, 10);
                }, 300);
            } else {
                showToast(data.message || 'Registration failed. Please try again.', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred during registration. Please try again.', 'error');
        })
        .finally(() => {
            isProcessing = false;
            setButtonState(registerButton, false);
        });
    });
    
    logoutBtn.addEventListener('click', function() {
        // Prevent double clicks
        if (this.disabled) return;
        
        this.disabled = true;
        localStorage.removeItem('user');
        currentUser = null;
        showToast('You have been logged out successfully');
        showLoginInterface();
        setTimeout(() => {
            this.disabled = false;
        }, 1000);
    });
    
    // Voice recording functionality with debounce
    recordBtn.addEventListener('click', debounce(toggleRecording, 300));
    
    function toggleRecording() {
        // Prevent multiple clicks
        if (isProcessing) return;
        
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }
    
    function startRecording() {
        // Reset previous results
        resultSection.classList.add('hidden');
        
        // Prevent multiple recordings
        if (isProcessing) return;
        isProcessing = true;
        
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                isRecording = true;
                recordBtn.classList.add('recording');
                recordText.textContent = 'Stop Recording';
                recordingIndicator.classList.remove('hidden');
                
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = processRecording;
                
                mediaRecorder.start();
                isProcessing = false;
                
                // Auto stop after 10 seconds
                setTimeout(() => {
                    if (isRecording) {
                        stopRecording();
                    }
                }, 10000);
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                showToast('Could not access your microphone. Please check permissions and try again.', 'error');
                isProcessing = false;
            });
    }
    
    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.classList.remove('recording');
            recordText.textContent = 'Start Recording';
            recordingIndicator.classList.add('hidden');
            
            // Stop all audio tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
    }
    
    function processRecording() {
        if (audioChunks.length === 0) {
            showToast('No audio recorded. Please try again.', 'error');
            return;
        }
        
        isProcessing = true;
        
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        
        // Add visual feedback
        recordBtn.disabled = true;
        const processingIndicator = document.createElement('div');
        processingIndicator.textContent = 'Processing your audio...';
        processingIndicator.className = 'processing-indicator';
        recordBtn.parentNode.insertBefore(processingIndicator, recordBtn.nextSibling);
        
        // Create form data
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('user_id', currentUser.id);
        formData.append('language', languageSelect.value);
        
        // Send to server with timeout handling
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        fetch('/api/process-voice', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Server error');
                });
            }
            return response.json();
        })
        .then(data => {
            processingIndicator.remove();
            displayResults(data);
        })
        .catch(error => {
            processingIndicator.remove();
            console.error('Error processing audio:', error);
            
            // Show a user-friendly error message
            let errorMessage = 'An error occurred while processing your voice command';
            
            if (error.name === 'AbortError') {
                errorMessage = 'Request timed out. The server took too long to respond.';
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            resultSection.classList.remove('hidden');
            recognizedText.textContent = 'Could not process speech';
            detectedIntent.textContent = 'None';
            responseMessage.innerHTML = 
                `<div class="error-message">
                    <p><strong>Error:</strong> ${errorMessage}</p>
                    <p>Please try again with a clearer voice recording, or try using a different browser or device.</p>
                </div>`;
            balanceContainer.classList.add('hidden');
            transactionContainer.classList.add('hidden');
        })
        .finally(() => {
            recordBtn.disabled = false;
            isProcessing = false;
        });
    }
    
    function displayResults(data) {
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        
        // Scroll to results if needed
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Display the results section with animation
        resultSection.classList.remove('hidden');
        resultSection.style.opacity = 0;
        setTimeout(() => {
            resultSection.style.opacity = 1;
        }, 10);
        
        // Update recognized text
        recognizedText.textContent = data.recognized_text || 'No speech detected';
        
        // Update preprocessed text
        preprocessedText.textContent = data.preprocessed_text || data.recognized_text || 'No text to process';
        
        // Update detected intent
        detectedIntent.textContent = formatIntentName(data.intent.intent_type);
        
        // Update response message
        if (data.response.success === false) {
            responseMessage.innerHTML = `
                <div class="error-message">
                    <p>${data.response.message || 'Could not complete your request'}</p>
                </div>`;
        } else {
            responseMessage.textContent = data.response.message;
        }
        
        // Handle specific intent displays
        if (data.intent.intent_type === 'check_balance' && data.response.accounts) {
            displayBalances(data.response.accounts);
        } else {
            balanceContainer.classList.add('hidden');
        }
        
        if (data.intent.intent_type === 'transaction_history' && data.response.transactions) {
            displayTransactions(data.response.transactions);
        } else {
            transactionContainer.classList.add('hidden');
        }
    }
    
    function displayBalances(accounts) {
        balanceContainer.classList.remove('hidden');
        balanceInfo.innerHTML = '';
        
        for (const [accountType, account] of Object.entries(accounts)) {
            const balanceElement = document.createElement('div');
            balanceElement.className = 'balance-item';
            
            // Format currency for better display
            const formattedBalance = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: account.currency
            }).format(account.balance);
            
            balanceElement.innerHTML = `
                <div>
                    <strong>${accountType.charAt(0).toUpperCase() + accountType.slice(1)}:</strong>
                    <small>(Account ID: ${account.account_id})</small>
                </div>
                <div>
                    <strong>${formattedBalance}</strong>
                </div>
            `;
            balanceInfo.appendChild(balanceElement);
        }
    }
    
    function displayTransactions(transactions) {
        transactionContainer.classList.remove('hidden');
        transactionsBody.innerHTML = '';
        
        if (transactions.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="4" style="text-align: center;">No recent transactions found</td>
            `;
            transactionsBody.appendChild(row);
            return;
        }
        
        transactions.forEach(transaction => {
            const row = document.createElement('tr');
            
            // Format currency and date for better display
            const formattedAmount = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(transaction.amount);
            
            const date = new Date(transaction.date);
            const formattedDate = new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            }).format(date);
            
            row.innerHTML = `
                <td>${formattedDate}</td>
                <td>${formatTransactionType(transaction.type)}</td>
                <td>${formattedAmount}</td>
                <td>${transaction.description}</td>
            `;
            transactionsBody.appendChild(row);
        });
    }
    
    function formatIntentName(intent) {
        if (!intent) return 'Unknown';
        return intent.split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    function formatTransactionType(type) {
        if (!type) return 'Unknown';
        return type.split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    // Language change handler with debounce
    languageSelect.addEventListener('change', debounce(function() {
        const language = this.value;
        
        // Update example phrases based on language
        updateExamplePhrases(language);
        
        // Save user preference
        if (currentUser) {
            fetch('/api/update-language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    user_id: currentUser.id,
                    language: language
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(`Language preference updated to ${getLanguageName(language)}`);
                    // Update user object in local storage
                    currentUser.language = language;
                    localStorage.setItem('user', JSON.stringify(currentUser));
                }
            })
            .catch(error => {
                console.error('Error updating language:', error);
            });
        }
    }, 300));
    
    function getLanguageName(code) {
        const languages = {
            'en-US': 'English',
            'hi-IN': 'Hindi',
            'ta-IN': 'Tamil'
        };
        return languages[code] || code;
    }
    
    function updateExamplePhrases(language) {
        examplePhrases.innerHTML = '';
        
        // Start with fade-out animation
        examplePhrases.style.opacity = 0;
        
        let phrases;
        if (language === 'hi-IN') {
            phrases = [
                '"मेरा बैलेंस क्या है?"',
                '"जेन को 100 रुपये ट्रांसफर करें"',
                '"मेरे हाल के लेनदेन दिखाएं"'
            ];
        } else if (language === 'ta-IN') {
            phrases = [
                '"என் இருப்பு என்ன?"',
                '"ஜேனுக்கு 100 ரூபாய் அனுப்பு"',
                '"என் சமீபத்திய பரிவர்த்தனைகளைக் காட்டு"'
            ];
        } else {
            // Default to English
            phrases = [
                '"What is my account balance?"',
                '"Transfer 100 dollars to Jane"',
                '"Show my recent transactions"'
            ];
        }
        
        // Create and append list items
        phrases.forEach(phrase => {
            const li = document.createElement('li');
            li.textContent = phrase;
            examplePhrases.appendChild(li);
        });
        
        // Fade back in
        setTimeout(() => {
            examplePhrases.style.opacity = 1;
        }, 300);
    }
    
    function showBankingInterface() {
        // First hide login/register
        loginSection.classList.add('hidden');
        registerSection.classList.add('hidden');
        
        // Then show banking with animation
        bankingSection.style.opacity = 0;
        bankingSection.classList.remove('hidden');
        userInfo.classList.remove('hidden');
        
        setTimeout(() => {
            bankingSection.style.opacity = 1;
        }, 10);
        
        // Set username
        usernameSpan.textContent = currentUser.name;
        
        // Set language preference
        languageSelect.value = currentUser.language || 'en-US';
        updateExamplePhrases(currentUser.language || 'en-US');
    }
    
    function showLoginInterface() {
        // Hide banking
        bankingSection.classList.add('hidden');
        registerSection.classList.add('hidden');
        userInfo.classList.add('hidden');
        resultSection.classList.add('hidden');
        
        // Show login with animation
        loginSection.style.opacity = 0;
        loginSection.classList.remove('hidden');
        
        setTimeout(() => {
            loginSection.style.opacity = 1;
        }, 10);
    }
    
    // Add CSS for toast notifications
    const style = document.createElement('style');
    style.textContent = `
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
            max-width: 350px;
        }
        
        .toast.success {
            background-color: #10b981;
        }
        
        .toast.error {
            background-color: #ef4444;
        }
        
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        /* Add smooth transitions for sections */
        #login-section, #register-section, #banking-section, #result-section, #example-phrases {
            transition: opacity 0.3s ease;
        }
    `;
    document.head.appendChild(style);
    
    // Initialize transition opacity
    loginSection.style.opacity = 1;
    registerSection.style.opacity = 0;
    bankingSection.style.opacity = 0;
});
