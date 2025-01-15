import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# Function to fetch exchange rate for a given currency code
def get_exchange_rate(currency_code):
    api_url = f"https://v6.exchangerate-api.com/v6/5b5308dec4754102958e17c5/latest/USD"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        if "conversion_rates" in data:
            conversion_rates = data["conversion_rates"]
            return conversion_rates.get(currency_code, None)
        else:
            st.error("Error: Conversion rates not found.")
            return None
    else:
        st.error(f"Error fetching exchange rates: {response.status_code}")
        return None

# Function to calculate monthly payment (fixed-rate mortgage formula)
def calculate_monthly_payment(loan_amount, annual_interest_rate, loan_term_years):
    monthly_interest_rate = annual_interest_rate / 100 / 12
    number_of_payments = loan_term_years * 12
    if monthly_interest_rate > 0:
        monthly_payment = (
            loan_amount * monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments
        ) / ((1 + monthly_interest_rate) ** number_of_payments - 1)
    else:
        # If the interest rate is 0, we use simple division
        monthly_payment = loan_amount / number_of_payments
    return monthly_payment

# Function to generate amortization schedule
def generate_amortization_schedule(loan_amount, annual_interest_rate, loan_term_years, monthly_payment):
    monthly_interest_rate = annual_interest_rate / 100 / 12
    balance = loan_amount
    schedule = []

    for payment_number in range(1, loan_term_years * 12 + 1):
        interest_payment = balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        schedule.append({
            "Payment Number": payment_number,
            "Principal Payment": principal_payment,
            "Interest Payment": interest_payment,
            "Remaining Balance": max(balance, 0),
        })
        if balance <= 0:
            break
    return pd.DataFrame(schedule)

# Streamlit app title
st.title("Loan/Mortgage Calculator with Currency Conversion")

# Step 1: Currency selection
currency_code = st.text_input("Enter Currency Code (e.g., EUR, INR, GBP):", value="USD")

# Initialize session state to store inputs and results
if "loan_amount" not in st.session_state:
    st.session_state.loan_amount = 0
    st.session_state.annual_interest_rate = 0
    st.session_state.loan_term_years = 0
    st.session_state.schedule = pd.DataFrame()
    st.session_state.monthly_payment = 0.0
    st.session_state.exchange_rate_initial = None

# Step 2: User input for loan details
loan_amount = st.number_input(f"Loan Amount in {currency_code}:", min_value=0.0, value=250000.0, step=1000.0)
annual_interest_rate = st.number_input("Annual Interest Rate (%):", min_value=0.0, value=5.0, step=0.1)
loan_term_years = st.number_input("Loan Term (Years):", min_value=1, value=30, step=1)

if st.button("Calculate Loan"):
    # Get the exchange rate for the selected currency (relative to USD)
    exchange_rate_initial = get_exchange_rate(currency_code)
    if exchange_rate_initial is None:
        st.error(f"Could not retrieve exchange rate for {currency_code}.")
    else:
        # Save values to session state
        st.session_state.loan_amount = loan_amount
        st.session_state.annual_interest_rate = annual_interest_rate
        st.session_state.loan_term_years = loan_term_years
        st.session_state.exchange_rate_initial = exchange_rate_initial

        # Step 1: Calculate monthly payment in the selected currency
        monthly_payment_in_selected_currency = calculate_monthly_payment(loan_amount, annual_interest_rate, loan_term_years)

        # Step 2: Generate amortization schedule in the selected currency
        schedule_initial = generate_amortization_schedule(loan_amount, annual_interest_rate, loan_term_years, monthly_payment_in_selected_currency)

        # Save results to session state
        st.session_state.schedule = schedule_initial
        st.session_state.monthly_payment = monthly_payment_in_selected_currency

        # Display results in the selected currency
        st.subheader(f"Results in {currency_code}")
        st.write(f"Monthly Payment: {monthly_payment_in_selected_currency:,.2f} {currency_code}")

        # Display amortization schedule in selected currency
        st.subheader(f"Amortization Schedule in {currency_code}")
        st.dataframe(schedule_initial)

        # Plot amortization schedule in selected currency
        st.subheader(f"Amortization Chart in {currency_code}")
        fig, ax = plt.subplots()
        ax.plot(schedule_initial["Payment Number"], schedule_initial["Remaining Balance"], label=f"Remaining Balance in {currency_code}")
        ax.set_xlabel("Payment Number")
        ax.set_ylabel(f"Amount ({currency_code})")
        ax.set_title(f"Loan Amortization Schedule in {currency_code}")
        ax.legend()
        st.pyplot(fig)

# Step 2: Enter conversion currency code and convert results
conversion_currency_code = st.text_input(f"Enter Conversion Currency Code (e.g., USD, GBP, INR):", value="USD")

if conversion_currency_code:
    # Get exchange rate for conversion currency
    exchange_rate_conversion = get_exchange_rate(conversion_currency_code)
    if exchange_rate_conversion is None:
        st.error(f"Could not retrieve exchange rate for {conversion_currency_code}.")
    else:
        # Check if exchange rates are valid
        if st.session_state.exchange_rate_initial is None:
            st.error("Initial exchange rate not found. Please calculate the loan first.")
        else:
            # Convert loan amount and monthly payment to the target currency
            loan_amount_in_converted_currency = st.session_state.loan_amount * (exchange_rate_conversion / st.session_state.exchange_rate_initial) if exchange_rate_conversion and st.session_state.exchange_rate_initial else None
            monthly_payment_in_converted_currency = st.session_state.monthly_payment * (exchange_rate_conversion / st.session_state.exchange_rate_initial) if exchange_rate_conversion and st.session_state.exchange_rate_initial else None

            # Handle case if conversion failed
            if loan_amount_in_converted_currency is None or monthly_payment_in_converted_currency is None:
                st.error("Error: Conversion calculation failed. Please try again.")
            else:
                # Convert amortization schedule values to the target currency
                schedule_converted = st.session_state.schedule.copy()
                schedule_converted["Principal Payment"] = schedule_converted["Principal Payment"] * (exchange_rate_conversion / st.session_state.exchange_rate_initial)
                schedule_converted["Interest Payment"] = schedule_converted["Interest Payment"] * (exchange_rate_conversion / st.session_state.exchange_rate_initial)
                schedule_converted["Remaining Balance"] = schedule_converted["Remaining Balance"] * (exchange_rate_conversion / st.session_state.exchange_rate_initial)

                # Display converted amortization schedule
                st.subheader(f"Amortization Schedule Converted to {conversion_currency_code}")
                st.dataframe(schedule_converted)

                # Display monthly payment in converted currency
                st.write(f"Monthly Payment in {conversion_currency_code}: {monthly_payment_in_converted_currency:,.2f}")

                # Plot converted amortization schedule
                st.subheader(f"Amortization Chart Converted to {conversion_currency_code}")
                fig, ax = plt.subplots()
                ax.plot(schedule_converted["Payment Number"], schedule_converted["Remaining Balance"],
                        label=f"Remaining Balance in {conversion_currency_code}")
                ax.set_xlabel("Payment Number")
                ax.set_ylabel(f"Amount ({conversion_currency_code})")
                ax.set_title(f"Loan Amortization Schedule in {conversion_currency_code}")
                ax.legend()
                st.pyplot(fig)
