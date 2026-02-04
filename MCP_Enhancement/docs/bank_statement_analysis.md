# Bank Statement Analysis App

## Overview

This Streamlit application enables users to upload their bank statements in PDF format and receive a comprehensive analysis of their transactions. The app extracts transaction data from the uploaded statement, categorizes the expenses, computes key financial metrics, and determines loan eligibility using a pre-trained Random Forest model. Additionally, it provides visualizations to help users understand their spending habits.

## Features

- **PDF Upload**: Users can easily upload their bank statements in PDF format.
- **PDF Parsing**: Extracts text from the uploaded PDF.
- **Transaction Processing**: Identifies and processes transaction details including date, description, amount, and balance.
- **Expense Categorization**: Categorizes transactions into predefined categories like Credits, Payments, Bank Charges, etc.
- **Key Metrics Calculation**: Computes average daily expense, total expense, maximum expense, minimum expense, and the number of transactions.
- **Loan Eligibility Prediction**: Uses a Random Forest model to predict loan eligibility based on transaction history.
- **Visualizations**: Provides bar charts, pie charts, and line graphs to visualize expense distribution and trends.

## How It Works

1. **PDF Upload**
   - Users upload their bank statement in PDF format using the file uploader interface.

2. **PDF Parsing**
   - The app extracts text from the PDF document using the `pdfplumber` library.

3. **Transaction Processing**
   - Extracted text is processed to identify individual transactions, capturing details such as date, description, amount, and balance.

4. **Expense Categorization**
   - Transactions are categorized based on their descriptions into predefined categories like Payments, Credits, Bank Charges, etc.

5. **Key Metrics Calculation**
   - The app calculates various financial metrics including average daily expense, total expense, maximum and minimum expense, and the number of transactions.

6. **Loan Eligibility Prediction**
   - A Random Forest model is used to predict loan eligibility based on features extracted from transaction data.

7. **Visualizations**
   - The app generates visualizations such as bar charts, pie charts, and line graphs to represent expense distribution and trends.

8. **Hiding Streamlit Components**
   - Customizes the UI by hiding default Streamlit components like the menu and footer for a cleaner look.
     
## Prerequisites

- Python 3.7 or higher
- `pip` (Python package installer)
    
## Usage

1. Launch the app in your browser.
2. Upload a PDF bank statement.
3. Review the extracted transactions and categorized expenses.
4. View key metrics and visualizations.
5. Check loan eligibility based on the analyzed data.

## Dependencies

- `streamlit`: For creating the web application interface.
- `pdfplumber`: For extracting text from PDF files.
- `fitz` (PyMuPDF): For additional PDF processing capabilities, such as extracting images or complex text layouts.
- `re`: For processing text and extracting transaction details.
- `pandas`: For data manipulation and analysis.
- `plotly`: For creating interactive visualizations.
- `sklearn`: For building and using the Random Forest model.

BLOG- https://link.medium.com/aoQxUW4gFMb